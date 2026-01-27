"""
新浪新闻爬虫 - 配置化版本
"""
import time
import random
import logging
from typing import List, Dict, Optional
from datetime import datetime

from config.settings import config
from database.news_db import NewsDatabase
from .parser import NewsParser

# 在 sina_crawler.py 开头添加：
from utils.logger import setup_logging
from utils.exporter import DataExporter

class SinaNewsCrawler:
    """配置化的新浪新闻爬虫"""
    
    def __init__(self):
        # 从配置加载
        self.base_url = config.get('crawler.base_url')
        self.timeout = config.get('crawler.timeout')
        self.max_retries = config.get('crawler.max_retries')
        self.delay_range = config.get('crawler.delay_range')
        
        # 初始化组件
        self.db = NewsDatabase(config.get('database.path'))
        self.parser = NewsParser()
        
        # 请求会话
        self.session = self._create_session()
        
        # 统计
        self.stats = {
            'total_crawled': 0,
            'success': 0,
            'failed': 0,
            'duplicates': 0
        }
    
    def _create_session(self):
        """创建请求会话"""
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置请求头
        session.headers.update({
            'User-Agent': config.get('crawler.user_agent'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        return session
    
    def _delay(self):
        """随机延迟"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def crawl_category(self, category_config: Dict) -> List[Dict]:
        """爬取指定分类的新闻"""
        category_name = category_config['name']
        url = category_config['url']
        max_news = category_config['max_news']
        
        logging.info(f"开始爬取分类: {category_name}")
        
        try:
            # 获取页面
            html = self._fetch_page(url)
            if not html:
                return []
            
            # 解析新闻链接
            news_links = self.parser.parse_news_list(html, category_name)
            
            # 增量爬取：只爬取新链接
            if config.get('incremental.enabled'):
                news_links = self._filter_existing_links(news_links)
            
            # 限制数量
            news_links = news_links[:max_news]
            
            # 爬取新闻详情
            news_data = []
            for i, link in enumerate(news_links, 1):
                logging.info(f"爬取进度: {i}/{len(news_links)} - {link['title'][:30]}...")
                
                news_detail = self.crawl_news_detail(link['url'], category_name)
                if news_detail:
                    news_data.append(news_detail)
                
                self._delay()  # 延迟避免被封
            
            logging.info(f"分类 {category_name} 完成: {len(news_data)} 篇新闻")
            return news_data
            
        except Exception as e:
            logging.error(f"爬取分类 {category_name} 失败: {e}")
            return []
    
    def _fetch_page(self, url: str, retry_count: int = 0) -> Optional[str]:
        """获取页面内容（带重试）"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
            
        except Exception as e:
            if retry_count < self.max_retries:
                logging.warning(f"请求失败，第{retry_count + 1}次重试: {url}")
                time.sleep(2 ** retry_count)  # 指数退避
                return self._fetch_page(url, retry_count + 1)
            else:
                logging.error(f"请求最终失败: {url} - {e}")
                return None
    
    def _filter_existing_links(self, news_links: List[Dict]) -> List[Dict]:
        """过滤已存在的新闻链接"""
        filtered = []
        
        for link in news_links:
            # 检查URL是否已存在
            if not self.db.is_duplicate_title(link['title']):
                filtered.append(link)
            else:
                self.stats['duplicates'] += 1
        
        logging.info(f"去重后剩余: {len(filtered)}/{len(news_links)} 个链接")
        return filtered
    
    def crawl_news_detail(self, url: str, category: str) -> Optional[Dict]:
        """爬取新闻详情"""
        try:
            html = self._fetch_page(url)
            if not html:
                return None
            
            news_detail = self.parser.parse_news_detail(html, url, category)
            if not news_detail:
                return None
            
            # 添加爬取时间
            news_detail['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 保存到数据库
            if config.get('output.save_to_database'):
                success = self.db.save_news(news_detail)
                if success:
                    self.stats['success'] += 1
                else:
                    self.stats['failed'] += 1
            
            self.stats['total_crawled'] += 1
            return news_detail
            
        except Exception as e:
            logging.error(f"爬取新闻详情失败 {url}: {e}")
            self.stats['failed'] += 1
            return None
    
    def crawl_all_categories(self) -> Dict[str, List[Dict]]:
        """爬取所有启用的分类"""
        if not config.get('categories.enabled'):
            logging.warning("分类爬取已禁用")
            return {}
        
        all_news = {}
        category_configs = config.get('categories.list', [])
        
        for cat_config in category_configs:
            news_data = self.crawl_category(cat_config)
            all_news[cat_config['name']] = news_data
            
            # 分类间延迟
            if cat_config != category_configs[-1]:
                time.sleep(random.uniform(3, 6))
        
        return all_news
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        db_stats = self.db.get_news_count()
        return {
            'crawl_stats': self.stats,
            'database_stats': db_stats
        }
    
    def export_data(self, news_data: Dict[str, List[Dict]]):
        """导出数据到文件"""
        if not config.get('output.save_json') and not config.get('output.save_csv'):
            return
        
        from utils.exporter import DataExporter
        exporter = DataExporter(config.get('output.output_dir'))
        
        if config.get('output.save_json'):
            exporter.save_to_json(news_data)
        
        if config.get('output.save_csv'):
            exporter.save_to_csv(news_data)
    
    def run(self):
        """运行爬虫"""
        logging.info("=" * 60)
        logging.info("新浪新闻爬虫 - 配置化版本")
        logging.info("=" * 60)
        
        start_time = time.time()
        
        # 爬取新闻
        news_data = self.crawl_all_categories()
        
        # 导出数据
        self.export_data(news_data)
        
        # 显示统计
        stats = self.get_stats()
        self._print_statistics(stats)
        
        end_time = time.time()
        logging.info(f"总耗时: {end_time - start_time:.2f}秒")
        
        return news_data
    
    def _print_statistics(self, stats: Dict):
        """打印统计信息"""
        print("\n" + "=" * 60)
        print("📊 爬虫统计")
        print("=" * 60)
        
        crawl_stats = stats['crawl_stats']
        db_stats = stats['database_stats']
        
        print(f"总爬取: {crawl_stats['total_crawled']} 篇")
        print(f"成功保存: {crawl_stats['success']} 篇")
        print(f"失败: {crawl_stats['failed']} 篇")
        print(f"重复跳过: {crawl_stats['duplicates']} 篇")
        
        print(f"\n📁 数据库统计:")
        print(f"  总新闻数: {db_stats['total']} 篇")
        
        for category, count in db_stats['by_category'].items():
            print(f"  {category}: {count} 篇")
        
        print("=" * 60)