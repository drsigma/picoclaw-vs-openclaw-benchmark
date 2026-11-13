#!/usr/bin/env python3
"""
benchmark/mcp_server.py - Live Model Context Protocol (MCP) Server
Elsevier SoftwareX: picoclaw-vs-openclaw-benchmark (Gate R10 - MCP Live Transport Ablation)

Implements a real JSON-RPC 2.0 Model Context Protocol (MCP) server supporting:
  1. Stdio transport (stdin -> stdout)
  2. Local HTTP loopback transport (POST /mcp)

Exposes the standardized benchmark tool suite:
  - list_dir: lists directory mock files
  - grep_logs: regex search across mock system logs
  - calc_stats: numerical statistics aggregation

Author: Rafael Paniccia Cassetta (UFABC)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.join(REPO_DIR, "data", "workload_data")


def handle_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """Dispatches tool execution against benchmark mock datasets."""
    if tool_name == "list_dir":
        path = arguments.get("dir_path") or os.path.join(BASE_DIR, "mock_files")
        if not os.path.exists(path):
            return []
        return sorted(os.listdir(path))

    elif tool_name == "grep_logs":
        pattern = arguments.get("pattern", "WARN|ERROR")
        path = arguments.get("file_path") or os.path.join(BASE_DIR, "system_logs.jsonl")
        if not os.path.exists(path):
            return {"count": 0, "values": []}
        matched = []
        reg = re.compile(pattern)
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    if reg.search(rec.get("message", "")):
                        if "duration_ms" in rec:
                            matched.append(float(rec["duration_ms"]))
                except Exception:
                    continue
        return {"count": len(matched), "values": matched[:20]}

    elif tool_name == "calc_stats":
        values = arguments.get("values", [])
        if not values:
            return {"mean": 0.0, "std": 0.0, "count": 0}
        n = len(values)
        m = sum(values) / n
        var = sum((x - m) ** 2 for x in values) / n if n > 1 else 0.0
        return {"mean": round(m, 3), "std": round(math.sqrt(var), 3), "count": n}

    else:
        raise ValueError(f"Unknown MCP tool: {tool_name}")


def process_jsonrpc_request(req_str: str) -> Dict[str, Any]:
    """Processes a JSON-RPC 2.0 MCP request and returns the response dictionary."""
    try:
        req = json.loads(req_str)
    except Exception as e:
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"Parse error: {e}"}}

    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {"name": "list_dir", "description": "Lists directory files"},
                    {"name": "grep_logs", "description": "Greps patterns in system logs"},
                    {"name": "calc_stats", "description": "Calculates statistical aggregation"},
                ]
            },
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        try:
            res = handle_tool_call(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(res)}]},
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(e)},
            }

    elif method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "picoclaw-benchmark-mcp", "version": "1.0.0"},
            },
        }

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }


def run_stdio_server():
    """Runs standard input/output MCP JSON-RPC server loop."""
    for line in sys.stdin:
        if not line.strip():
            continue
        resp = process_jsonrpc_request(line)
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


class MCPHTTPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path in ("/mcp", "/"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            resp = process_jsonrpc_request(body)
            resp_bytes = json.dumps(resp).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence default stderr logging for benchmarking
        pass


def run_http_server(host: str = "127.0.0.1", port: int = 8090):
    """Runs local loopback HTTP MCP server."""
    server = HTTPServer((host, port), MCPHTTPHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PicoClaw/OpenClaw Benchmark Live MCP Server")
    parser.add_argument("--stdio", action="store_true", help="Run via stdin/stdout transport")
    parser.add_argument("--http", action="store_true", help="Run via local HTTP transport")
    parser.add_argument("--port", type=int, default=8090, help="Port for HTTP server (default 8090)")
    args = parser.parse_args()

    if args.stdio:
        run_stdio_server()
    elif args.http:
        run_http_server(port=args.port)
    else:
        # Default to stdio
        run_stdio_server()
