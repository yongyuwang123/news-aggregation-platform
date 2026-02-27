# test_sina.py
"""
测试新浪新闻源
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.data_sources.sina_news_source import SinaNewsDataSource  # 改这里

def test_sina():
    """测试新浪新闻采集"""
    
    print("="*60)
    print("测试新浪新闻源")
    print("="*60)
    
    # 配置
    config = {
        'enabled': True,
        'base_url': 'https://news.sina.com.cn',
        'categories': [
            {'name': '科技', 'url': 'https://news.sina.com.cn/tech/', 'max_articles': 3},
            {'name': '国内', 'url': 'https://news.sina.com.cn/china/', 'max_articles': 2},
        ]
    }
    
    # 初始化数据源
    source = SinaNewsDataSource('sina_test', config)  # 改这里
    
    # 获取文章
    print("\n开始采集新浪新闻...")
    articles = source.fetch_articles(limit=5)
    
    print(f"\n✅ 获取到 {len(articles)} 篇文章")
    
    for i, article in enumerate(articles, 1):
        print(f"\n{i}. {article.title}")
        print(f"   📝 {article.description[:80]}..." if len(article.description) > 80 else f"   📝 {article.description}")
        print(f"   🏷️ 分类: {article.category.value if hasattr(article.category, 'value') else article.category}")
        print(f"   👤 作者: {article.author}")
        print(f"   🕒 时间: {article.published_at or article.fetched_at}")
        print(f"   🔗 {article.url}")
    
    print("\n" + "="*60)
    print("测试完成")

if __name__ == "__main__":
    test_sina()