import feedparser
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.core.models import Article, ArticleCategory
from src.data_sources.base_source import DataSource

class RSSDataSource(DataSource):
    """RSS 订阅数据源"""
    
    @classmethod
    def get_required_config_keys(cls) -> List[str]:
        return ['feed_url']
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.feed_url = config['feed_url']
        self.category = ArticleCategory(config.get('category', 'technology'))
    
    def fetch_articles(self, limit: int = 50) -> List[Article]:
        feed = feedparser.parse(self.feed_url)
        articles = []
        for entry in feed.entries[:limit]:
            # 提取标签（如果有）
            tags = [tag.term for tag in entry.get('tags', [])] if hasattr(entry, 'tags') else []
            article = Article(
                source=self.name,
                source_id=entry.get('id', entry.link),
                title=entry.title,
                url=entry.link,
                description=entry.get('summary', '')[:200],
                content=entry.get('summary', ''),
                category=self.category,
                tags=tags,
                published_at=entry.get('published', datetime.now().isoformat()),
                fetched_at=datetime.now().isoformat(),
                extra={'feed_title': feed.feed.get('title', '')}
            )
            articles.append(article)
        self.logger.info(f"从 {self.feed_url} 抓取 {len(articles)} 条")
        return articles
    
    def get_article_detail(self, article_id: str) -> Optional[Article]:
        # 可选：单独抓取详情页（如需要全文）
        return None