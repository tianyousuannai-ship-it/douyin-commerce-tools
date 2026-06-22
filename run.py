#!/usr/bin/env python3
"""选品分析服务 - 静态文件 + DeepSeek AI 代理"""
import json, os, sys, http.server, urllib.request

KEY = os.environ.get("DEEPSEEK_API_KEY", "")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

PROMPT = """你是抖音宠物赛道带货选品分析专家。给出专业分析，严格按JSON格式输出（不要markdown代码块）：
{"marketScore":0-100,"compScore":0-100,"profitScore":0-100,"marketAnalysis":"100字内","compAnalysis":"100字内","contentStrategy":["策略1","策略2","策略3","策略4"],"risks":["风险1","风险2"],"overallVerdict":"建议入手|谨慎评估|不太建议","tags":["标签1","标签2"]}
评分:宠物用品刚需+15,高客单+10;热门品类(猫粮狗粮猫砂)+25竞争,小众-15;佣金>30%+20利润,客单50-200+15。策略要结合品类具体。"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/api/analyze":
            self.send_error(404); return
        body = json.loads(self.rfile.read(int(self.headers["content-length"])))
        msg = f"品类：{body.get('category','')}，价格：{body.get('priceMin',0)}-{body.get('priceMax',0)}元，人群：{body.get('audience','')}，佣金：{body.get('commission',0)}%，备注：{body.get('notes','')}"
        try:
            req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions",
                data=json.dumps({"model":"deepseek-chat","messages":[{"role":"system","content":PROMPT},{"role":"user","content":msg}],"temperature":0.7,"max_tokens":800}).encode(),
                headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
            resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
            txt = resp["choices"][0]["message"]["content"].strip()
            if txt.startswith("```"): txt = txt.split("\n",1)[1].rstrip("`").strip()
            self.send_json(json.loads(txt))
        except Exception as e:
            self.send_json({"error":str(e)})

    def send_json(self, data):
        self.send_response(200); self.send_header("Content-Type","application/json;charset=utf-8")
        self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
        self.wfile.write(json.dumps(data,ensure_ascii=False).encode())

    def do_OPTIONS(self):
        self.send_response(200); self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type"); self.end_headers()

if not KEY:
    print("ERROR: DEEPSEEK_API_KEY not set"); sys.exit(1)

http.server.HTTPServer(("0.0.0.0",PORT), Handler).serve_forever()
