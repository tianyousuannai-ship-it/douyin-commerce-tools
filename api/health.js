// Vercel Serverless Function - 健康检查
export default function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.status(200).json({
    status: "ok",
    hasAI: Boolean(process.env.DEEPSEEK_API_KEY),
    version: "v3"
  });
}
