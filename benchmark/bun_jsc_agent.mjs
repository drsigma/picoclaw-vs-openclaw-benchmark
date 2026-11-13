#!/usr/bin/env bun
/**
 * benchmark/bun_jsc_agent.mjs - Independent Bun / JavaScriptCore Orchestrator Worker
 * Evaluates Apple WebKit JavaScriptCore (JSC) JIT compilation, Zig-backed I/O (Bun.file),
 * nanosecond monotonic timing (Bun.nanoseconds), and native fetch streaming across W1-W4.
 *
 * Author: Rafael Paniccia Cassetta (UFABC)
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rawArgs = typeof Bun !== "undefined" ? Bun.argv.slice(2) : process.argv.slice(2);
if (rawArgs.length > 0 && (rawArgs[0] === "--version" || rawArgs[0] === "version" || rawArgs[0] === "--help")) {
  console.log("bun_jsc_agent v1.0.0");
  process.exit(0);
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_DIR = path.resolve(__dirname, "..");
const ENV = typeof Bun !== "undefined" ? Bun.env : process.env;
const API_URL = ENV.LLAMA_API_URL || "http://127.0.0.1:8080/v1/chat/completions";
const BASE_DIR = ENV.WORKLOAD_DATA_DIR || path.join(REPO_DIR, "data", "workload_data");

function nowMs() {
  if (typeof Bun !== "undefined" && typeof Bun.nanoseconds === "function") {
    return Bun.nanoseconds() / 1e6;
  }
  return performance.now();
}

function readResidentMemoryMB() {
  return process.memoryUsage().rss / (1024.0 * 1024.0);
}

function synthesizeToolDescriptors(count = 15) {
  const descriptors = new Array(count);
  for (let idx = 0; idx < count; idx++) {
    descriptors[idx] = {
      type: "function",
      function: {
        name: `system_tool_${idx}`,
        description: `Standard system tool descriptor #${idx} for agent runtime evaluation.`,
        parameters: {
          type: "object",
          properties: {
            action: { type: "string", description: "Action to execute" },
            target: { type: "string", description: "Target parameter or file path" }
          },
          required: ["action", "target"]
        }
      }
    };
  }
  return JSON.parse(JSON.stringify(descriptors));
}

async function readBinaryFloat32(filePath, expectedFloatCount) {
  let buf;
  if (typeof Bun !== "undefined" && typeof Bun.file === "function") {
    const ab = await Bun.file(filePath).arrayBuffer();
    buf = new Float32Array(ab);
  } else {
    const raw = fs.readFileSync(filePath);
    buf = new Float32Array(raw.buffer, raw.byteOffset, raw.byteLength / 4);
  }
  if (buf.length !== expectedFloatCount) {
    throw new Error(`FATAL: Binary tensor ${filePath} has ${buf.length} floats, expected ${expectedFloatCount}`);
  }
  return buf;
}

async function readTextFast(filePath) {
  if (typeof Bun !== "undefined" && typeof Bun.file === "function") {
    return await Bun.file(filePath).text();
  }
  return fs.readFileSync(filePath, "utf-8");
}

function inspectDirectory(mockDir) {
  const names = fs.readdirSync(mockDir);
  const formatted = names.map((entry) => {
    const stat = fs.statSync(path.join(mockDir, entry));
    return `${entry}:${stat.size}`;
  });
  return JSON.stringify({ count: formatted.length, files: formatted.slice(0, 10) });
}

async function filterSystemLogs(logFile) {
  const text = await readTextFast(logFile);
  const lines = text.split("\n");
  const pattern = /"subsystem":\s*"UMA_BUS_CONTROLLER"/;
  const latencies = [];
  for (let i = 0; i < lines.length; i++) {
    const row = lines[i];
    if (pattern.test(row)) {
      const parsed = JSON.parse(row);
      if (typeof parsed.latency_ms === "number") {
        latencies.push(parsed.latency_ms);
      }
    }
  }
  return {
    latencies,
    summaryJson: JSON.stringify({ matched_records: latencies.length, sample: latencies.slice(0, 5) })
  };
}

function computeSummaryStats(values) {
  const n = values.length;
  if (n === 0) {
    throw new Error("FATAL: Empty latency array in computeSummaryStats");
  }
  let sum = 0.0;
  for (let i = 0; i < n; i++) sum += values[i];
  const mean = sum / n;
  let sqDiff = 0.0;
  for (let i = 0; i < n; i++) {
    const d = values[i] - mean;
    sqDiff += d * d;
  }
  const variance = n > 1 ? sqDiff / (n - 1) : 0.0;
  return JSON.stringify({ n, mean, variance, stddev: Math.sqrt(variance) });
}

async function runJscVectorRetrieval(baseDir) {
  const inDim = 256;
  const outDim = 384;
  const nDocs = 10000;

  const wProj = await readBinaryFloat32(path.join(baseDir, "w_proj.bin"), inDim * outDim);
  const bProj = await readBinaryFloat32(path.join(baseDir, "b_proj.bin"), outDim);
  const docMatrix = await readBinaryFloat32(path.join(baseDir, "doc_embeddings.bin"), nDocs * outDim);

  const qRaw = new Float32Array(inDim);
  for (let d = 0; d < inDim; d++) {
    qRaw[d] = Math.sin(d * 0.17) * 0.05;
  }

  const qProj = new Float32Array(outDim);
  let normSq = 0.0;
  for (let j = 0; j < outDim; j++) {
    let acc = bProj[j];
    for (let i = 0; i < inDim; i++) {
      acc += qRaw[i] * wProj[i * outDim + j];
    }
    qProj[j] = acc;
    normSq += acc * acc;
  }

  const invNorm = 1.0 / (Math.sqrt(normSq) + 1e-8);
  for (let j = 0; j < outDim; j++) {
    qProj[j] *= invNorm;
  }

  const ranked = new Array(nDocs);
  for (let docIdx = 0; docIdx < nDocs; docIdx++) {
    const offset = docIdx * outDim;
    let dot = 0.0;
    for (let j = 0; j < outDim; j++) {
      dot += qProj[j] * docMatrix[offset + j];
    }
    ranked[docIdx] = { idx: docIdx, score: dot };
  }

  ranked.sort((a, b) => b.score - a.score);

  const chunksText = await readTextFast(path.join(baseDir, "rag_chunks_10k.json"));
  const chunksMap = JSON.parse(chunksText);

  let contextBlock = "";
  for (let k = 0; k < 5; k++) {
    const docId = String(ranked[k].idx);
    contextBlock += (chunksMap[docId] || `[Chunk #${docId}] Context reference document.`) + "\n";
  }
  return contextBlock;
}

async function streamCompletionJSC(messages, tools, maxTokens) {
  const bodyStr = JSON.stringify({
    model: "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
    messages,
    tools,
    max_tokens: maxTokens,
    temperature: 0.0,
    seed: 42,
    stream: true,
    cache_prompt: ENV.BENCH_CACHE_PROMPT === "true"
  });

  const tReq0 = nowMs();
  const response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: bodyStr
  });

  if (response.status !== 200) {
    const errBody = await response.text();
    throw new Error(`FATAL: llama-server HTTP ${response.status}: ${errBody}`);
  }

  let ttftMs = 0.0;
  let promptMs = 0.0;
  let predictedMs = 0.0;
  let hasTimings = false;
  let awaitingFirstToken = true;
  let deltaCount = 0;
  let cachedTokens = 0;
  let uncachedTokens = 0;
  let usagePromptTokens = 0;
  let completionTokens = 0;
  let finishReason = "";
  let assistantText = "";

  const decoder = new TextDecoder();
  let streamBuf = "";
  let done = false;

  for await (const chunk of response.body) {
    if (done) break;
    streamBuf += decoder.decode(chunk, { stream: true });
    const lines = streamBuf.split("\n");
    streamBuf = lines.pop() || "";
    for (let rawLine of lines) {
      const line = rawLine.trim();
      if (!line.startsWith("data: ")) continue;
      const payload = line.slice(6);
      if (payload === "[DONE]") {
        done = true;
        break;
      }
      const frame = JSON.parse(payload);
      if (frame.timings) {
        if (typeof frame.timings.prompt_ms === "number") {
          promptMs = frame.timings.prompt_ms;
          hasTimings = true;
        }
        if (typeof frame.timings.predicted_ms === "number") {
          predictedMs = frame.timings.predicted_ms;
          hasTimings = true;
        }
        if (typeof frame.timings.cache_n === "number" && frame.timings.cache_n >= 0) {
          cachedTokens = frame.timings.cache_n;
        }
        if (typeof frame.timings.prompt_n === "number" && frame.timings.prompt_n >= 0) {
          uncachedTokens = frame.timings.prompt_n;
        }
        if (typeof frame.timings.predicted_n === "number" && frame.timings.predicted_n > 0) {
          completionTokens = frame.timings.predicted_n;
        }
      }
      if (frame.usage) {
        if (typeof frame.usage.prompt_tokens === "number" && frame.usage.prompt_tokens > 0) {
          usagePromptTokens = frame.usage.prompt_tokens;
        }
        if (typeof frame.usage.completion_tokens === "number" && frame.usage.completion_tokens > 0) {
          completionTokens = frame.usage.completion_tokens;
        }
      }
      const choice = frame.choices?.[0];
      if (choice) {
        if (typeof choice.finish_reason === "string" && choice.finish_reason.length > 0) {
          finishReason = choice.finish_reason;
        }
        const delta = choice.delta;
        if (delta) {
          let emitted = false;
          if (delta.content && delta.content.length > 0) {
            emitted = true;
            deltaCount++;
            assistantText += delta.content;
          }
          if (delta.tool_calls && delta.tool_calls.length > 0) {
            emitted = true;
            deltaCount += delta.tool_calls.length;
          }
          if (emitted && awaitingFirstToken) {
            ttftMs = nowMs() - tReq0;
            awaitingFirstToken = false;
          }
        }
      }
    }
  }

  const promptTokens = usagePromptTokens > 0 ? usagePromptTokens : (cachedTokens + uncachedTokens);
  const neuralMs = hasTimings ? (promptMs + predictedMs) : (nowMs() - tReq0);
  const finalPromptMs = hasTimings ? promptMs : ttftMs;
  const finalPredictedMs = hasTimings ? predictedMs : Math.max(0.0, neuralMs - ttftMs);
  if (completionTokens === 0) completionTokens = deltaCount;
  if (!finishReason) finishReason = "stop";
  const itlMs = completionTokens > 1 ? Math.max(0.0, (neuralMs - ttftMs) / (completionTokens - 1)) : 0.0;

  return {
    neuralMs,
    promptMs: finalPromptMs,
    predictedMs: finalPredictedMs,
    ttftMs,
    itlMs,
    promptTokens,
    completionTokens,
    cachedTokens,
    uncachedTokens,
    finishReason,
    httpStatus: response.status,
    assistantText
  };
}

async function executeWorkloadTier(tier, warmth, rssIdle) {
  const tStart = nowMs();
  const tCat0 = nowMs();
  const toolCatalog = synthesizeToolDescriptors(15);
  const tCatMs = nowMs() - tCat0;

  const mockDir = path.join(BASE_DIR, "mock_files");
  const logFile = path.join(BASE_DIR, "system_logs.jsonl");

  let tNeuralTotal = 0.0;
  let totalPromptMs = 0.0;
  let totalPredictedMs = 0.0;
  let ttftFirst = 0.0;
  let itlAvg = 0.0;
  let tDispatchTotal = tCatMs;
  let totalPromptTokens = 0;
  let totalCompletionTokens = 0;
  let totalCachedTokens = 0;
  let totalUncachedTokens = 0;
  let toolCalls = 0;
  let finishReason = "";
  let httpStatus = 200;

  if (tier === "W1") {
    const prompt =
      "Analyze Apple Silicon M4 Unified Memory Architecture cache coherence and LPDDR5X bandwidth allocation. ".repeat(8) +
      "Summarize the primary latency determinant in two concise sentences.";
    const messages = [
      { role: "system", content: "You are a concise technical systems assistant." },
      { role: "user", content: prompt }
    ];
    const r = await streamCompletionJSC(messages, toolCatalog, 64);
    tNeuralTotal = r.neuralMs;
    totalPromptMs = r.promptMs;
    totalPredictedMs = r.predictedMs;
    ttftFirst = r.ttftMs;
    itlAvg = r.itlMs;
    totalPromptTokens = r.promptTokens;
    totalCompletionTokens = r.completionTokens;
    totalCachedTokens = r.cachedTokens;
    totalUncachedTokens = r.uncachedTokens;
    finishReason = r.finishReason;
    httpStatus = r.httpStatus;
  } else if (tier === "W2") {
    const tTool0 = nowMs();
    const dirSummary = inspectDirectory(mockDir);
    const { latencies, summaryJson } = await filterSystemLogs(logFile);
    const statsJson = computeSummaryStats(latencies);
    tDispatchTotal += nowMs() - tTool0;
    toolCalls = 3;

    const prompt = `System Tool Chain Results:\n1. list_dir: ${dirSummary}\n2. grep_logs: ${summaryJson}\n3. calc_stats: ${statsJson}\nEvaluate the bus latency metrics and execute the next diagnostic step.`;
    const messages = [
      { role: "system", content: "You are a concise technical systems assistant." },
      { role: "user", content: prompt }
    ];
    const r = await streamCompletionJSC(messages, toolCatalog, 128);
    tNeuralTotal = r.neuralMs;
    totalPromptMs = r.promptMs;
    totalPredictedMs = r.predictedMs;
    ttftFirst = r.ttftMs;
    itlAvg = r.itlMs;
    totalPromptTokens = r.promptTokens;
    totalCompletionTokens = r.completionTokens;
    totalCachedTokens = r.cachedTokens;
    totalUncachedTokens = r.uncachedTokens;
    finishReason = r.finishReason;
    httpStatus = r.httpStatus;
  } else if (tier === "W3") {
    const tTool0 = nowMs();
    const ragContext = await runJscVectorRetrieval(BASE_DIR);
    tDispatchTotal += nowMs() - tTool0;
    toolCalls = 1;

    const messages = [
      { role: "system", content: "You are a concise technical systems assistant." },
      { role: "user", content: "Retrieved Context:\n" + ragContext + "\nQuestion: How do UMA bandwidth and runtime GC interact during local agent execution?" }
    ];
    const r = await streamCompletionJSC(messages, toolCatalog, 256);
    tNeuralTotal = r.neuralMs;
    totalPromptMs = r.promptMs;
    totalPredictedMs = r.predictedMs;
    ttftFirst = r.ttftMs;
    itlAvg = r.itlMs;
    totalPromptTokens = r.promptTokens;
    totalCompletionTokens = r.completionTokens;
    totalCachedTokens = r.cachedTokens;
    totalUncachedTokens = r.uncachedTokens;
    finishReason = r.finishReason;
    httpStatus = r.httpStatus;
  } else if (tier === "W4") {
    toolCalls = 10;
    let itlSum = 0.0;
    const history = [{ role: "system", content: "You are a concise technical systems assistant." }];
    for (let step = 1; step <= 10; step++) {
      const tTool0 = nowMs();
      inspectDirectory(mockDir);
      const { latencies } = await filterSystemLogs(logFile);
      const statsJson = computeSummaryStats(latencies);
      tDispatchTotal += nowMs() - tTool0;

      history.push({
        role: "user",
        content: `Turn ${step} Observation: ${statsJson}. State next brief diagnostic action.`
      });
      const r = await streamCompletionJSC(history, toolCatalog, 64);
      tNeuralTotal += r.neuralMs;
      totalPromptMs += r.promptMs;
      totalPredictedMs += r.predictedMs;
      if (step === 1) ttftFirst = r.ttftMs;
      itlSum += r.itlMs;
      totalPromptTokens += r.promptTokens;
      totalCompletionTokens += r.completionTokens;
      totalCachedTokens += r.cachedTokens;
      totalUncachedTokens += r.uncachedTokens;
      finishReason = r.finishReason;
      httpStatus = r.httpStatus;
      history.push({ role: "assistant", content: r.assistantText });
    }
    itlAvg = itlSum / 10.0;
  } else {
    throw new Error(`FATAL: Unsupported workload tier: ${tier}`);
  }

  if (totalPromptTokens <= 0 || totalCompletionTokens <= 0) {
    throw new Error(`FATAL: Invalid token counts in BunJSC worker (prompt=${totalPromptTokens}, completion=${totalCompletionTokens})`);
  }

  const tTaskMs = nowMs() - tStart;
  const tOrchMs = Math.max(0.0, tTaskMs - tNeuralTotal);
  const tHttpMs = Math.max(0.0, tOrchMs - tDispatchTotal);
  const phiOrch = tTaskMs > 0 ? (tOrchMs / tTaskMs) * 100.0 : 0.0;
  const rTool = toolCalls > 0 && tDispatchTotal > 0 ? toolCalls / (tDispatchTotal / 1000.0) : 0.0;
  const rssPeak = Math.max(rssIdle, readResidentMemoryMB());
  const cacheHitPct = totalPromptTokens > 0 ? (totalCachedTokens / totalPromptTokens) * 100.0 : 0.0;
  const bunVer = typeof Bun !== "undefined" ? Bun.version : "node-compat";

  return {
    architecture: `Bun JSC Orchestrator (Bun v${bunVer} / JavaScriptCore)`,
    workload: tier,
    warmth,
    t_task_ms: tTaskMs,
    t_neural_ms: tNeuralTotal,
    prompt_ms: totalPromptMs,
    predicted_ms: totalPredictedMs,
    t_orch_ms: tOrchMs,
    phi_orch_pct: phiOrch,
    ttft_ms: ttftFirst,
    itl_ms: itlAvg,
    t_dispatch_ms: tDispatchTotal,
    t_prune_ms: 0.0,
    t_http_ms: tHttpMs,
    r_tool_ops_sec: rTool,
    rss_idle_mb: rssIdle,
    rss_peak_mb: rssPeak,
    alpha_mem: rssPeak / Math.max(1.0, rssIdle),
    prompt_tokens: totalPromptTokens,
    completion_tokens: totalCompletionTokens,
    output_tokens: totalCompletionTokens,
    cached_tokens: totalCachedTokens,
    uncached_prompt_tokens: totalUncachedTokens,
    cache_hit_pct: cacheHitPct,
    tool_calls: toolCalls,
    http_status: httpStatus,
    finish_reason: finishReason
  };
}

async function main() {
  const tier = rawArgs[0] || "W1";
  const warmth = rawArgs[1] || "Cold";
  const reps = parseInt(rawArgs[2] || "1", 10);
  const rssIdle = readResidentMemoryMB();
  const out = [];
  for (let i = 0; i < reps; i++) {
    out.push(await executeWorkloadTier(tier, warmth, rssIdle));
  }
  console.log(JSON.stringify(out));
}

main().catch((err) => {
  console.error("Bun JSC Orchestrator Fatal Error:", err);
  process.exit(1);
});
