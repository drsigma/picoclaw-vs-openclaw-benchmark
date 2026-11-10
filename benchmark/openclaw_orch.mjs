#!/usr/bin/env node
/**
 * OpenClaw TypeScript/Node.js Orchestrator Benchmark Worker
 * Evaluates V8 dynamic module loading, JSON schema validation, object allocation,
 * generational GC pressure, and tool dispatch under equalized neural workloads.
 */
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { performance } from "node:perf_hooks";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_DIR = path.resolve(__dirname, "..");
const API_URL = process.env.LLAMA_API_URL || "http://127.0.0.1:8080/v1/chat/completions";
const BASE_DIR = process.env.WORKLOAD_DATA_DIR || path.join(REPO_DIR, "data", "workload_data");

function getRSSMB() {
  return process.memoryUsage().rss / (1024.0 * 1024.0);
}

// Simulate OpenClaw's 54-tool TypeBox/JSON-Schema catalog & prompt context builder overhead
function buildOpenClawToolCatalog() {
  const catalog = [];
  for (let i = 0; i < 54; i++) {
    catalog.push({
      id: `openclaw_tool_${i}`,
      name: `tool_${i}`,
      description: `OpenClaw dynamic plugin tool descriptor #${i} with TypeBox runtime validation schema and session routing metadata.`,
      parameters: {
        type: "object",
        properties: {
          action: { type: "string", enum: ["run", "inspect", "query", "patch"] },
          target: { type: "string", description: "Target path or identifier" },
          options: {
            type: "object",
            properties: {
              timeoutMs: { type: "number", default: 10000 },
              recursive: { type: "boolean", default: false },
              headers: { type: "object", additionalProperties: { type: "string" } }
            }
          }
        },
        required: ["action", "target"]
      }
    });
  }
  // OpenClaw validates and serializes the catalog on turn preparation
  const serialized = JSON.stringify(catalog);
  const parsed = JSON.parse(serialized);
  return parsed.length;
}

function executeToolListDir(mockDir) {
  const entries = fs.readdirSync(mockDir);
  const files = entries.map((name) => {
    const st = fs.statSync(path.join(mockDir, name));
    return `${name}:${st.size}`;
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
      const obj = JSON.parse(line);
      if (typeof obj.latency_ms === "number") {
        vals.push(obj.latency_ms);
      }
    }
  }
  return {
    vals,
    summary: JSON.stringify({ matched_records: vals.length, sample: vals.slice(0, 5) })
  };
}

function executeToolCalcStats(vals) {
  const n = vals.length;
  const mean = vals.reduce((a, b) => a + b, 0) / n;
  const variance = vals.reduce((a, v) => a + (v - mean) ** 2, 0) / (n - 1);
  return JSON.stringify({ n, mean, variance, stddev: Math.sqrt(variance) });
}

function executeVectorRAG(baseDir) {
  const nDocs = 10000;
  const dim = 384;
  // V8 dynamic array/object allocation during embedding projection and 10k cosine similarity search
  const qVec = new Array(dim);
  for (let d = 0; d < dim; d++) {
    qVec[d] = Math.sin(d * 0.17) * 0.05;
  }
  const scores = new Array(nDocs);
  for (let i = 0; i < nDocs; i++) {
    let dot = 0.0;
    const docVec = new Array(dim);
    for (let d = 0; d < dim; d++) {
      docVec[d] = ((i * 31 + d * 17) % 100) * 0.01;
      dot += qVec[d] * docVec[d];
    }
    scores[i] = { idx: i, score: dot };
  }
  scores.sort((a, b) => b.score - a.score);
  const chunks = JSON.parse(fs.readFileSync(path.join(baseDir, "rag_chunks_10k.json"), "utf-8"));
  let out = "";
  for (let k = 0; k < 5; k++) {
    out += chunks[String(k)] + "\n";
  }
  return out;
}

async function callLlamaStream(messages, maxTokens) {
  const payload = JSON.stringify({
    model: "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
    messages,
    max_tokens: maxTokens,
    temperature: 0.0,
    seed: 42,
    stream: true
  });
  const t0 = performance.now();
  const resp = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload
  });
  let ttftMs = 0.0;
  let firstChunk = true;
  let tokenCount = 0;
  let outText = "";
  const decoder = new TextDecoder();
  let buf = "";
  for await (const chunk of resp.body) {
    buf += decoder.decode(chunk, { stream: true });
    const lines = buf.split("\n");
    buf = lines.pop() || "";
    for (let line of lines) {
      line = line.trim();
      if (line.startsWith("data: ")) {
        const dataStr = line.slice(6);
        if (dataStr === "[DONE]") break;
        try {
          const parsed = JSON.parse(dataStr);
          const content = parsed.choices?.[0]?.delta?.content;
          if (content && content.length > 0) {
            if (firstChunk) {
              ttftMs = performance.now() - t0;
              firstChunk = false;
            }
            tokenCount++;
            outText += content;
          }
        } catch {}
      }
    }
  }
  const totalNeuralMs = performance.now() - t0;
  const itlMs = tokenCount > 1 ? (totalNeuralMs - ttftMs) / (tokenCount - 1) : 0.0;
  return { totalNeuralMs, ttftMs, itlMs, tokenCount, outText };
}

async function runWorkload(tier, warmth, rssIdle) {
  const tStart = performance.now();
  let tNeuralTotal = 0.0;
  let ttftFirst = 0.0;
  let itlAvg = 0.0;
  let tDispatchTotal = 0.0;
  let totalTokens = 0;
  let toolCalls = 0;

  // OpenClaw session & 54-tool catalog validation pass
  buildOpenClawToolCatalog();

  const mockDir = path.join(BASE_DIR, "mock_files");
  const logFile = path.join(BASE_DIR, "system_logs.jsonl");

  if (tier === "W1") {
    const prompt =
      "Analyze Apple Silicon M4 Unified Memory Architecture cache coherence and LPDDR5X bandwidth allocation. ".repeat(8) +
      "Summarize the primary latency determinant in two concise sentences.";
    const msgs = [
      { role: "system", content: "You are PicoClaw, a concise technical systems assistant." },
      { role: "user", content: prompt }
    ];
    const r = await callLlamaStream(msgs, 64);
    tNeuralTotal = r.totalNeuralMs;
    ttftFirst = r.ttftMs;
    itlAvg = r.itlMs;
    totalTokens = r.tokenCount;
    toolCalls = 0;
  } else if (tier === "W2") {
    const tTool0 = performance.now();
    buildOpenClawToolCatalog();
    const res1 = executeToolListDir(mockDir);
    const { vals, summary: res2 } = executeToolGrepLogs(logFile);
    const res3 = executeToolCalcStats(vals);
    execFileSync("/bin/echo", ["tool_chain_sync"]);
    tDispatchTotal = performance.now() - tTool0;
    toolCalls = 3;

    const prompt = `System Tool Chain Results:\n1. list_dir: ${res1}\n2. grep_logs: ${res2}\n3. calc_stats: ${res3}\nProvide a concise technical diagnostic summary of the bus latency metrics.`;
    const msgs = [
      { role: "system", content: "You are PicoClaw executing a 3-step diagnostic tool chain." },
      { role: "user", content: prompt }
    ];
    const r = await callLlamaStream(msgs, 128);
    tNeuralTotal = r.totalNeuralMs;
    ttftFirst = r.ttftMs;
    itlAvg = r.itlMs;
    totalTokens = r.tokenCount;
  } else if (tier === "W3") {
    const tTool0 = performance.now();
    buildOpenClawToolCatalog();
    const ragContext = executeVectorRAG(BASE_DIR);
    tDispatchTotal = performance.now() - tTool0;
    toolCalls = 1;

    const msgs = [
      { role: "system", content: "You are PicoClaw RAG engine. Synthesize the retrieved vector memory chunks." },
      { role: "user", content: "Retrieved Context:\n" + ragContext + "\nQuestion: How do UMA bandwidth and runtime GC interact during local agent execution?" }
    ];
    const r = await callLlamaStream(msgs, 256);
    tNeuralTotal = r.totalNeuralMs;
    ttftFirst = r.ttftMs;
    itlAvg = r.itlMs;
    totalTokens = r.tokenCount;
  } else if (tier === "W4") {
    toolCalls = 10;
    let itlSum = 0.0;
    const history = [
      { role: "system", content: "You are PicoClaw operating in a 10-turn autonomous ReAct diagnostic loop." }
    ];
    for (let step = 1; step <= 10; step++) {
      const tTool0 = performance.now();
      buildOpenClawToolCatalog();
      executeToolListDir(mockDir);
      const { vals } = executeToolGrepLogs(logFile);
      const statStr = executeToolCalcStats(vals);
      tDispatchTotal += performance.now() - tTool0;

      history.push({
        role: "user",
        content: `Turn ${step} Observation: ${statStr}. State next brief diagnostic action.`
      });
      const r = await callLlamaStream(history, 64);
      tNeuralTotal += r.totalNeuralMs;
      if (step === 1) ttftFirst = r.ttftMs;
      itlSum += r.itlMs;
      totalTokens += r.tokenCount;
      history.push({ role: "assistant", content: r.outText });
    }
    itlAvg = itlSum / 10.0;
  }

  const tTaskMs = performance.now() - tStart;
  const tOrchMs = Math.max(0.1, tTaskMs - tNeuralTotal);
  const phiOrch = (tOrchMs / tTaskMs) * 100.0;
  const rTool = toolCalls > 0 && tDispatchTotal > 0 ? toolCalls / (tDispatchTotal / 1000.0) : 0.0;
  const rssPeak = Math.max(rssIdle, getRSSMB());

  return {
    architecture: "OpenClaw (Node.js/TS)",
    workload: tier,
    warmth,
    t_task_ms: tTaskMs,
    t_neural_ms: tNeuralTotal,
    t_orch_ms: tOrchMs,
    phi_orch_pct: phiOrch,
    ttft_ms: ttftFirst,
    itl_ms: itlAvg,
    t_dispatch_ms: tDispatchTotal,
    r_tool_ops_sec: rTool,
    rss_idle_mb: rssIdle,
    rss_peak_mb: rssPeak,
    alpha_mem: rssPeak / Math.max(1.0, rssIdle),
    output_tokens: totalTokens,
    tool_calls: toolCalls
  };
}

async function main() {
  const tier = process.argv[2] || "W1";
  const warmth = process.argv[3] || "Cold";
  const reps = parseInt(process.argv[4] || "1", 10);
  // Load OpenClaw core metadata in memory to match OpenClaw Gateway resident baseline
  const pkgCandidates = [
    path.join(REPO_DIR, "tools", "openclaw-package.json"),
    path.join(REPO_DIR, "tools", "openclaw-2026.10.7", "package.json")
  ];
  let openclawPkg = "";
  for (const p of pkgCandidates) {
    if (fs.existsSync(p)) {
      openclawPkg = fs.readFileSync(p, "utf-8");
      break;
    }
  }
  const rssIdle = getRSSMB() + (openclawPkg.length > 0 ? 0 : 0);
  const results = [];
  for (let i = 0; i < reps; i++) {
    results.push(await runWorkload(tier, warmth, rssIdle));
  }
  console.log(JSON.stringify(results));
}

main();
