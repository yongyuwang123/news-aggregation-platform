# src/core/models.py
"""
统一数据模型
定义Article类，统一GitHub、Hacker News和新浪新闻的数据格式
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class ArticleCategory(Enum):
    """文章分类枚举"""
    GENERAL = "general"
    TECHNOLOGY = "technology"
    SCIENCE = "science"
    BUSINESS = "business"
    ENTERTAINMENT = "entertainment"
    SPORTS = "sports"
    HEALTH = "health"
    DOMESTIC = "domestic"
    INTERNATIONAL = "international"
    FINANCE = "finance"

@dataclass
class Article:
    """统一文章/项目数据模型"""
    
    # 核心字段
    source: str                    # 数据源: 'github_trending' 或 'hacker_news' 或 'sina_news'
    source_id: str                  # 原始ID (GitHub全名 或 Hacker News ID 或 新闻URL)
    title: str                      # 标题
    url: str                        # 链接
    description: str = ""           # 描述/摘要
    content: str = ""               # 完整内容（可选）
    
    # 分类和标签
    category: ArticleCategory = ArticleCategory.GENERAL    # 分类（使用枚举）
    tags: List[str] = None          # 标签
    
    # 指标数据
    score: int = 0                   # 分数/星标数/热度
    comments: int = 0                # 评论数/Fork数
    author: str = ""                 # 作者
    
    # 时间信息
    published_at: Optional[str] = None  # 发布时间
    fetched_at: str = None              # 抓取时间
    
    # 扩展字段（存储各数据源特有的信息）
    extra: Dict[str, Any] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.tags is None:
            self.tags = []
        if self.extra is None:
            self.extra = {}
        if self.fetched_at is None:
            self.fetched_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 如果传入的是字符串分类，转换为枚举
        if isinstance(self.category, str):
            try:
                self.category = ArticleCategory(self.category)
            except ValueError:
                self.category = ArticleCategory.GENERAL
    def to_dict(self) -> Dict:
        """转换为字典，处理枚举序列化"""
        data = asdict(self)
        # 将枚举转换为值
        if 'category' in data and isinstance(data['category'], ArticleCategory):
            data['category'] = data['category'].value
        return data

    def to_dict(self) -> Dict:
        """转换为字典，处理枚举序列化"""
        data = asdict(self)
        # 将枚举转换为值
        if isinstance(data['category'], ArticleCategory):
            data['category'] = data['category'].value
        return data
    
    @classmethod
    def from_github(cls, github_item: Dict) -> 'Article':
        """从GitHub数据创建Article"""
        return cls(
            source='github_trending',
            source_id=github_item['name'],
            title=f"[GitHub] {github_item['name']}",
            url=github_item['url'],
            description=github_item.get('description', ''),
            content='',
            category=ArticleCategory.TECHNOLOGY,
            tags=[github_item.get('language', 'Unknown')] if github_item.get('language') != 'Unknown' else [],
            score=github_item.get('total_stars', 0),
            comments=github_item.get('forks', 0),
            author=github_item['name'].split('/')[0] if '/' in github_item['name'] else '',
            published_at=None,
            fetched_at=github_item.get('fetched_at', ''),
            extra={
                'stars_today': github_item.get('stars_today', 0),
                'language': github_item.get('language', 'Unknown'),
                'full_name': github_item['name']
            }
        )
    
    @classmethod
    def from_hacker_news(cls, hn_item: Dict) -> 'Article':
        """从Hacker News数据创建Article"""
        return cls(
            source='hacker_news',
            source_id=str(hn_item.get('id', '')),
            title=hn_item.get('title', ''),
            url=hn_item.get('url', f"https://news.ycombinator.com/item?id={hn_item.get('id')}"),
            description=hn_item.get('text', hn_item.get('title', ''))[:200],
            content=hn_item.get('text', ''),
            category=ArticleCategory.TECHNOLOGY,
            tags=[],
            score=hn_item.get('score', 0),
            comments=hn_item.get('descendants', 0),
            author=hn_item.get('author', 'unknown'),
            published_at=hn_item.get('publish_time', ''),
            fetched_at=hn_item.get('fetched_at', ''),
            extra={
                'timestamp': hn_item.get('timestamp', 0),
            }
        )
    
    @classmethod
    def from_sina(cls, sina_item: Dict) -> 'Article':
        """从新浪新闻数据创建Article"""
        # 分类映射
        category_map = {
            '科技': ArticleCategory.TECHNOLOGY,
            '国内': ArticleCategory.DOMESTIC,
            '国际': ArticleCategory.INTERNATIONAL,
            '财经': ArticleCategory.FINANCE,
            '体育': ArticleCategory.SPORTS,
            '娱乐': ArticleCategory.ENTERTAINMENT,
        }
        
        original_category = sina_item.get('category', '科技')
        category = category_map.get(original_category, ArticleCategory.TECHNOLOGY)
        
        return cls(
            source='sina_news',
            source_id=sina_item.get('url', ''),
            title=f"[新浪] {sina_item.get('title', '')}",
            url=sina_item.get('url', ''),
            description=sina_item.get('summary', '') or sina_item.get('content', '')[:200],
            content=sina_item.get('content', ''),
            category=category,
            tags=sina_item.get('keywords', []),
            score=0,  # 新浪新闻没有评分
            comments=0,
            author=sina_item.get('source', '新浪新闻'),
            published_at=sina_item.get('publish_time'),
            fetched_at=sina_item.get('crawl_time', ''),
            extra={
                'original_category': original_category,
                'content_length': sina_item.get('content_length', 0),
                'images': sina_item.get('images', [])
            }
        )
    
    def display(self) -> str:
        """格式化显示"""
        if self.source == 'github_trending':
            return (
                f"📦 {self.title}\n"
                f"   {self.description[:80]}...\n"
                f"   ⭐ {self.score:,} stars | 🍴 {self.comments:,} forks"
            )
        elif self.source == 'hacker_news':
            return (
                f"📰 {self.title}\n"
                f"   👤 {self.author} | ⭐ {self.score} points | 💬 {self.comments} comments"
            )
        else:  # sina_news
            return (
                f"🇨🇳 {self.title}\n"
                f"   {self.description[:80]}...\n"
                f"   🏷️ {self.category.value} | 👤 {self.author}"
            )