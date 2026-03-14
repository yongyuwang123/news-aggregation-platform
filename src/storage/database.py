# src/storage/database.py
"""
SQLite数据库模块
存储和管理文章数据
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path

# 导入数据模型
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.core.models import Article

class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = "data/techpulse.db"):
        """初始化数据库连接"""
        # 确保data目录存在
        Path(db_path).parent.mkdir(exist_ok=True)
        
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建文章表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    tags TEXT,  -- JSON格式存储
                    score INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    author TEXT,
                    published_at TEXT,
                    fetched_at TEXT NOT NULL,
                    ai_summary TEXT,           -- AI生成的摘要
                    ai_extra TEXT,             -- JSON格式的额外分析
                    ai_analyzed_at TEXT,        -- AI分析时间
                    extra TEXT,  -- JSON格式存储,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source, source_id)  -- 避免重复
                )
            ''')
            
            # 创建每日报告表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_date TEXT UNIQUE,
                    summary TEXT,
                    recommendations TEXT,  -- JSON格式
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON articles(source)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_fetched_at ON articles(fetched_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_score ON articles(score DESC)')
            
            cursor.execute("PRAGMA table_info(articles)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'ai_summary' not in columns:
                cursor.execute("ALTER TABLE articles ADD COLUMN ai_summary TEXT")
            if 'ai_extra' not in columns:
                cursor.execute("ALTER TABLE articles ADD COLUMN ai_extra TEXT")
            conn.commit()
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def save_article(self, article: Article) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                article_dict = article.to_dict()
                tags_json = json.dumps(article_dict.get('tags', []), ensure_ascii=False)
                extra_json = json.dumps(article_dict.get('extra', {}), ensure_ascii=False)
            
                # 处理 category 为字符串
                category_value = article_dict.get('category', 'technology')
                if hasattr(category_value, 'value'):
                    category_value = category_value.value

                cursor.execute('''
                    INSERT OR REPLACE INTO articles 
                    (source, source_id, title, url, description, category, 
                    tags, score, comments, author, published_at, fetched_at, extra,
                    ai_summary, ai_extra, ai_analyzed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article_dict.get('source', ''),
                    article_dict.get('source_id', ''),
                    article_dict.get('title', ''),
                    article_dict.get('url', ''),
                    article_dict.get('description', ''),
                    category_value,
                    tags_json,
                    article_dict.get('score', 0),
                    article_dict.get('comments', 0),
                    article_dict.get('author', ''),
                    article_dict.get('published_at'),
                    article_dict.get('fetched_at'),
                    extra_json,
                    getattr(article, 'ai_summary', None),
                    json.dumps(getattr(article, 'ai_extra', {})) if hasattr(article, 'ai_extra') else None,
                    getattr(article, 'ai_analyzed_at', None)
                ))
                return True
        except Exception as e:
            print(f"❌ 保存文章失败: {e}")
            return False
    
    
    def get_latest_articles(self, limit: int = 50) -> List[Article]:
        """获取最新文章"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM articles 
                ORDER BY fetched_at DESC, score DESC
                LIMIT ?
            ''', (limit,))
            
            return self._cursor_to_articles(cursor)
    
    def _cursor_to_articles(self, cursor) -> List[Article]:
        articles = []
        columns = [description[0] for description in cursor.description]
    
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
        
            # 解析JSON字段
            row_dict['tags'] = json.loads(row_dict['tags']) if row_dict['tags'] else []
            row_dict['extra'] = json.loads(row_dict['extra']) if row_dict['extra'] else {}
        
            # 创建Article对象（不包含AI字段，稍后手动添加）
            article = Article(
                source=row_dict['source'],
                source_id=row_dict['source_id'],
                title=row_dict['title'],
                url=row_dict['url'],
                description=row_dict['description'] or '',
                category=row_dict['category'] or 'technology',
                tags=row_dict['tags'],
                score=row_dict['score'] or 0,
                comments=row_dict['comments'] or 0,
                author=row_dict['author'] or '',
                published_at=row_dict['published_at'],
                fetched_at=row_dict['fetched_at'],
                extra=row_dict['extra']
            )
        
            # 添加AI分析相关属性
            article.id = row_dict.get('id')
            article.ai_summary = row_dict.get('ai_summary')
            article.ai_analyzed_at = row_dict.get('ai_analyzed_at')
            if row_dict.get('ai_extra'):
                try:
                    article.ai_extra = json.loads(row_dict['ai_extra'])
                except:
                    article.ai_extra = {}
            else:
                article.ai_extra = {}
        
            articles.append(article)
    
        return articles
    
    def get_stats(self) -> Dict:
        """获取数据库统计信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 总文章数
            cursor.execute('SELECT COUNT(*) FROM articles')
            total = cursor.fetchone()[0]
            
            # 各数据源数量
            cursor.execute('''
                SELECT source, COUNT(*) 
                FROM articles 
                GROUP BY source
            ''')
            sources = dict(cursor.fetchall())
            
            # 今日文章数
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('SELECT COUNT(*) FROM articles WHERE date(fetched_at) = ?', (today,))
            today_count = cursor.fetchone()[0]
            
            # 获取最新更新时间
            cursor.execute('SELECT MAX(fetched_at) FROM articles')
            latest_update = cursor.fetchone()[0]
            
            return {
                'total_articles': total,
                'by_source': sources,
                'today_articles': today_count,
                'latest_update': latest_update,
                'database_path': self.db_path
            }
    
    def get_today_articles(self) -> List[Article]:
        """获取今日文章"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取今天的日期（格式：YYYY-MM-DD）
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 查询今天发布的文章
            cursor.execute('''
                SELECT * FROM articles 
                WHERE DATE(published_at) = ? OR DATE(fetched_at) = ?
                ORDER BY published_at DESC
            ''', (today, today))
            
            return self._cursor_to_articles(cursor)
    
    def clear_old_data(self, days: int = 7):
        """清理旧数据（保留最近days天）"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM articles 
                WHERE date(fetched_at) < date('now', ?)
            ''', (f'-{days} days',))
            
            deleted = cursor.rowcount
            conn.commit()
            print(f"🧹 已清理 {deleted} 条旧数据")