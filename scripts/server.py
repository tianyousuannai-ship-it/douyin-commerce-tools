#!/usr/bin/env python3
"""选品分析后端 v3 - 静态文件 + 市场数据 + DeepSeek AI 代理"""
import json, os, sys, http.server, urllib.request, mimetypes
from pathlib import Path

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
ROOT_DIR = Path(__file__).resolve().parent.parent  # douyin-selector/

SYSTEM_PROMPT = """你是顶级抖音电商选品分析专家。
严格按以下 JSON 格式输出，不要 markdown 代码块：

{
  "scores": {
    "marketHeat": 0-100,
    "competition": 0-100,
    "profit": 0-100,
    "trend": 0-100,
    "contentFit": 0-100,
    "supplyChain": 0-100
  },
  "dimensionAnalysis": {
    "marketHeat": {"score": 0-100, "summary": "...", "factors": [...]},
    "competition": {"score": 0-100, "summary": "...", "entryBarrier": "...", "differentiation": "..."},
    "profit": {"score": 0-100, "summary": "...", "roiEstimate": "...", "breakEven": "..."},
    "trend": {"score": 0-100, "summary": "...", "direction": "上升/平稳/下降", "seasonality": "..."},
    "contentFit": {"score": 0-100, "summary": "...", "contentType": "...", "difficulty": "..."},
    "supplyChain": {"score": 0-100, "summary": "..."}
  },
  "overall": {
    "totalScore": 0-100,
    "verdict": "建议入手|谨慎评估|不太建议",
    "recommendedAction": "...",
    "riskLevel": "低/中/高"
  },
  "contentStrategy": ["策略1", "策略2", "策略3", "策略4", "策略5"],
  "risks": [{"risk": "...", "severity": "高/中/低", "mitigation": "..."}],
  "marketRefs": {"similarProducts": "...", "priceRange": "...", "targetGMV": "..."},
  "tags": ["标签1", "标签2"]
}"""

# ---------- MIME types ----------
MIME_MAP = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}


def serve_file(handler, rel_path):
    """Serve a static file from ROOT_DIR."""
    # Security: prevent directory traversal
    abs_path = (ROOT_DIR / rel_path).resolve()
    if not str(abs_path).startswith(str(ROOT_DIR)):
        handler.send_error(403)
        return
    if not abs_path.is_file():
        handler.send_error(404)
        return

    ext = abs_path.suffix.lower()
    mime = MIME_MAP.get(ext, "application/octet-stream")
    content = abs_path.read_bytes()

    handler.send_response(200)
    handler.send_header("Content-Type", mime)
    handler.send_header("Content-Length", len(content))
    handler.send_header("Cache-Control", "public, max-age=3600")
    handler.end_headers()
    handler.wfile.write(content)


def serve_json(handler, data):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Content-Length", len(body))
    handler.end_headers()
    handler.wfile.write(body)


class APIHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]  # strip query params

        # API: market intelligence data
        if path == "/api/market-intel":
            intel_path = ROOT_DIR / "data" / "market-intel.json"
            if intel_path.is_file():
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(intel_path.read_bytes())
            else:
                serve_json(self, {"error": "Market intel data not found"})
            return

        # API: health check
        if path == "/api/health":
            serve_json(self, {"status": "ok", "hasAI": bool(DEEPSEEK_KEY)})
            return

        # Serve static files
        if path == "/" or path == "":
            serve_file(self, "index.html")
            return
        if path.endswith(".html") or path.endswith(".css") or path.endswith(".js") \
           or path.endswith(".json") or path.endswith(".png") or path.endswith(".ico"):
            serve_file(self, path.lstrip("/"))
            return

        # Fallback: try index.html for SPA-like behavior
        serve_file(self, "index.html")

    def do_POST(self):
        if self.path == "/api/analyze":
            length = int(self.headers.get("content-length", 0))
            body = json.loads(self.rfile.read(length))
            result = self.call_deepseek(body)
            serve_json(self, result)
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def call_deepseek(self, user_input):
        if not DEEPSEEK_KEY:
            return {"error": "API key not configured", "fallback": True}
        user_msg = f"""品类：{user_input.get('category', '')}
价格：{user_input.get('priceMin', 0)}-{user_input.get('priceMax', 0)}元
人群：{user_input.get('audience', '')}
佣金：{user_input.get('commission', 0)}%
季节性：{user_input.get('season', '无明显季节性')}
竞品：{user_input.get('competitorLevel', '未知')}
供应链：{user_input.get('supplyChain', '未填写')}
月销：{user_input.get('monthlySales', '未知')}
备注：{user_input.get('notes', '无')}"""
        req = urllib.request.Request(
            DEEPSEEK_URL,
            data=json.dumps({
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg}
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            }).encode(),
            headers={
                "Authorization": f"Bearer {DEEPSEEK_KEY}",
                "Content-Type": "application/json"
            }
        )
        try:
            resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
            content = resp["choices"][0]["message"]["content"].strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]
            return json.loads(content)
        except Exception as e:
            return {"error": f"DeepSeek API error: {str(e)}", "fallback": True}

    def log_message(self, format, *args):
        # Quiet logging
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = http.server.HTTPServer(("0.0.0.0", port), APIHandler)
    ai_status = "enabled" if DEEPSEEK_KEY else "disabled (local fallback only)"
    print(f"选品分析 v3 running on :{port} | AI: {ai_status}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()
