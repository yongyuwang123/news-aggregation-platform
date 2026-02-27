# app.py
"""
TechPulse AI - Web展示
最简单的Flask应用，显示数据库中的文章
"""

from flask import Flask, render_template_string
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from src.storage.database import Database

app = Flask(__name__)
db = Database()

# HTML模板（最简单的内嵌模板）
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>TechPulse AI · 技术早报</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="300">  <!-- 每5分钟自动刷新 -->
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        
        .stats {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }
        
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            flex: 1;
            min-width: 150px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            color: #666;
            margin-top: 0.5rem;
        }
        
        .section {
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        
        .section-title {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .section-title h2 {
            font-size: 1.5rem;
            color: #333;
        }
        
        .github-icon { color: #333; }
        .hn-icon { color: #ff6600; }
        
        .article-list {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .article-item {
            padding: 1rem;
            border: 1px solid #f0f0f0;
            border-radius: 8px;
            transition: all 0.2s;
        }
        
        .article-item:hover {
            border-color: #667eea;
            box-shadow: 0 2px 10px rgba(102,126,234,0.1);
        }
        
        .article-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .article-title a {
            color: #333;
            text-decoration: none;
        }
        
        .article-title a:hover {
            color: #667eea;
        }
        
        .article-meta {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0.5rem;
        }
        
        .article-meta span {
            display: flex;
            align-items: center;
            gap: 0.3rem;
        }
        
        .article-description {
            color: #666;
            font-size: 0.95rem;
            margin-top: 0.5rem;
            padding-top: 0.5rem;
            border-top: 1px dashed #f0f0f0;
        }
        
        .badge {
            background: #f0f0f0;
            padding: 0.2rem 0.6rem;
            border-radius: 15px;
            font-size: 0.8rem;
            color: #666;
        }
        
        .github-badge {
            background: #e6e6ff;
            color: #333;
        }
        
        .footer {
            text-align: center;
            padding: 2rem;
            color: #666;
            font-size: 0.9rem;
        }
        
        @media (max-width: 768px) {
            .header h1 { font-size: 2rem; }
            .stats { flex-direction: column; }
            .stat-card { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 TechPulse AI</h1>
        <p>每日技术趋势 · GitHub Trending + Hacker News</p>
        <p style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.8;">
            🕒 最后更新: {{ latest_fetch }}
        </p>
    </div>
    
    <div class="container">
        <!-- 统计卡片 -->
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_articles }}</div>
                <div class="stat-label">总文章数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.by_source.get('github_trending', 0) }}</div>
                <div class="stat-label">GitHub 项目</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.by_source.get('hacker_news', 0) }}</div>
                <div class="stat-label">Hacker News</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.today_articles }}</div>
                <div class="stat-label">今日新增</div>
            </div>
        </div>
        
        <!-- GitHub Trending 部分 -->
        <div class="section">
            <div class="section-title">
                <span class="github-icon">📦</span>
                <h2>GitHub Trending · 今日热门</h2>
            </div>
            <div class="article-list">
                {% for article in github_articles %}
                <div class="article-item">
                    <div class="article-title">
                        <a href="{{ article.url }}" target="_blank">{{ article.title }}</a>
                    </div>
                    <div class="article-meta">
                        <span>⭐ {{ article.score }} stars</span>
                        <span>🍴 {{ article.comments }} forks</span>
                        {% if article.tags %}
                        <span class="badge">{{ article.tags[0] }}</span>
                        {% endif %}
                        <span>👤 {{ article.author }}</span>
                    </div>
                    <div class="article-description">
                        {{ article.description[:150] }}{% if article.description|length > 150 %}...{% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <!-- Hacker News 部分 -->
        <div class="section">
            <div class="section-title">
                <span class="hn-icon">📰</span>
                <h2>Hacker News · 热门讨论</h2>
            </div>
            <div class="article-list">
                {% for article in hn_articles %}
                <div class="article-item">
                    <div class="article-title">
                        <a href="{{ article.url }}" target="_blank">{{ article.title }}</a>
                    </div>
                    <div class="article-meta">
                        <span>⭐ {{ article.score }} points</span>
                        <span>💬 {{ article.comments }} comments</span>
                        <span>👤 {{ article.author }}</span>
                        <span>🕒 {{ article.published_at[:10] }}</span>
                    </div>
                    {% if article.description %}
                    <div class="article-description">
                        {{ article.description[:150] }}{% if article.description|length > 150 %}...{% endif %}
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>TechPulse AI · 数据每4小时更新 · {{ now }}</p>
        <p style="margin-top: 0.5rem; font-size: 0.8rem;">⚡ 一个项目学完Python全栈 · 寒假学习计划</p>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    """首页：显示GitHub和Hacker News文章"""
    
    # 获取最新文章
    all_articles = db.get_latest_articles(50)
    
    # 按来源分类
    github_articles = [a for a in all_articles if a.source == 'github_trending'][:15]
    hn_articles = [a for a in all_articles if a.source == 'hacker_news'][:15]
    
    # 获取统计信息
    stats = db.get_stats()
    
    # 获取最新的抓取时间
    latest_fetch = "暂无数据"
    if all_articles:
        # 取所有文章中最近的时间
        fetch_times = [a.fetched_at for a in all_articles if a.fetched_at]
        if fetch_times:
            latest_fetch = max(fetch_times)
    
    # 获取当前时间
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 确保所有变量都传递给模板
    return render_template_string(
        HTML_TEMPLATE,
        github_articles=github_articles,
        hn_articles=hn_articles,
        stats=stats,
        now=now,
        latest_fetch=latest_fetch  # ✅ 确保这一行存在
    )

@app.route('/refresh')
def refresh():
    """手动刷新数据（后续实现）"""
    return "刷新功能待实现"

if __name__ == '__main__':
    print("="*60)
    print("🚀 TechPulse AI Web 服务启动")
    print("="*60)
    print("🌐 访问地址: http://localhost:5000")
    print("📊 数据库: data/techpulse.db")
    print("="*60)
    print("按 Ctrl+C 停止服务")
    print("="*60)
    
    # 启动Flask应用
    app.run(debug=True, host='0.0.0.0', port=5000)