#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库测试脚本
"""
import sqlite3
import json
import os
import sys

def print_table_structure(db_path="data/news.db"):
    """打印表结构"""
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # 返回字典格式
    cursor = conn.cursor()
    
    print("=" * 60)
    print("📊 数据库分析")
    print("=" * 60)
    
    # 查看所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"数据库表 ({len(tables)}个):")
    for table in tables:
        table_name = table['name']
        print(f"\n📁 {table_name}:")
        
        # 查看表结构
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        for col in columns:
            not_null = "NOT NULL" if col['notnull'] else ""
            pk = "PRIMARY KEY" if col['pk'] else ""
            print(f"  {col['name']:20} {col['type']:15} {not_null} {pk}")
        
        # 查看记录数
        cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        count = cursor.fetchone()['count']
        print(f"  记录数: {count}")
    
    print("\n" + "=" * 60)
    print("📰 新闻数据统计")
    print("=" * 60)
    
    # 新闻表统计
    if 'news' in [t['name'] for t in tables]:
        # 总新闻数
        cursor.execute("SELECT COUNT(*) as total FROM news")
        total = cursor.fetchone()['total']
        print(f"总新闻数: {total}")
        
        # 按分类统计
        cursor.execute('''
        SELECT category, COUNT(*) as count 
        FROM news 
        GROUP BY category 
        ORDER BY count DESC
        ''')
        categories = cursor.fetchall()
        
        print("\n📊 分类统计:")
        for cat in categories:
            print(f"  {cat['category']:10}: {cat['count']:4} 篇")
        
        # 最新5条新闻
        print("\n🔥 最新5条新闻:")
        cursor.execute('''
        SELECT id, title, category, publish_time, content_length, crawl_time
        FROM news 
        ORDER BY id DESC 
        LIMIT 5
        ''')
        latest = cursor.fetchall()
        
        for i, news in enumerate(latest, 1):
            title_short = news['title'][:40] + "..." if len(news['title']) > 40 else news['title']
            print(f"{i}. [{news['category']}] {title_short}")
            print(f"   时间: {news['publish_time']} | 长度: {news['content_length']}字")
            print(f"   爬取: {news['crawl_time']}")
            print()
        
        # 内容长度分布
        print("📝 内容长度分布:")
        cursor.execute('''
        SELECT 
            CASE 
                WHEN content_length < 100 THEN '超短(<100)'
                WHEN content_length < 300 THEN '短(100-300)'
                WHEN content_length < 800 THEN '中(300-800)'
                WHEN content_length < 1500 THEN '长(800-1500)'
                ELSE '超长(1500+)'
            END as length_range,
            COUNT(*) as count
        FROM news 
        GROUP BY length_range
        ORDER BY 
            CASE length_range
                WHEN '超短(<100)' THEN 1
                WHEN '短(100-300)' THEN 2
                WHEN '中(300-800)' THEN 3
                WHEN '长(800-1500)' THEN 4
                ELSE 5
            END
        ''')
        length_stats = cursor.fetchall()
        
        for stat in length_stats:
            print(f"  {stat['length_range']:15}: {stat['count']:4} 篇")
    
    # 爬取日志统计
    if 'crawl_log' in [t['name'] for t in tables]:
        print("\n📋 爬取日志统计:")
        cursor.execute("SELECT COUNT(*) as total FROM crawl_log")
        total_logs = cursor.fetchone()['total']
        print(f"总爬取记录: {total_logs}")
        
        cursor.execute("SELECT success, COUNT(*) as count FROM crawl_log GROUP BY success")
        success_stats = cursor.fetchall()
        
        for stat in success_stats:
            status = "成功" if stat['success'] else "失败"
            print(f"  {status}: {stat['count']} 次")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ 数据库分析完成")
    print("=" * 60)

def export_sample_news(db_path="data/news.db", limit=3):
    """导出样本新闻数据"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM news 
    ORDER BY id DESC 
    LIMIT ?
    ''', (limit,))
    
    sample_news = cursor.fetchall()
    
    print(f"\n📄 样本新闻数据 (共{len(sample_news)}条):")
    print("=" * 60)
    
    for i, news in enumerate(sample_news, 1):
        print(f"\n【样本 {i}】")
        print(f"标题: {news['title']}")
        print(f"分类: {news['category']}")
        print(f"来源: {news['source']}")
        print(f"发布时间: {news['publish_time']}")
        print(f"爬取时间: {news['crawl_time']}")
        print(f"内容长度: {news['content_length']}字")
        print(f"URL: {news['url']}")
        
        # 解析关键词
        if news['keywords']:
            try:
                keywords = json.loads(news['keywords'])
                print(f"关键词: {', '.join(keywords)}")
            except:
                pass
        
        # 显示内容预览
        if news['content']:
            content_preview = news['content'][:200] + "..." if len(news['content']) > 200 else news['content']
            print(f"内容预览: {content_preview}")
        
        print("-" * 40)
    
    conn.close()

if __name__ == "__main__":
    # 检查数据库文件
    db_path = "data/news.db"
    
    if os.path.exists(db_path):
        print_table_structure(db_path)
        print("\n" + "=" * 60)
        print("📋 导出样本数据")
        print("=" * 60)
        export_sample_news(db_path, limit=2)
    else:
        print(f"❌ 数据库文件不存在: {db_path}")
        print("请先运行爬虫创建数据库")