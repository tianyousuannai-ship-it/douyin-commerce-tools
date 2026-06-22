// Vercel Serverless Function - DeepSeek AI 选品分析引擎 v2
// 环境变量: DEEPSEEK_API_KEY

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") return res.status(200).end();
  if (req.method !== "POST") return res.status(405).json({ error: "Method not allowed" });

  const apiKey = process.env.DEEPSEEK_API_KEY;
  if (!apiKey) return res.status(500).json({ error: "API key not configured" });

  const {
    category, priceMin, priceMax, audience, commission, notes,
    season, supplyChain, competitorLevel, monthlySales
  } = req.body;

  const userMsg = [
    `品类：${category || "未填写"}`,
    `价格区间：${priceMin || 0}-${priceMax || 999}元`,
    `目标人群：${audience || "未填写"}`,
    `佣金比例：${commission || 0}%`,
    `季节性：${season || "无明显季节性"}`,
    `供应链情况：${supplyChain || "未填写"}`,
    `竞品强度：${competitorLevel || "未知"}`,
    `预估月销：${monthlySales || "未知"}`,
    `备注：${notes || "无"}`
  ].join("\n");

  const systemPrompt = `你是顶级抖音电商选品分析专家，精通抖音电商生态、流量算法、带货逻辑和品类趋势。
请基于用户输入的商品信息，做一次完整的选品诊断分析。

严格按以下 JSON 格式输出，不要 markdown 代码块，不要其他内容：

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
    "marketHeat": {
      "score": 0-100,
      "summary": "市场热度分析，80字以内",
      "factors": ["利好因素1", "利好因素2"]
    },
    "competition": {
      "score": 0-100,
      "summary": "竞争格局分析，80字以内",
      "entryBarrier": "进入门槛评估",
      "differentiation": "差异化切入点建议"
    },
    "profit": {
      "score": 0-100,
      "summary": "利润评估，80字以内",
      "roiEstimate": "预估ROI范围，如1:2到1:4",
      "breakEven": "预估回本周期"
    },
    "trend": {
      "score": 0-100,
      "summary": "趋势分析，80字以内",
      "direction": "上升/平稳/下降",
      "seasonality": "季节性影响评估"
    },
    "contentFit": {
      "score": 0-100,
      "summary": "内容适配度，80字以内",
      "contentType": "推荐的内容形式",
      "difficulty": "内容制作难度评估"
    },
    "supplyChain": {
      "score": 0-100,
      "summary": "供应链评估，80字以内"
    }
  },
  "overall": {
    "totalScore": 0-100,
    "verdict": "建议入手|谨慎评估|不太建议",
    "recommendedAction": "一句话行动建议",
    "riskLevel": "低/中/高"
  },
  "contentStrategy": [
    "策略1，要具体且结合品类特点",
    "策略2",
    "策略3",
    "策略4",
    "策略5"
  ],
  "risks": [
    {"risk": "风险描述", "severity": "高/中/低", "mitigation": "应对建议"}
  ],
  "marketRefs": {
    "similarProducts": "市面上同类产品的表现参考",
    "priceRange": "该品类抖音主流价格带",
    "targetGMV": "预估月GMV范围"
  },
  "tags": ["标签1", "标签2"]
}

评分参考标准：
- marketHeat（市场热度）：品类搜索量、短视频播放量、直播观看量热度。刚需/高频品类加分，冷门小众品类减分。
- competition（竞争强度）：分数越高代表竞争越激烈。头部品牌集中、大量带货达人做的品类加分，细分蓝海减分。
- profit（利润空间）：考虑佣金、客单价、退货率、运费成本。佣金高+客单价适中加分。
- trend（趋势走向）：该品类近期的搜索增长/下滑趋势。上升趋势加分，下滑趋势减分。
- contentFit（内容适配度）：该品类是否容易产出优质带货内容。适合展示效果、容易拍出吸引力的加分。
- supplyChain（供应链成熟度）：是否有稳定货源、是否有价格优势、是否有独家代理可能。

策略要求：必须具体到品类，结合真实抖音带货场景。比如不会只说"做直播"，而会说"每天下午3点开播，以工厂实拍为背景，主打源头价格"。
风险要求：必须真实，每条风险都要有应对建议。
市场参考：给出该品类在抖音的真实参考数据。`;

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
        max_tokens: 1500,
      }),
    });

    const json = await resp.json();
    const content = (json.choices?.[0]?.message?.content || "")
      .replace(/```json|```/g, "")
      .trim();
    const data = JSON.parse(content);
    return res.status(200).json(data);
  } catch (e) {
    return res.status(200).json({ error: e.message });
  }
}
