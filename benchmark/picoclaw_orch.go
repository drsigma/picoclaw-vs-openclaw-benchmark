package main

import (
	"bufio"
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"sort"
	"strings"
	"syscall"
	"time"
)

type FunctionParameterProp struct {
	Type        string `json:"type"`
	Description string `json:"description,omitempty"`
}

type FunctionParameters struct {
	Type       string                           `json:"type"`
	Properties map[string]FunctionParameterProp `json:"properties"`
	Required   []string                         `json:"required"`
}

type ToolFunction struct {
	Name        string             `json:"name"`
	Description string             `json:"description"`
	Parameters  FunctionParameters `json:"parameters"`
}

type ToolDefinition struct {
	Type     string       `json:"type"`
	Function ToolFunction `json:"function"`
}

type ChatMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type ChatRequest struct {
	Model       string           `json:"model"`
	Messages    []ChatMessage    `json:"messages"`
	Tools       []ToolDefinition `json:"tools,omitempty"`
	MaxTokens   int              `json:"max_tokens"`
	Temperature float64          `json:"temperature"`
	Seed        int              `json:"seed"`
	Stream      bool             `json:"stream"`
	CachePrompt bool             `json:"cache_prompt"`
}

type TrialResult struct {
	Architecture     string  `json:"architecture"`
	Workload         string  `json:"workload"`
	Warmth           string  `json:"warmth"`
	TTaskMs          float64 `json:"t_task_ms"`
	TNeuralMs        float64 `json:"t_neural_ms"`
	PromptMs         float64 `json:"prompt_ms"`
	PredictedMs      float64 `json:"predicted_ms"`
	TOrchMs          float64 `json:"t_orch_ms"`
	PhiOrchPct       float64 `json:"phi_orch_pct"`
	TTFTMs           float64 `json:"ttft_ms"`
	ITLMs            float64 `json:"itl_ms"`
	TDispatchMs      float64 `json:"t_dispatch_ms"`
	TPruneMs         float64 `json:"t_prune_ms"`
	THttpMs          float64 `json:"t_http_ms"`
	RToolOpsSec      float64 `json:"r_tool_ops_sec"`
	RSSIdleMB        float64 `json:"rss_idle_mb"`
	RSSPeakMB        float64 `json:"rss_peak_mb"`
	AlphaMem         float64 `json:"alpha_mem"`
	PromptTokens     int     `json:"prompt_tokens"`
	CompletionTokens int     `json:"completion_tokens"`
	OutputTokens     int     `json:"output_tokens"`
	CachedTokens     int     `json:"cached_tokens"`
	UncachedPromptTokens int `json:"uncached_prompt_tokens"`
	CacheHitPct      float64 `json:"cache_hit_pct"`
	ToolCalls        int     `json:"tool_calls"`
	HttpStatus       int     `json:"http_status"`
	FinishReason     string  `json:"finish_reason"`
}

func minInt(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func getRSSMB() float64 {
	var rusage syscall.Rusage
	if err := syscall.Getrusage(syscall.RUSAGE_SELF, &rusage); err == nil {
		if runtime.GOOS == "darwin" {
			return float64(rusage.Maxrss) / (1024.0 * 1024.0)
		}
		return float64(rusage.Maxrss) / 1024.0
	}
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	return float64(m.Sys) / (1024.0 * 1024.0)
}

func buildStandardToolCatalog(count int) []ToolDefinition {
	tools := make([]ToolDefinition, count)
	for i := 0; i < count; i++ {
		tools[i] = ToolDefinition{
			Type: "function",
			Function: ToolFunction{
				Name:        fmt.Sprintf("system_tool_%d", i),
				Description: fmt.Sprintf("Standard system tool descriptor #%d for agent runtime evaluation.", i),
				Parameters: FunctionParameters{
					Type: "object",
					Properties: map[string]FunctionParameterProp{
						"action": {Type: "string", Description: "Action to execute"},
						"target": {Type: "string", Description: "Target parameter or file path"},
					},
					Required: []string{"action", "target"},
				},
			},
		}
	}
	return tools
}

func buildToolEmbeddings(nTools int) []float32 {
	const dim = 384
	mat := make([]float32, nTools*dim)
	for i := 0; i < nTools; i++ {
		var tNormSq float64
		rowOffset := i * dim
		for d := 0; d < dim; d++ {
			v := math.Sin(float64(i+1)*0.31 + float64(d)*0.13)
			mat[rowOffset+d] = float32(v)
			tNormSq += v * v
		}
		tNorm := float32(math.Sqrt(tNormSq) + 1e-8)
		for d := 0; d < dim; d++ {
			mat[rowOffset+d] /= tNorm
		}
	}
	return mat
}

func pruneToolsVectorRAG(catalog []ToolDefinition, toolEmb []float32, tier string, topK int) ([]ToolDefinition, float64) {
	t0 := time.Now()
	const dim = 384
	nTools := len(catalog)
	if nTools <= topK {
		return catalog, 0.0
	}
	tierSeed := 1.0
	switch tier {
	case "W2":
		tierSeed = 2.0
	case "W3":
		tierSeed = 3.0
	case "W4":
		tierSeed = 4.0
	}

	qVec := make([]float32, dim)
	var qNormSq float64
	for d := 0; d < dim; d++ {
		val := math.Cos(tierSeed*0.37 + float64(d)*0.19)
		qVec[d] = float32(val)
		qNormSq += val * val
	}
	qNorm := float32(math.Sqrt(qNormSq) + 1e-8)
	for d := 0; d < dim; d++ {
		qVec[d] /= qNorm
	}

	scores := make([]docScore, nTools)
	for i := 0; i < nTools; i++ {
		rowOffset := i * dim
		var dot float32
		for d := 0; d < dim; d++ {
			dot += toolEmb[rowOffset+d] * qVec[d]
		}
		scores[i] = docScore{idx: i, score: dot}
	}

	sort.Slice(scores, func(a, b int) bool {
		if scores[a].score == scores[b].score {
			return scores[a].idx < scores[b].idx
		}
		return scores[a].score > scores[b].score
	})

	topIndices := make([]int, topK)
	for k := 0; k < topK; k++ {
		topIndices[k] = scores[k].idx
	}
	sort.Ints(topIndices)

	pruned := make([]ToolDefinition, topK)
	for k, idx := range topIndices {
		pruned[k] = catalog[idx]
	}
	elapsedMs := float64(time.Since(t0).Nanoseconds()) / 1e6
	return pruned, elapsedMs
}

func executeToolListDir(mockDir string) (string, error) {
	entries, err := os.ReadDir(mockDir)
	if err != nil {
		return "", err
	}
	var names []string
	for _, e := range entries {
		info, _ := e.Info()
		sz := int64(0)
		if info != nil {
			sz = info.Size()
		}
		names = append(names, fmt.Sprintf("%s:%d", e.Name(), sz))
	}
	k := minInt(10, len(names))
	out, _ := json.Marshal(map[string]interface{}{
		"count": len(names),
		"files": names[:k],
	})
	return string(out), nil
}

func executeToolGrepLogs(logFile string) ([]float64, string, error) {
	f, err := os.Open(logFile)
	if err != nil {
		return nil, "", err
	}
	defer f.Close()
	re := regexp.MustCompile(`"subsystem":\s*"UMA_BUS_CONTROLLER"`)
	var vals []float64
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Text()
		if re.MatchString(line) {
			var obj map[string]interface{}
			if err := json.Unmarshal([]byte(line), &obj); err == nil {
				if v, ok := obj["latency_ms"].(float64); ok {
					vals = append(vals, v)
				}
			}
		}
	}
	k := minInt(5, len(vals))
	sample := []float64{}
	if k > 0 {
		sample = vals[:k]
	}
	out, _ := json.Marshal(map[string]interface{}{
		"matched_records": len(vals),
		"sample":          sample,
	})
	return vals, string(out), nil
}

func executeToolCalcStats(vals []float64) string {
	n := len(vals)
	if n == 0 {
		return "{}"
	}
	sum := 0.0
	for _, v := range vals {
		sum += v
	}
	mean := sum / float64(n)
	varSq := 0.0
	for _, v := range vals {
		d := v - mean
		varSq += d * d
	}
	variance := 0.0
	if n > 1 {
		variance = varSq / float64(n-1)
	}
	out, _ := json.Marshal(map[string]interface{}{
		"n":        n,
		"mean":     mean,
		"variance": variance,
		"stddev":   math.Sqrt(variance),
	})
	return string(out)
}

type docScore struct {
	idx   int
	score float32
}

type StreamResult struct {
	TotalNeuralMs        float64
	PromptMs             float64
	PredictedMs          float64
	TTFTMs               float64
	ITLMs                float64
	PromptTokens         int
	CompletionTokens     int
	CachedTokens         int
	UncachedPromptTokens int
	FinishReason         string
	HttpStatus           int
	OutputText           string
}

func executeVectorRAG(baseDir string) string {
	const inDim = 256
	const outDim = 384
	const nDocs = 10000

	wProj := make([]float32, inDim*outDim)
	bProj := make([]float32, outDim)
	docMatrix := make([]float32, nDocs*outDim)

	wFile := filepath.Join(baseDir, "w_proj.bin")
	bFile := filepath.Join(baseDir, "b_proj.bin")
	docsBinFile := filepath.Join(baseDir, "doc_embeddings.bin")

	wBytes, errW := os.ReadFile(wFile)
	bBytes, errB := os.ReadFile(bFile)
	docBytes, errDoc := os.ReadFile(docsBinFile)
	if errW != nil || errB != nil || errDoc != nil ||
		len(wBytes) != inDim*outDim*4 || len(bBytes) != outDim*4 || len(docBytes) != nDocs*outDim*4 {
		panic(fmt.Sprintf("FATAL: Required RAG binary datasets missing or corrupted in %s (w_proj.bin, b_proj.bin, doc_embeddings.bin)", baseDir))
	}

	for i := 0; i < inDim*outDim; i++ {
		wProj[i] = math.Float32frombits(binary.LittleEndian.Uint32(wBytes[i*4 : (i+1)*4]))
	}
	for i := 0; i < outDim; i++ {
		bProj[i] = math.Float32frombits(binary.LittleEndian.Uint32(bBytes[i*4 : (i+1)*4]))
	}
	for i := 0; i < nDocs*outDim; i++ {
		docMatrix[i] = math.Float32frombits(binary.LittleEndian.Uint32(docBytes[i*4 : (i+1)*4]))
	}

	// 1. Query vector initialization and linear projection (256 -> 384)
	qRaw := make([]float32, inDim)
	for d := 0; d < inDim; d++ {
		qRaw[d] = float32(math.Sin(float64(d)*0.17)) * 0.05
	}

	qProj := make([]float32, outDim)
	for j := 0; j < outDim; j++ {
		sum := bProj[j]
		for i := 0; i < inDim; i++ {
			sum += qRaw[i] * wProj[i*outDim+j]
		}
		qProj[j] = sum
	}

	// 2. L2 Normalization of projected query vector
	var normSq float32
	for j := 0; j < outDim; j++ {
		normSq += qProj[j] * qProj[j]
	}
	norm := float32(math.Sqrt(float64(normSq))) + 1e-8
	for j := 0; j < outDim; j++ {
		qProj[j] /= norm
	}

	// 3. Cosine similarity against all 10,000 document vectors
	scores := make([]docScore, nDocs)
	for i := 0; i < nDocs; i++ {
		var dot float32
		rowOffset := i * outDim
		for j := 0; j < outDim; j++ {
			dot += qProj[j] * docMatrix[rowOffset+j]
		}
		scores[i] = docScore{idx: i, score: dot}
	}

	// 4. Descending sort to select Top-5 chunks
	sort.Slice(scores, func(a, b int) bool {
		return scores[a].score > scores[b].score
	})

	docsFile := filepath.Join(baseDir, "rag_chunks_10k.json")
	raw, errChunks := os.ReadFile(docsFile)
	if errChunks != nil {
		panic(fmt.Sprintf("FATAL: rag_chunks_10k.json missing in %s: %v", baseDir, errChunks))
	}
	var chunks map[string]string
	_ = json.Unmarshal(raw, &chunks)

	var sb strings.Builder
	for k := 0; k < 5; k++ {
		topIdx := scores[k].idx
		if text, ok := chunks[fmt.Sprintf("%d", topIdx)]; ok {
			sb.WriteString(text)
		} else {
			sb.WriteString(fmt.Sprintf("[Chunk #%04d] Context reference document.", topIdx))
		}
		sb.WriteString("\n")
	}
	return sb.String()
}

func callLlamaStream(client *http.Client, apiURL string, messages []ChatMessage, tools []ToolDefinition, maxTokens int) StreamResult {
	reqBody := ChatRequest{
		Model:       "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
		Messages:    messages,
		Tools:       tools,
		MaxTokens:   maxTokens,
		Temperature: 0.0,
		Seed:        42,
		Stream:      true,
		CachePrompt: os.Getenv("BENCH_CACHE_PROMPT") == "true",
	}
	payload, _ := json.Marshal(reqBody)
	t0 := time.Now()
	req, _ := http.NewRequest("POST", apiURL, bytes.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")
	resp, err := client.Do(req)
	if err != nil {
		panic(fmt.Sprintf("FATAL: HTTP request to llama-server failed: %v", err))
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		panic(fmt.Sprintf("FATAL: llama-server returned HTTP %d: %s", resp.StatusCode, string(bodyBytes)))
	}

	var ttftMs float64
	var promptMs, predictedMs float64
	hasServerTimings := false
	firstChunk := true
	tokenCount := 0
	var cachedTokens, uncachedPromptTokens, usagePromptTokens, completionTokens int
	var finishReason string
	var outText strings.Builder
	reader := bufio.NewReader(resp.Body)

	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			break
		}
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "data: ") {
			dataStr := strings.TrimPrefix(line, "data: ")
			if dataStr == "[DONE]" {
				break
			}
			var chunk map[string]interface{}
			if err := json.Unmarshal([]byte(dataStr), &chunk); err == nil {
				if timings, ok := chunk["timings"].(map[string]interface{}); ok {
					if pMs, ok := timings["prompt_ms"].(float64); ok {
						promptMs = pMs
						hasServerTimings = true
					}
					if predMs, ok := timings["predicted_ms"].(float64); ok {
						predictedMs = predMs
						hasServerTimings = true
					}
					if cn, ok := timings["cache_n"].(float64); ok && cn >= 0 {
						cachedTokens = int(cn)
					}
					if pn, ok := timings["prompt_n"].(float64); ok && pn >= 0 {
						uncachedPromptTokens = int(pn)
					}
					if predN, ok := timings["predicted_n"].(float64); ok && predN > 0 {
						completionTokens = int(predN)
					}
				}
				if usage, ok := chunk["usage"].(map[string]interface{}); ok {
					if pt, ok := usage["prompt_tokens"].(float64); ok && pt > 0 {
						usagePromptTokens = int(pt)
					}
					if ct, ok := usage["completion_tokens"].(float64); ok && ct > 0 {
						completionTokens = int(ct)
					}
				}
				if choices, ok := chunk["choices"].([]interface{}); ok && len(choices) > 0 {
					if c0, ok := choices[0].(map[string]interface{}); ok {
						if fr, ok := c0["finish_reason"].(string); ok && fr != "" {
							finishReason = fr
						}
						if delta, ok := c0["delta"].(map[string]interface{}); ok {
							hasData := false
							if content, ok := delta["content"].(string); ok && len(content) > 0 {
								hasData = true
								tokenCount++
								outText.WriteString(content)
							}
							if toolCalls, ok := delta["tool_calls"].([]interface{}); ok && len(toolCalls) > 0 {
								hasData = true
								tokenCount += len(toolCalls)
							}
							if hasData && firstChunk {
								ttftMs = float64(time.Since(t0).Nanoseconds()) / 1e6
								firstChunk = false
							}
						}
					}
				}
			}
		}
	}

	var totalNeuralMs float64
	if hasServerTimings {
		totalNeuralMs = promptMs + predictedMs
	} else {
		totalNeuralMs = float64(time.Since(t0).Nanoseconds()) / 1e6
	}

	promptTokens := 0
	if usagePromptTokens > 0 {
		promptTokens = usagePromptTokens
	} else {
		promptTokens = cachedTokens + uncachedPromptTokens
	}

	if completionTokens == 0 {
		completionTokens = tokenCount
	}
	if finishReason == "" {
		finishReason = "stop"
	}

	itlMs := 0.0
	if completionTokens > 1 {
		itlMs = (totalNeuralMs - ttftMs) / float64(completionTokens-1)
	}

	if !hasServerTimings {
		promptMs = ttftMs
		predictedMs = math.Max(0.0, totalNeuralMs-ttftMs)
	}

	return StreamResult{
		TotalNeuralMs:        totalNeuralMs,
		PromptMs:             promptMs,
		PredictedMs:          predictedMs,
		TTFTMs:               ttftMs,
		ITLMs:                itlMs,
		PromptTokens:         promptTokens,
		CompletionTokens:     completionTokens,
		CachedTokens:         cachedTokens,
		UncachedPromptTokens: uncachedPromptTokens,
		FinishReason:         finishReason,
		HttpStatus:           resp.StatusCode,
		OutputText:           outText.String(),
	}
}

func runWorkload(client *http.Client, apiURL, baseDir, tier, warmth string, rssIdle float64) TrialResult {
	tStart := time.Now()
	var tNeuralTotal, totalPromptMs, totalPredictedMs, ttftFirst, itlAvg, tDispatchTotal, tPruneTotal float64
	var totalPromptTokens, totalCompletionTokens, totalCachedTokens, totalUncachedPromptTokens, toolCalls int
	var lastFinishReason string
	lastHttpStatus := 200

	isToolRag := os.Getenv("OPENCLAW_MODE") == "tool_rag" || os.Getenv("PICOCLAW_MODE") == "tool_rag" || os.Getenv("TOOL_RAG_MODE") == "true"

	// Equalized tool definitions sent in request (15 tools for minimal/picoclaw parity, or 54 -> Top-5 in tool_rag mode)
	tToolCatalog0 := time.Now()
	var fullCatalog []ToolDefinition
	var toolEmb []float32
	var toolCatalog []ToolDefinition
	if isToolRag {
		fullCatalog = buildStandardToolCatalog(54)
		toolEmb = buildToolEmbeddings(54)
		pruned, tpMs := pruneToolsVectorRAG(fullCatalog, toolEmb, tier, 5)
		toolCatalog = pruned
		tPruneTotal += tpMs
	} else {
		toolCatalog = buildStandardToolCatalog(15)
	}
	tCatalogMs := float64(time.Since(tToolCatalog0).Nanoseconds()) / 1e6

	mockDir := filepath.Join(baseDir, "mock_files")
	logFile := filepath.Join(baseDir, "system_logs.jsonl")

	switch tier {
	case "W1":
		tDispatchTotal = tCatalogMs
		prompt := strings.Repeat("Analyze Apple Silicon M4 Unified Memory Architecture cache coherence and LPDDR5X bandwidth allocation. ", 8) +
			"Summarize the primary latency determinant in two concise sentences."
		msgs := []ChatMessage{
			{Role: "system", Content: "You are a concise technical systems assistant."},
			{Role: "user", Content: prompt},
		}
		sr := callLlamaStream(client, apiURL, msgs, toolCatalog, 64)
		tNeuralTotal = sr.TotalNeuralMs
		totalPromptMs = sr.PromptMs
		totalPredictedMs = sr.PredictedMs
		ttftFirst = sr.TTFTMs
		itlAvg = sr.ITLMs
		totalPromptTokens = sr.PromptTokens
		totalCompletionTokens = sr.CompletionTokens
		totalCachedTokens = sr.CachedTokens
		totalUncachedPromptTokens = sr.UncachedPromptTokens
		lastFinishReason = sr.FinishReason
		lastHttpStatus = sr.HttpStatus
		toolCalls = 0

	case "W2":
		tTool0 := time.Now()
		res1, err1 := executeToolListDir(mockDir)
		if err1 != nil {
			panic(fmt.Sprintf("W2 executeToolListDir failed: %v", err1))
		}
		vals, res2, err2 := executeToolGrepLogs(logFile)
		if err2 != nil {
			panic(fmt.Sprintf("W2 executeToolGrepLogs failed: %v", err2))
		}
		res3 := executeToolCalcStats(vals)
		tDispatchTotal = tCatalogMs + float64(time.Since(tTool0).Nanoseconds())/1e6
		toolCalls = 3

		prompt := fmt.Sprintf("System Tool Chain Results:\n1. list_dir: %s\n2. grep_logs: %s\n3. calc_stats: %s\nEvaluate the bus latency metrics and execute the next diagnostic step.", res1, res2, res3)
		msgs := []ChatMessage{
			{Role: "system", Content: "You are a concise technical systems assistant."},
			{Role: "user", Content: prompt},
		}
		sr := callLlamaStream(client, apiURL, msgs, toolCatalog, 128)
		tNeuralTotal = sr.TotalNeuralMs
		totalPromptMs = sr.PromptMs
		totalPredictedMs = sr.PredictedMs
		ttftFirst = sr.TTFTMs
		itlAvg = sr.ITLMs
		totalPromptTokens = sr.PromptTokens
		totalCompletionTokens = sr.CompletionTokens
		totalCachedTokens = sr.CachedTokens
		totalUncachedPromptTokens = sr.UncachedPromptTokens
		lastFinishReason = sr.FinishReason
		lastHttpStatus = sr.HttpStatus

	case "W3":
		tTool0 := time.Now()
		ragContext := executeVectorRAG(baseDir)
		tDispatchTotal = tCatalogMs + float64(time.Since(tTool0).Nanoseconds())/1e6
		toolCalls = 1

		msgs := []ChatMessage{
			{Role: "system", Content: "You are a concise technical systems assistant."},
			{Role: "user", Content: "Retrieved Context:\n" + ragContext + "\nQuestion: How do UMA bandwidth and runtime GC interact during local agent execution?"},
		}
		sr := callLlamaStream(client, apiURL, msgs, toolCatalog, 256)
		tNeuralTotal = sr.TotalNeuralMs
		totalPromptMs = sr.PromptMs
		totalPredictedMs = sr.PredictedMs
		ttftFirst = sr.TTFTMs
		itlAvg = sr.ITLMs
		totalPromptTokens = sr.PromptTokens
		totalCompletionTokens = sr.CompletionTokens
		totalCachedTokens = sr.CachedTokens
		totalUncachedPromptTokens = sr.UncachedPromptTokens
		lastFinishReason = sr.FinishReason
		lastHttpStatus = sr.HttpStatus

	case "W4":
		toolCalls = 10
		var itlSum float64
		history := []ChatMessage{
			{Role: "system", Content: "You are a concise technical systems assistant."},
		}
		tDispatchTotal = tCatalogMs
		for step := 1; step <= 10; step++ {
			tTool0 := time.Now()
			if isToolRag && step > 1 {
				pruned, tpMs := pruneToolsVectorRAG(fullCatalog, toolEmb, tier, 5)
				toolCatalog = pruned
				tPruneTotal += tpMs
			}
			_, _ = executeToolListDir(mockDir)
			vals, _, _ := executeToolGrepLogs(logFile)
			statStr := executeToolCalcStats(vals)
			tDispatchTotal += float64(time.Since(tTool0).Nanoseconds()) / 1e6

			history = append(history, ChatMessage{
				Role:    "user",
				Content: fmt.Sprintf("Turn %d Observation: %s. State next brief diagnostic action.", step, statStr),
			})
			sr := callLlamaStream(client, apiURL, history, toolCatalog, 64)
			tNeuralTotal += sr.TotalNeuralMs
			totalPromptMs += sr.PromptMs
			totalPredictedMs += sr.PredictedMs
			if step == 1 {
				ttftFirst = sr.TTFTMs
			}
			itlSum += sr.ITLMs
			totalPromptTokens += sr.PromptTokens
			totalCompletionTokens += sr.CompletionTokens
			totalCachedTokens += sr.CachedTokens
			totalUncachedPromptTokens += sr.UncachedPromptTokens
			lastFinishReason = sr.FinishReason
			lastHttpStatus = sr.HttpStatus
			history = append(history, ChatMessage{Role: "assistant", Content: sr.OutputText})
		}
		itlAvg = itlSum / 10.0
	}

	if totalPromptTokens <= 0 || totalCompletionTokens <= 0 {
		panic(fmt.Sprintf("FATAL: Validation failed - prompt_tokens (%d) <= 0 or completion_tokens (%d) <= 0", totalPromptTokens, totalCompletionTokens))
	}

	tTaskMs := float64(time.Since(tStart).Nanoseconds()) / 1e6
	tHttpMs := math.Max(0.0, tTaskMs-tNeuralTotal-tDispatchTotal)
	tOrchMs := math.Max(0.0, tTaskMs-tNeuralTotal)
	phiOrch := 0.0
	if tTaskMs > 0 {
		phiOrch = (tOrchMs / tTaskMs) * 100.0
	}
	rTool := 0.0
	if toolCalls > 0 && tDispatchTotal > 0 {
		rTool = float64(toolCalls) / (tDispatchTotal / 1000.0)
	}
	rssPeak := getRSSMB()
	if rssPeak < rssIdle {
		rssPeak = rssIdle
	}

	cacheHitPct := 0.0
	if totalPromptTokens > 0 {
		cacheHitPct = (float64(totalCachedTokens) / float64(totalPromptTokens)) * 100.0
	}

	archName := "PicoClaw (Go 1.23)"
	if isToolRag {
		archName = "PicoClaw [tool_rag] (Go 1.23)"
	}

	return TrialResult{
		Architecture:         archName,
		Workload:             tier,
		Warmth:               warmth,
		TTaskMs:              tTaskMs,
		TNeuralMs:            tNeuralTotal,
		PromptMs:             totalPromptMs,
		PredictedMs:          totalPredictedMs,
		TOrchMs:              tOrchMs,
		PhiOrchPct:           phiOrch,
		TTFTMs:               ttftFirst,
		ITLMs:                itlAvg,
		TDispatchMs:          tDispatchTotal,
		TPruneMs:             tPruneTotal,
		THttpMs:              tHttpMs,
		RToolOpsSec:          rTool,
		RSSIdleMB:            rssIdle,
		RSSPeakMB:            rssPeak,
		AlphaMem:             rssPeak / math.Max(1.0, rssIdle),
		PromptTokens:         totalPromptTokens,
		CompletionTokens:     totalCompletionTokens,
		OutputTokens:         totalCompletionTokens,
		CachedTokens:         totalCachedTokens,
		UncachedPromptTokens: totalUncachedPromptTokens,
		CacheHitPct:          cacheHitPct,
		ToolCalls:            toolCalls,
		HttpStatus:           lastHttpStatus,
		FinishReason:         lastFinishReason,
	}
}

type LocalToolResult struct {
	Workload   string  `json:"workload"`
	Iterations int     `json:"iterations"`
	TotalOps   int     `json:"total_ops"`
	TExecMs    float64 `json:"t_exec_ms"`
}

func runLocalToolsBenchmark(baseDir, tier string, iterations int) LocalToolResult {
	mockDir := filepath.Join(baseDir, "mock_files")
	logFile := filepath.Join(baseDir, "system_logs.jsonl")
	t0 := time.Now()
	totalOps := 0
	if tier == "W2" {
		for i := 0; i < iterations; i++ {
			buildStandardToolCatalog(15)
			executeToolListDir(mockDir)
			vals, _, _ := executeToolGrepLogs(logFile)
			executeToolCalcStats(vals)
			totalOps += 3
		}
	} else if tier == "W3" {
		for i := 0; i < iterations; i++ {
			buildStandardToolCatalog(15)
			executeVectorRAG(baseDir)
			totalOps += 1
		}
	} else {
		panic(fmt.Sprintf("Unsupported tier for local tools: %s", tier))
	}
	elapsedMs := float64(time.Since(t0).Microseconds()) / 1000.0
	return LocalToolResult{
		Workload:   tier,
		Iterations: iterations,
		TotalOps:   totalOps,
		TExecMs:    elapsedMs,
	}
}

func main() {
	if len(os.Args) > 1 && (os.Args[1] == "--version" || os.Args[1] == "version" || os.Args[1] == "--help") {
		fmt.Println("picoclaw_orch v1.0.0")
		os.Exit(0)
	}
	tier := "W1"
	warmth := "Cold"
	reps := 1
	apiURL := "http://127.0.0.1:8080/v1/chat/completions"
	if envURL := os.Getenv("LLAMA_API_URL"); envURL != "" {
		apiURL = envURL
	}
	baseDir := os.Getenv("WORKLOAD_DATA_DIR")
	if baseDir == "" {
		candidates := []string{
			"./data/workload_data",
			"../data/workload_data",
		}
		for _, c := range candidates {
			if _, err := os.Stat(c); err == nil {
				baseDir = c
				break
			}
		}
	}
	if baseDir == "" {
		baseDir = "./data/workload_data"
	}
	if len(os.Args) > 1 && os.Args[1] == "--local-tools" {
		localTier := "W2"
		localIter := 200
		if len(os.Args) > 2 {
			localTier = os.Args[2]
		}
		if len(os.Args) > 3 {
			fmt.Sscanf(os.Args[3], "%d", &localIter)
		}
		res := runLocalToolsBenchmark(baseDir, localTier, localIter)
		out, _ := json.Marshal([]LocalToolResult{res})
		fmt.Println(string(out))
		return
	}
	if len(os.Args) > 1 {
		tier = os.Args[1]
	}
	if len(os.Args) > 2 {
		warmth = os.Args[2]
	}
	if len(os.Args) > 3 {
		fmt.Sscanf(os.Args[3], "%d", &reps)
	}
	rssIdle := getRSSMB()
	client := &http.Client{Timeout: 120 * time.Second}
	var results []TrialResult
	for i := 0; i < reps; i++ {
		res := runWorkload(client, apiURL, baseDir, tier, warmth, rssIdle)
		results = append(results, res)
	}
	out, _ := json.Marshal(results)
	fmt.Println(string(out))
}
