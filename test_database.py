# test_database.py (修正版)
"""
测试数据库存储功能
"""

import sys
from pathlib import Path
import json

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from src.core.models import Article
from src.storage.database import Database

def test_github_to_database():
    """测试GitHub数据存入数据库"""
    print("="*60)
    print("测试1: GitHub数据存入数据库")
    print("="*60)
    
    filename = 'github_trending_test.json'
    if not Path(filename).exists():
        print(f"❌ 找不到文件: {filename}")
        return []
    
    print(f"📁 找到文件: {filename}")
    
    with open(filename, 'r', encoding='utf-8') as f:
        github_data = json.load(f)
    
    print(f"📦 读取到 {len(github_data)} 条GitHub数据")
    
    articles = []
    for i, item in enumerate(github_data[:10]):
        article = Article.from_github(item)
        # 确保category是字符串
        if hasattr(article.category, 'value'):
            article.category = article.category.value
        articles.append(article)
        print(f"   ✓ {i+1}. {article.title[:50]}...")
    
    # 修改这里：使用 save_article 循环保存，而不是 save_articles
    db = Database()
    saved_count = 0
    for article in articles:
        if db.save_article(article):
            saved_count += 1
    
    print(f"\n💾 成功保存 {saved_count}/{len(articles)} 条数据到数据库")
    return articles

def test_hackernews_to_database():
    """测试Hacker News数据存入数据库"""
    print("\n" + "="*60)
    print("测试2: Hacker News数据存入数据库")
    print("="*60)
    
    filename = 'hacker_news.json'
    if not Path(filename).exists():
        print(f"❌ 找不到文件: {filename}")
        return []
    
    print(f"📁 找到文件: {filename}")
    
    with open(filename, 'r', encoding='utf-8') as f:
        hn_data = json.load(f)
    
    print(f"📰 读取到 {len(hn_data)} 条Hacker News数据")
    
    articles = []
    for i, item in enumerate(hn_data[:10]):
        article = Article.from_hacker_news(item)
        # 确保category是字符串
        if hasattr(article.category, 'value'):
            article.category = article.category.value
        articles.append(article)
        print(f"   ✓ {i+1}. {article.title[:50]}...")
    
    # 修改这里：使用 save_article 循环保存
    db = Database()
    saved_count = 0
    for article in articles:
        if db.save_article(article):
            saved_count += 1
    
    print(f"\n💾 成功保存 {saved_count}/{len(articles)} 条数据到数据库")
    return articles

def test_query():
    """测试查询功能"""
    print("\n" + "="*60)
    print("测试3: 查询数据库")
    print("="*60)
    
    db = Database()
    
    # 获取今日文章
    today_articles = db.get_today_articles()
    print(f"📅 今日文章: {len(today_articles)} 条")
    
    # 获取最新文章
    latest = db.get_latest_articles(5)
    print("\n✨ 最新5条:")
    for i, article in enumerate(latest, 1):
        print(f"   {i}. {article.display()}")
    
    # 获取统计信息
    stats = db.get_stats()
    print(f"\n📊 数据库统计:")
    print(f"   总文章数: {stats['total_articles']}")
    print(f"   各数据源: {stats['by_source']}")
    print(f"   今日新增: {stats['today_articles']}")
    
    return stats

if __name__ == "__main__":
    print("🚀 开始测试数据库功能...\n")
    
    github_articles = test_github_to_database()
    hn_articles = test_hackernews_to_database()
    
    if github_articles or hn_articles:
        test_query()
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60)