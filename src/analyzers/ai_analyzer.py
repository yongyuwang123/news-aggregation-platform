import os
import json
from typing import List, Dict, Optional
from openai import OpenAI
from src.core.models import Article

class AIAnalyzer:
    """调用大模型对文章进行分析"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = "deepseek-chat"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量")
        self.base_url = base_url or "https://api.deepseek.com/v1"
        self.model = model
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def summarize_article(self, article: Article) -> str:
        """生成单篇文章摘要"""
        prompt = f"请用 50 字以内总结以下文章的核心内容：\n标题：{article.title}\n内容：{article.content[:1000]}"
        response = self._call_llm(prompt)
        return response.strip()

    def analyze_daily_trends(self, articles: List[Article]) -> Dict:
        """分析每日文章，返回趋势总结和推荐"""
        # 拼接文章标题和摘要
        texts = "\n".join([f"- {a.title}：{a.description[:100]}" for a in articles[:10]])
        prompt = f"""今日技术文章列表：
{texts}

请完成：
1. 用一段话总结今天的主要技术趋势。
2. 列出最值得深入阅读的 3 篇文章，并说明理由。
输出格式：JSON，包含 summary (字符串) 和 recommendations (列表，每个元素包含 title 和 reason)。
"""
        response = self._call_llm(prompt)
        try:
            return json.loads(response)
        except:
            # 如果返回的不是 JSON，则包装一下
            return {"summary": response, "recommendations": []}

    def _call_llm(self, prompt: str) -> str:
        """调用大模型 API"""
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"AI 调用失败：{e}")
            return "AI 分析暂时不可用。"