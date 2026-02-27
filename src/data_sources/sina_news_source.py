# src/data_sources/sina_news_source.py
"""
新浪新闻数据源适配器
将原有新浪爬虫适配到统一数据源接口
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import time
import random

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.models import Article, ArticleCategory
from src.data_sources.base_source import DataSource

# 导入原有的新浪爬虫组件（现在在同一目录下）
try:
    # 直接导入，因为都在同一目录
    from parser import NewsParser
    from sina_crawler import SinaNewsCrawler
    print("✅ 成功导入原有爬虫")
    HAS_CRAWLER = True
except ImportError as e:
    print(f"⚠️ 导入原有爬虫失败: {e}，将使用简化模式")
    NewsParser = None
    SinaNewsCrawler = None
    HAS_CRAWLER = False

class SinaNewsDataSource(DataSource):
    """新浪新闻数据源"""
    
    @classmethod
    def get_required_config_keys(cls) -> List[str]:
        """返回必需的配置键列表"""
        return ['base_url']  # 只需要 base_url 是必需的
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        # 分类映射（新浪分类 -> 统一分类）
        self.category_mapping = {
            '首页': ArticleCategory.GENERAL,
            '国内': ArticleCategory.DOMESTIC,
            '国际': ArticleCategory.INTERNATIONAL,
            '科技': ArticleCategory.TECHNOLOGY,
            '体育': ArticleCategory.SPORTS,
            '娱乐': ArticleCategory.ENTERTAINMENT,
            '财经': ArticleCategory.FINANCE,
        }
        
        # 初始化原有爬虫
        self.parser = None
        self.crawler = None
        self.use_simple_mode = not HAS_CRAWLER
        
        if HAS_CRAWLER:
            try:
                self.parser = NewsParser()
                self.crawler = SinaNewsCrawler()
                self.logger.info("✅ 使用原有新浪爬虫")
            except Exception as e:
                self.logger.warning(f"初始化原有爬虫失败: {e}，使用简化模式")
                self.use_simple_mode = True
        else:
            self.use_simple_mode = True
            self.logger.info("使用简化模式（直接HTTP请求）")
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
    
    def fetch_articles(self, limit: int = 50) -> List[Article]:
        """获取文章列表 - 实现抽象方法"""
        articles = []
        success = False
        
        try:
            if self.use_simple_mode:
                articles = self._fetch_simple(limit)
            else:
                articles = self._fetch_with_crawler(limit)
            
            success = True
            self.update_fetch_stats(success=True)  # 使用基类的方法
            self.logger.info(f"✅ 获取 {len(articles)} 条新浪新闻")
            
        except Exception as e:
            self.update_fetch_stats(success=False)  # 使用基类的方法
            self.logger.error(f"❌ 获取新浪新闻失败: {e}")
        
        return articles
    
    def get_article_detail(self, article_id: str) -> Optional[Article]:
        """获取文章详情 - 实现抽象方法"""
        if article_id.startswith('http'):
            try:
                if self.use_simple_mode:
                    return None
                else:
                    if self.crawler and self.parser:
                        html = self.crawler._fetch_page(article_id)
                        if html:
                            category = '科技' if 'tech' in article_id else '首页'
                            detail = self.parser.parse_news_detail(html, article_id, category)
                            if detail:
                                return self._convert_to_article(detail)
            except Exception as e:
                self.logger.warning(f"获取文章详情失败 {article_id}: {e}")
        
        return None
    
    def fetch_data(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取数据（兼容DataSourceManager）"""
        articles = self.fetch_articles(limit)
        return [a.to_dict() for a in articles]
    
    def _fetch_with_crawler(self, limit: int) -> List[Article]:
        """使用原有爬虫获取数据"""
        articles = []
        
        # 获取配置的分类
        categories = self.config.get('categories', [
            {'name': '科技', 'url': 'https://news.sina.com.cn/tech/', 'max_articles': 5}
        ])
        
        for cat_config in categories[:3]:  # 限制分类数量，避免太慢
            cat_name = cat_config.get('name')
            cat_url = cat_config.get('url')
            cat_limit = cat_config.get('max_articles', 10)
            
            self.logger.info(f"爬取分类: {cat_name}")
            
            try:
                html = self.crawler._fetch_page(cat_url)
                if not html:
                    continue
                
                news_links = self.parser.parse_news_list(html, cat_name)
                news_links = news_links[:cat_limit]
                
                for link in news_links:
                    detail = self.crawler.crawl_news_detail(link['url'], cat_name)
                    if detail:
                        article = self._convert_to_article(detail)
                        if article:
                            articles.append(article)
                    
                    time.sleep(random.uniform(1, 2))
                    
            except Exception as e:
                self.logger.error(f"爬取分类 {cat_name} 失败: {e}")
                continue
        
        return articles[:limit]
    
    def _fetch_simple(self, limit: int) -> List[Article]:
        """简化版：直接请求并解析"""
        articles = []
        tech_url = "https://news.sina.com.cn/tech/"
        
        try:
            response = self.session.get(tech_url, timeout=10)
            if response.status_code != 200:
                return articles
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)
            
            for link in links[:limit]:
                href = link['href']
                title = link.get_text().strip()
                
                if len(title) < 10 or 'javascript' in href:
                    continue
                
                if 'sina.com.cn' in href and '/doc-' in href:
                    if href.startswith('//'):
                        href = 'https:' + href
                    elif href.startswith('/'):
                        href = 'https://news.sina.com.cn' + href
                    
                    article = Article(
                        source=self.name,
                        source_id=href,
                        title=f"[新浪] {title}",
                        url=href,
                        description=title,
                        category=ArticleCategory.TECHNOLOGY,
                        tags=['科技'],
                        score=0,
                        comments=0,
                        author='新浪科技',
                        published_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        fetched_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        extra={'original_category': '科技'}
                    )
                    articles.append(article)
                    
        except Exception as e:
            self.logger.error(f"简化版获取失败: {e}")
        
        return articles
    
    def get_info(self) -> Dict[str, Any]:
        """获取数据源信息"""
        return {
            'name': self.name,
            'type': 'sina_news',
            'status': 'active' if self.config.get('enabled', True) else 'disabled',
            'last_fetch_time': self.last_fetch_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_fetch_time else None,
            'fetch_count': self.fetch_count,
            'error_count': self.error_count,
            'use_simple_mode': self.use_simple_mode
        }
    
    def _convert_to_article(self, news_item: Dict) -> Optional[Article]:
        """将新浪新闻格式转换为统一Article格式"""
        try:
            category_map = {
                '科技': ArticleCategory.TECHNOLOGY,
                '国内': ArticleCategory.DOMESTIC,
                '国际': ArticleCategory.INTERNATIONAL,
                '财经': ArticleCategory.FINANCE,
                '体育': ArticleCategory.SPORTS,
                '娱乐': ArticleCategory.ENTERTAINMENT,
            }
            
            original_category = news_item.get('category', '科技')
            category = category_map.get(original_category, ArticleCategory.TECHNOLOGY)
            
            return Article(
                source=self.name,
                source_id=news_item.get('url', ''),
                title=f"[新浪] {news_item.get('title', '')}",
                url=news_item.get('url', ''),
                description=news_item.get('summary', '') or news_item.get('content', '')[:200],
                content=news_item.get('content', ''),
                category=category,
                tags=news_item.get('keywords', []),
                score=0,
                comments=0,
                author=news_item.get('source', '新浪新闻'),
                published_at=news_item.get('publish_time'),
                fetched_at=news_item.get('crawl_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                extra={
                    'original_category': original_category,
                    'content_length': news_item.get('content_length', 0),
                    'images': news_item.get('images', [])
                }
            )
        except Exception as e:
            self.logger.warning(f"转换文章失败: {e}")
            return None