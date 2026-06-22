#!/usr/bin/env python3
"""选品分析后端 - DeepSeek API 代理"""
import json, os, http.server, urllib.request, urllib.parse

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

SYSTEM_PROMPT = """你是抖音宠物赛道带货选品分析专家。根据用户输入的商品信息，给出专业分析。
严格按以下 JSON 格式输出，不要输出其他内容：
{
  "marketScore": 0-100的整数,
  "compScore": 0-100的整数(分数越高代表竞争越激烈),
  "profitScore": 0-100的整数,
  "marketAnalysis": "市场分析，100字以内",
  "compAnalysis": "竞争格局分析，100字以内",
  "contentStrategy": ["策略1", "策略2", "策略3", "策略4"],
  "risks": ["风险1", "风险2"],
  "overallVerdict": "建议入手" 或 "谨慎评估" 或 "不太建议",
  "tags": ["标签1", "标签2"]
}

评分标准：
- 市场潜力：宠物用品刚需+15分，高客单价+10分，新奇品类+5分
- 竞争程度：热门品类(猫粮/狗粮/猫砂)+25分，小众品类-15分
- 利润空间：佣金>30%+20分，客单价50-200+15分
- 内容策略要具体，结合品类特点
- 风险提示要真实，不要敷衍"""

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

        user_msg = f"""商品品类：{user_input.get('category', '')}
价格区间：{user_input.get('priceMin', 0)}-{user_input.get('priceMax', 0)}元
目标人群：{user_input.get('audience', '')}
佣金比例：{user_input.get('commission', 0)}%
补充说明：{user_input.get('notes', '无')}"""

        req = urllib.request.Request(
            DEEPSEEK_URL,
            data=json.dumps({
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }).encode(),
            headers={
                "Authorization": f"Bearer {DEEPSEEK_KEY}",
                "Content-Type": "application/json"
            }
        )
        try:
            resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
            content = resp["choices"][0]["message"]["content"]
            # Strip markdown code fences if present
            content = content.strip()
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
    print(f"DeepSeek proxy running on :{port}")
    server.serve_forever()
