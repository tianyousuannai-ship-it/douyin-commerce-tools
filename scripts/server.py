#!/usr/bin/env python3
"""选品分析后端 v2 - DeepSeek API 代理"""
import json, os, http.server, urllib.request

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

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

class APIHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/analyze":
            length = int(self.headers.get("content-length", 0))
            body = json.loads(self.rfile.read(length))
            result = self.call_deepseek(body)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def call_deepseek(self, user_input):
        if not DEEPSEEK_KEY:
            return {"error": "API key not configured"}
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
            return {"error": f"DeepSeek API error: {str(e)}"}

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    server = http.server.HTTPServer(("0.0.0.0", port), APIHandler)
    print(f"DeepSeek proxy v2 running on :{port}")
    server.serve_forever()
