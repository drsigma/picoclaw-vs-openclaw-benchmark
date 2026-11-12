#!/usr/bin/env node
/**
 * OpenClaw TypeScript/Node.js Orchestrator Benchmark Worker
 * Evaluates V8 dynamic module loading, JSON schema validation, object allocation,
 * generational GC pressure, and tool dispatch under equalized neural workloads.
 */
import fs from "node:fs";
import path from "node:path";
import { performance } from "node:perf_hooks";
import { fileURLToPath } from "node:url";
import v8 from "node:v8";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_DIR = path.resolve(__dirname, "..");
const API_URL = process.env.LLAMA_API_URL || "http://127.0.0.1:8080/v1/chat/completions";
const BASE_DIR = process.env.WORKLOAD_DATA_DIR || path.join(REPO_DIR, "data", "workload_data");

function getRSSMB() {
  return process.memoryUsage().rss / (1024.0 * 1024.0);
}

// Build OpenClaw's tool schema catalog & prompt context builder
// Supports ablation modes: "full" (54 tools stock enterprise) vs "minimal" (15 tools equalized)
function buildOpenClawToolCatalog() {
  const mode = process.env.OPENCLAW_MODE || "minimal";
  const toolCount = mode === "full" ? 54 : 15;
  const catalog = [];
  for (let i = 0; i < toolCount; i++) {
    catalog.push({
      type: "function",
      function: {
        name: `system_tool_${i}`,
        description: `OpenClaw dynamic tool descriptor #${i} with TypeBox runtime validation schema and session routing metadata.`,
        parameters: {
          type: "object",
          properties: {
            action: { type: "string", description: "Action to execute" },
            target: { type: "string", description: "Target parameter or file path" }
          },
          required: ["action", "target"]
        }
      }
    });
  }
  // V8 object allocation and schema serialization pass
  const serialized = JSON.stringify(catalog);
  return JSON.parse(serialized);
}

function executeToolListDir(mockDir) {
  const entries = fs.readdirSync(mockDir);
  const files = entries.map((name) => {
    try {
      const st = fs.statSync(path.join(mockDir, name));
      return `${name}:${st.size}`;
    } catch {
      return `${name}:0`;
    }
  });
  return JSON.stringify({ count: files.length, files: files.slice(0, 10) });
}

function executeToolGrepLogs(logFile) {
  const raw = fs.readFileSync(logFile, "utf-8");
  const lines = raw.split("\n");
  const re = /"subsystem":\s*"UMA_BUS_CONTROLLER"/;
  const vals = [];
  for (const line of lines) {
    if (re.test(line)) {
      try {
        const obj = JSON.parse(line);
        if (typeof obj.latency_ms === "number") {
          vals.push(obj.latency_ms);
        }
      } catch {}
    }
  }
  return {
    vals,
    summary: JSON.stringify({ matched_records: vals.length, sample: vals.slice(0, 5) })
  };
}

function executeToolCalcStats(vals) {
  const n = vals.length;
  if (n === 0) return "{}";
  const mean = vals.reduce((a, b) => a + b, 0) / n;
  let variance = 0.0;
  if (n > 1) {
    variance = vals.reduce((a, v) => a + (v - mean) ** 2, 0) / (n - 1);
  }
  return JSON.stringify({ n, mean, variance, stddev: Math.sqrt(variance) });
}

function executeVectorRAG(baseDir) {
  const inDim = 256;
  const outDim = 384;
  const nDocs = 10000;

  const wFile = path.join(baseDir, "w_proj.bin");
  const bFile = path.join(baseDir, "b_proj.bin");
  const docsBinFile = path.join(baseDir, "doc_embeddings.bin");

  const wBuf = fs.readFileSync(wFile);
  const bBuf = fs.readFileSync(bFile);
  const docBuf = fs.readFileSync(docsBinFile);

  if (wBuf.length !== inDim * outDim * 4 || bBuf.length !== outDim * 4 || docBuf.length !== nDocs * outDim * 4) {
    throw new Error(`FATAL: Required RAG binary datasets corrupted or incomplete in ${baseDir}`);
  }

  const wProj = new Float32Array(wBuf.buffer, wBuf.byteOffset, inDim * outDim);
  const bProj = new Float32Array(bBuf.buffer, bBuf.byteOffset, outDim);
  const docMatrix = new Float32Array(docBuf.buffer, docBuf.byteOffset, nDocs * outDim);

  // 1. Query vector initialization and linear projection (256 -> 384)
  const qRaw = new Float32Array(inDim);
  for (let d = 0; d < inDim; d++) {
    qRaw[d] = Math.sin(d * 0.17) * 0.05;
  }

  const qProj = new Float32Array(outDim);
  for (let j = 0; j < outDim; j++) {
    let sum = bProj[j];
    for (let i = 0; i < inDim; i++) {
      sum += qRaw[i] * wProj[i * outDim + j];
    }
    qProj[j] = sum;
  }

  // 2. L2 Normalization of projected query vector
  let normSq = 0.0;
  for (let j = 0; j < outDim; j++) {
    normSq += qProj[j] * qProj[j];
  }
  const norm = Math.sqrt(normSq) + 1e-8;
  for (let j = 0; j < outDim; j++) {
    qProj[j] /= norm;
  }

  // 3. Cosine similarity against all 10,000 document vectors
  const scores = new Array(nDocs);
  for (let i = 0; i < nDocs; i++) {
    let dot = 0.0;
    const rowOffset = i * outDim;
    for (let j = 0; j < outDim; j++) {
      dot += qProj[j] * docMatrix[rowOffset + j];
    }
    scores[i] = { idx: i, score: dot };
  }

  // 4. Descending sort to select Top-5 chunks
  scores.sort((a, b) => b.score - a.score);

  const chunksRaw = fs.readFileSync(path.join(baseDir, "rag_chunks_10k.json"), "utf-8");
  const chunks = JSON.parse(chunksRaw);

  let out = "";
  for (let k = 0; k < 5; k++) {
    const topIdx = scores[k].idx;
    out += (chunks[String(topIdx)] || `[Chunk #${topIdx}] Context reference document.`) + "\n";
  }
  return out;
}

async function callLlamaStream(messages, tools, maxTokens) {
  const payload = JSON.stringify({
    model: "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
    messages,
    tools,
    max_tokens: maxTokens,
    temperature: 0.0,
    seed: 42,
    stream: true,
    cache_prompt: process.env.BENCH_CACHE_PROMPT === "true"
  });
  const t0 = performance.now();
  const resp = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload
  });

  if (resp.status !== 200) {
    const errText = await resp.text();
    throw new Error(`FATAL: llama-server returned HTTP ${resp.status}: ${errText}`);
  }

  let ttftMs = 0.0;
  let promptMs = 0.0;
  let predictedMs = 0.0;
  let hasServerTimings = false;
  let firstChunk = true;
  let tokenCount = 0;
  let promptTokens = 0;
  let completionTokens = 0;
  let finishReason = "";
  let outText = "";
  const decoder = new TextDecoder();
  let buf = "";

  let isDone = false;
  for await (const chunk of resp.body) {
    if (isDone) break;
    buf += decoder.decode(chunk, { stream: true });
    const lines = buf.split("\n");
    buf = lines.pop() || "";
    for (let line of lines) {
      line = line.trim();
      if (line.startsWith("data: ")) {
        const dataStr = line.slice(6);
        if (dataStr === "[DONE]") {
          isDone = true;
          break;
        }
        try {
          const parsed = JSON.parse(dataStr);
          if (parsed.timings) {
            if (typeof parsed.timings.prompt_ms === "number") {
              promptMs = parsed.timings.prompt_ms;
              hasServerTimings = true;
            }
            if (typeof parsed.timings.predicted_ms === "number") {
              predictedMs = parsed.timings.predicted_ms;
              hasServerTimings = true;
            }
            if (typeof parsed.timings.prompt_n === "number" && parsed.timings.prompt_n > 0) {
              promptTokens = parsed.timings.prompt_n;
            }
            if (typeof parsed.timings.predicted_n === "number" && parsed.timings.predicted_n > 0) {
              completionTokens = parsed.timings.predicted_n;
            }
          }
          if (parsed.usage) {
            if (typeof parsed.usage.prompt_tokens === "number" && parsed.usage.prompt_tokens > 0) {
              promptTokens = parsed.usage.prompt_tokens;
            }
            if (typeof parsed.usage.completion_tokens === "number" && parsed.usage.completion_tokens > 0) {
              completionTokens = parsed.usage.completion_tokens;
            }
          }
          const c0 = parsed.choices?.[0];
          if (c0) {
            if (c0.finish_reason && typeof c0.finish_reason === "string") {
              finishReason = c0.finish_reason;
            }
            const delta = c0.delta;
            if (delta) {
              let hasData = false;
              if (delta.content && delta.content.length > 0) {
                hasData = true;
                tokenCount++;
                outText += delta.content;
              }
              if (delta.tool_calls && delta.tool_calls.length > 0) {
                hasData = true;
                tokenCount += delta.tool_calls.length;
              }
              if (hasData && firstChunk) {
                ttftMs = performance.now() - t0;
                firstChunk = false;
              }
            }
          }
        } catch {}
      }
    }
  }

  const totalNeuralMs = hasServerTimings ? (promptMs + predictedMs) : (performance.now() - t0);
  if (completionTokens === 0) completionTokens = tokenCount;
  if (!finishReason) finishReason = "stop";
  const itlMs = completionTokens > 1 ? (totalNeuralMs - ttftMs) / (completionTokens - 1) : 0.0;
  return {
    totalNeuralMs,
    ttftMs,
    itlMs,
    promptTokens,
    completionTokens,
    finishReason,
    httpStatus: resp.status,
    outText
  };
}

async function runWorkload(tier, warmth, rssIdle) {
  const tStart = performance.now();
  let tNeuralTotal = 0.0;
  let ttftFirst = 0.0;
  let itlAvg = 0.0;
  let tDispatchTotal = 0.0;
  let totalPromptTokens = 0;
  let totalCompletionTokens = 0;
  let toolCalls = 0;
  let lastFinishReason = "";
  let lastHttpStatus = 200;

  const tCatalog0 = performance.now();
  const toolCatalog = buildOpenClawToolCatalog();
  const tCatalogMs = performance.now() - tCatalog0;

  const mockDir = path.join(BASE_DIR, "mock_files");
  const logFile = path.join(BASE_DIR, "system_logs.jsonl");

  if (tier === "W1") {
    tDispatchTotal = tCatalogMs;
    const prompt =
      "Analyze Apple Silicon M4 Unified Memory Architecture cache coherence and LPDDR5X bandwidth allocation. ".repeat(8) +
      "Summarize the primary latency determinant in two concise sentences.";
    const msgs = [
      { role: "system", content: "You are a concise technical systems assistant." },
      { role: "user", content: prompt }
    ];
    const r = await callLlamaStream(msgs, toolCatalog, 64);
    tNeuralTotal = r.totalNeuralMs;
    ttftFirst = r.ttftMs;
    itlAvg = r.itlMs;
    totalPromptTokens = r.promptTokens;
    totalCompletionTokens = r.completionTokens;
    lastFinishReason = r.finishReason;
    lastHttpStatus = r.httpStatus;
    toolCalls = 0;
  } else if (tier === "W2") {
    const tTool0 = performance.now();
    const res1 = executeToolListDir(mockDir);
    const { vals, summary: res2 } = executeToolGrepLogs(logFile);
    const res3 = executeToolCalcStats(vals);
    tDispatchTotal = tCatalogMs + (performance.now() - tTool0);
    toolCalls = 3;

    const prompt = `System Tool Chain Results:\n1. list_dir: ${res1}\n2. grep_logs: ${res2}\n3. calc_stats: ${res3}\nProvide a concise technical diagnostic summary of the bus latency metrics.`;
    const msgs = [
      { role: "system", content: "You are a concise technical systems assistant." },
      { role: "user", content: prompt }
    ];
    const r = await callLlamaStream(msgs, toolCatalog, 128);
    tNeuralTotal = r.totalNeuralMs;
    ttftFirst = r.ttftMs;
    itlAvg = r.itlMs;
    totalPromptTokens = r.promptTokens;
    totalCompletionTokens = r.completionTokens;
    lastFinishReason = r.finishReason;
    lastHttpStatus = r.httpStatus;
  } else if (tier === "W3") {
    const tTool0 = performance.now();
    const ragContext = executeVectorRAG(BASE_DIR);
    tDispatchTotal = tCatalogMs + (performance.now() - tTool0);
    toolCalls = 1;

    const msgs = [
      { role: "system", content: "You are a concise technical systems assistant." },
      { role: "user", content: "Retrieved Context:\n" + ragContext + "\nQuestion: How do UMA bandwidth and runtime GC interact during local agent execution?" }
    ];
    const r = await callLlamaStream(msgs, toolCatalog, 256);
    tNeuralTotal = r.totalNeuralMs;
    ttftFirst = r.ttftMs;
    itlAvg = r.itlMs;
    totalPromptTokens = r.promptTokens;
    totalCompletionTokens = r.completionTokens;
    lastFinishReason = r.finishReason;
    lastHttpStatus = r.httpStatus;
  } else if (tier === "W4") {
    toolCalls = 10;
    let itlSum = 0.0;
    const history = [
      { role: "system", content: "You are a concise technical systems assistant." }
    ];
    tDispatchTotal = tCatalogMs;
    for (let step = 1; step <= 10; step++) {
      const tTool0 = performance.now();
      executeToolListDir(mockDir);
      const { vals } = executeToolGrepLogs(logFile);
      const statStr = executeToolCalcStats(vals);
      tDispatchTotal += (performance.now() - tTool0);

      history.push({
        role: "user",
        content: `Turn ${step} Observation: ${statStr}. State next brief diagnostic action.`
      });
      const r = await callLlamaStream(history, toolCatalog, 64);
      tNeuralTotal += r.totalNeuralMs;
      if (step === 1) ttftFirst = r.ttftMs;
      itlSum += r.itlMs;
      totalPromptTokens += r.promptTokens;
      totalCompletionTokens += r.completionTokens;
      lastFinishReason = r.finishReason;
      lastHttpStatus = r.httpStatus;
      history.push({ role: "assistant", content: r.outText });
    }
    itlAvg = itlSum / 10.0;
  }

  const tTaskMs = performance.now() - tStart;
  const tHttpMs = Math.max(0.0, tTaskMs - tNeuralTotal - tDispatchTotal);
  const tOrchMs = Math.max(0.0, tTaskMs - tNeuralTotal);
  const phiOrch = tTaskMs > 0 ? (tOrchMs / tTaskMs) * 100.0 : 0.0;
  const rTool = toolCalls > 0 && tDispatchTotal > 0 ? toolCalls / (tDispatchTotal / 1000.0) : 0.0;
  const rssPeak = Math.max(rssIdle, getRSSMB());
  const alphaMem = rssPeak / Math.max(1.0, rssIdle);
  const v8UsedHeapMb = v8.getHeapStatistics().used_heap_size / (1024.0 * 1024.0);
  const mode = process.env.OPENCLAW_MODE || "minimal";

  return {
    architecture: `OpenClaw [${mode}] (Node.js v26.12)`,
    workload: tier,
    warmth: warmth,
    t_task_ms: tTaskMs,
    t_neural_ms: tNeuralTotal,
    t_orch_ms: tOrchMs,
    phi_orch_pct: phiOrch,
    ttft_ms: ttftFirst,
    itl_ms: itlAvg,
    t_dispatch_ms: tDispatchTotal,
    t_http_ms: tHttpMs,
    r_tool_ops_sec: rTool,
    rss_idle_mb: rssIdle,
    rss_peak_mb: rssPeak,
    v8_used_heap_mb: v8UsedHeapMb,
    alpha_mem: alphaMem,
    prompt_tokens: totalPromptTokens,
    completion_tokens: totalCompletionTokens,
    output_tokens: totalCompletionTokens,
    tool_calls: toolCalls,
    http_status: lastHttpStatus,
    finish_reason: lastFinishReason
  };
}

async function main() {
  const args = process.argv.slice(2);
  const tier = args[0] || "W1";
  const warmth = args[1] || "Cold";
  const reps = parseInt(args[2] || "1", 10);
  const rssIdle = getRSSMB();
  const results = [];
  for (let i = 0; i < reps; i++) {
    const res = await runWorkload(tier, warmth, rssIdle);
    results.push(res);
  }
  console.log(JSON.stringify(results));
}

main().catch((err) => {
  console.error("OpenClaw Worker Error:", err);
  process.exit(1);
});
