// Vercel Serverless Function - DeepSeek API 代理
// 部署后在 Vercel 设置环境变量 DEEPSEEK_API_KEY

export default async function handler(req, res) {
  // CORS
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    return res.status(200).end();
  }

  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const apiKey = process.env.DEEPSEEK_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: "API key not configured on server" });
  }

  const { category, priceMin, priceMax, audience, commission, notes } = req.body;

  const userMsg = `品类：${category || ""}，价格：${priceMin || 0}-${priceMax || 999}元，人群：${audience || ""}，佣金：${commission || 20}%，备注：${notes || ""}`;

  const systemPrompt = `你是抖音带货选品分析专家。严格按JSON格式输出（不要markdown代码块）：
{"marketScore":0-100,"compScore":0-100,"profitScore":0-100,"marketAnalysis":"市场分析100字","compAnalysis":"竞争分析100字","contentStrategy":["策略1","策略2","策略3","策略4"],"risks":["风险1"],"overallVerdict":"建议入手|谨慎评估|不太建议","tags":["标签1","标签2"]}`;

  try {
    const resp = await fetch("https://api.deepseek.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: "deepseek-chat",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: userMsg },
        ],
        temperature: 0.7,
        max_tokens: 800,
      }),
    });

    const json = await resp.json();
    const content = (json.choices?.[0]?.message?.content || "").replace(/```json|```/g, "").trim();
    const data = JSON.parse(content);
    return res.status(200).json(data);
  } catch (e) {
    return res.status(200).json({ error: e.message });
  }
}
