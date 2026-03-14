# app.py
"""
TechPulse AI - Web展示
最简单的Flask应用，显示数据库中的文章
"""
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template_string
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from src.storage.database import Database
from src.analyzers.ai_analyzer import AIAnalyzer

app = Flask(__name__)
db = Database()

# AI分析路由
@app.route('/analyze/<int:article_id>', methods=['POST'])
def analyze_article(article_id):
    """对单篇文章生成AI摘要"""
    try:
        # 获取文章
        all_articles = db.get_latest_articles(100)
        article = next((a for a in all_articles if hasattr(a, 'id') and a.id == article_id), None)
        
        if not article:
            return {"error": "文章不存在"}, 404
        
        # 检查是否已有AI摘要
        if hasattr(article, 'ai_summary') and article.ai_summary:
            return {"summary": article.ai_summary, "cached": True}
        
        # 调用AI分析器
        analyzer = AIAnalyzer()
        summary = analyzer.summarize_article(article)
        
        # 保存摘要到数据库
        article.ai_summary = summary
        article.ai_analyzed_at = datetime.now().isoformat()
        db.save_article(article)
        
        return {"summary": summary, "cached": False}
        
    except Exception as e:
        print(f"AI分析失败: {e}")
        return {"error": "AI分析失败，请检查API配置"}, 500

@app.route('/daily')
def daily_report():
    """显示今日趋势报告"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        report = db.get_report_by_date(today)
        
        if not report:
            return "今日报告尚未生成，请等待定时任务运行或手动触发。"
        
        # 创建报告模板
        REPORT_TEMPLATE = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>TechPulse AI - 每日趋势报告</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; }
                .summary { background: #f0f8ff; padding: 20px; border-radius: 8px; margin-bottom: 30px; line-height: 1.6; }
                .recommendations { margin-top: 20px; }
                .recommendation { background: #f9f9f9; padding: 15px; margin: 10px 0; border-left: 4px solid #4a90e2; border-radius: 4px; }
                .nav { text-align: center; margin-top: 30px; }
                .nav a { color: #4a90e2; text-decoration: none; margin: 0 10px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 TechPulse AI 每日趋势报告</h1>
                    <p>报告日期: {{ today }}</p>
                </div>
                
                <div class="summary">
                    <h2>📊 今日技术趋势总结</h2>
                    <p>{{ summary }}</p>
                </div>
                
                {% if recommendations %}
                <div class="recommendations">
                    <h2>⭐ 今日推荐阅读</h2>
                    {% for rec in recommendations %}
                    <div class="recommendation">
                        <h3>{{ rec.title }}</h3>
                        <p>{{ rec.reason }}</p>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                <div class="nav">
                    <a href="/">← 返回首页</a>
                    <a href="/reports">📚 历史报告</a>
                    <a href="#" onclick="location.reload()">🔄 刷新报告</a>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return render_template_string(REPORT_TEMPLATE, 
                                    summary=report['summary'], 
                                    recommendations=report['recommendations'],
                                    today=today)
        
    except Exception as e:
        print(f"获取报告失败: {e}")
        return f"获取报告失败: {e}"

@app.route('/reports')
def reports_list():
    """显示历史报告列表"""
    try:
        reports = db.get_daily_reports(limit=30)
        
        REPORTS_TEMPLATE = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>TechPulse AI - 历史报告</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; }
                .report-item { background: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #4a90e2; }
                .report-date { font-weight: bold; color: #333; }
                .report-summary { color: #666; margin-top: 5px; font-size: 0.9rem; }
                .nav { text-align: center; margin-top: 30px; }
                .nav a { color: #4a90e2; text-decoration: none; margin: 0 10px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📚 TechPulse AI 历史报告</h1>
                    <p>查看过去30天的技术趋势分析报告</p>
                </div>
                
                {% if reports %}
                <div class="reports-list">
                    {% for report in reports %}
                    <div class="report-item">
                        <div class="report-date">
                            <a href="/daily/{{ report.report_date }}">{{ report.report_date }}</a>
                        </div>
                        <div class="report-summary">
                            {{ report.summary[:200] }}{% if report.summary|length > 200 %}...{% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div style="text-align: center; padding: 40px; color: #666;">
                    <p>暂无历史报告，请等待定时任务生成报告。</p>
                </div>
                {% endif %}
                
                <div class="nav">
                    <a href="/">← 返回首页</a>
                    <a href="/daily">📊 今日报告</a>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return render_template_string(REPORTS_TEMPLATE, reports=reports)
        
    except Exception as e:
        print(f"获取报告列表失败: {e}")
        return f"获取报告列表失败: {e}"
@app.route('/daily/<date_str>')
def daily_report_by_date(date_str):
    """显示指定日期的趋势报告"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT summary, recommendations FROM daily_reports WHERE report_date = ?', (date_str,))
            row = cursor.fetchone()
        
        if not row:
            return f"{date_str} 的报告不存在。"
        
        summary = row[0]
        recommendations = json.loads(row[1]) if row[1] else []
        
        # 使用相同的报告模板
        REPORT_TEMPLATE = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>TechPulse AI - 每日趋势报告</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; }
                .summary { background: #f0f8ff; padding: 20px; border-radius: 8px; margin-bottom: 30px; line-height: 1.6; }
                .recommendations { margin-top: 20px; }
                .recommendation { background: #f9f9f9; padding: 15px; margin: 10px 0; border-left: 4px solid #4a90e2; border-radius: 4px; }
                .nav { text-align: center; margin-top: 30px; }
                .nav a { color: #4a90e2; text-decoration: none; margin: 0 10px; }
                .export-buttons { text-align: center; margin: 20px 0; }
                .export-btn { background: #28a745; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin: 0 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 TechPulse AI 每日趋势报告</h1>
                    <p>报告日期: {{ date_str }}</p>
                </div>
                
                <div class="export-buttons">
                    <button class="export-btn" onclick="exportMarkdown()">📄 导出Markdown</button>
                    <button class="export-btn" onclick="exportPDF()">📊 导出PDF</button>
                </div>
                
                <div class="summary">
                    <h2>📊 技术趋势总结</h2>
                    <p>{{ summary }}</p>
                </div>
                
                {% if recommendations %}
                <div class="recommendations">
                    <h2>⭐ 推荐阅读</h2>
                    {% for rec in recommendations %}
                    <div class="recommendation">
                        <h3>{{ rec.title }}</h3>
                        <p>{{ rec.reason }}</p>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                <div class="nav">
                    <a href="/">← 返回首页</a>
                    <a href="/daily">📊 今日报告</a>
                </div>
            </div>
            
            <script>
            function exportMarkdown() {
                const content = `# TechPulse AI 趋势报告\\n\\n**报告日期**: {{ date_str }}\\n\\n## 📊 技术趋势总结\\n\\n{{ summary }}\\n\\n{% if recommendations %}## ⭐ 推荐阅读\\n\\n{% for rec in recommendations %}### {{ rec.title }}\\n\\n{{ rec.reason }}\\n\\n{% endfor %}{% endif %}`;
                
                const blob = new Blob([content], { type: 'text/markdown' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `techpulse-report-{{ date_str }}.md`;
                a.click();
                URL.revokeObjectURL(url);
            }
            
            function exportPDF() {
                alert('PDF导出功能需要后端支持，正在开发中...');
            }
            </script>
        </body>
        </html>
        '''
        
        return render_template_string(REPORT_TEMPLATE, 
                                    summary=summary, 
                                    recommendations=recommendations,
                                    date_str=date_str)
        
    except Exception as e:
        print(f"获取报告失败: {e}")
        return f"获取报告失败: {e}"
@app.route('/api/export/<date_str>/<format>')
def export_report(date_str: str, format: str):
    """导出报告API"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT summary, recommendations FROM daily_reports WHERE report_date = ?', (date_str,))
            row = cursor.fetchone()
        
        if not row:
            return {"error": "报告不存在"}, 404
        
        report = {
            'summary': row[0],
            'recommendations': json.loads(row[1]) if row[1] else []
        }
        
        if format == 'markdown':
            content = f"""# TechPulse AI 趋势报告
**报告日期**: {date_str}
## 📊 技术趋势总结
{report['summary']}
"""
            
            if report['recommendations']:
                content += "## ⭐ 推荐阅读\n\n"
                for rec in report['recommendations']:
                    content += f"### {rec['title']}\n\n{rec['reason']}\n\n"
            
            return content, 200, {
                'Content-Type': 'text/markdown',
                'Content-Disposition': f'attachment; filename="techpulse-report-{date_str}.md"'
            }
        
        elif format == 'json':
            from flask import jsonify
            return jsonify(report), 200, {
                'Content-Type': 'application/json',
                'Content-Disposition': f'attachment; filename="techpulse-report-{date_str}.json"'
            }
        
        else:
            return {"error": "不支持的格式"}, 400
            
    except Exception as e:
        print(f"导出报告失败: {e}")
        return {"error": str(e)}, 500

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
        <div style="margin-top: 0.5rem;">
            <a href="/daily" style="background: #4a90e2; color: white; padding: 0.5rem 1rem; text-decoration: none; border-radius: 5px; font-size: 0.9rem;">
                📊 查看今日趋势报告
            </a>
        </div>
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
                    
                    <!-- AI分析区域 -->
                    <div style="margin-top: 0.5rem;">
                        {% if article.ai_summary %}
                        <div class="ai-summary" style="margin-top: 0.5rem; padding: 0.5rem; background: #f0f4f8; border-radius: 5px; font-size: 0.9rem;">
                            <strong>🤖 AI摘要：</strong>{{ article.ai_summary }}
                        </div>
                        {% else %}
                        <button class="ai-btn" data-id="{{ article.id }}" style="background: #4a90e2; color: white; border: none; padding: 0.3rem 0.8rem; border-radius: 3px; cursor: pointer; font-size: 0.8rem;">
                            🤖 AI分析
                        </button>
                        <div class="ai-summary" id="summary-{{ article.id }}" style="display: none; margin-top: 0.5rem; padding: 0.5rem; background: #f0f4f8; border-radius: 5px; font-size: 0.9rem;"></div>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>TechPulse AI · 数据每4小时更新 · {{ now }}</p>
        <p style="margin-top: 0.5rem; font-size: 0.8rem;">⚡ 一个项目学完Python全栈 · 寒假学习计划</p>
    </div>
    
    <!-- AI分析JavaScript -->
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll('.ai-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const articleId = this.dataset.id;
                const summaryDiv = document.getElementById(`summary-${articleId}`);
                
                // 如果已经加载过，直接显示
                if (summaryDiv.innerHTML.trim() !== '') {
                    summaryDiv.style.display = summaryDiv.style.display === 'block' ? 'none' : 'block';
                    return;
                }
                
                // 否则请求AI分析
                this.disabled = true;
                this.textContent = '分析中...';
                
                fetch(`/analyze/${articleId}`, { method: 'POST' })
                    .then(res => res.json())
                    .then(data => {
                        if (data.summary) {
                            summaryDiv.innerHTML = `<strong>🤖 AI摘要：</strong>${data.summary}`;
                            summaryDiv.style.display = 'block';
                            
                            // 如果是新分析的，重新加载页面显示缓存结果
                            if (!data.cached) {
                                setTimeout(() => {
                                    location.reload();
                                }, 2000);
                            }
                        } else {
                            summaryDiv.innerHTML = '<strong>❌ 分析失败：</strong>' + (data.error || '未知错误');
                            summaryDiv.style.display = 'block';
                        }
                        this.disabled = false;
                        this.textContent = '🤖 AI分析';
                    })
                    .catch(err => {
                        summaryDiv.innerHTML = '<strong>❌ 请求失败：</strong>网络错误';
                        summaryDiv.style.display = 'block';
                        this.disabled = false;
                        this.textContent = '🤖 AI分析';
                    });
            });
        });
    });
    </script>
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