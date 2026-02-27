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
                    extra TEXT,  -- JSON格式存储
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source, source_id)  -- 避免重复
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON articles(source)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_fetched_at ON articles(fetched_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_score ON articles(score DESC)')
            
            conn.commit()
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def save_article(self, article: Article) -> bool:
        """保存单篇文章"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 转换tags和extra为JSON
                tags_json = json.dumps(article.tags, ensure_ascii=False)
                extra_json = json.dumps(article.extra, ensure_ascii=False)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO articles 
                    (source, source_id, title, url, description, category, 
                     tags, score, comments, author, published_at, fetched_at, extra)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article.source,
                    article.source_id,
                    article.title,
                    article.url,
                    article.description,
                    article.category,
                    tags_json,
                    article.score,
                    article.comments,
                    article.author,
                    article.published_at,
                    article.fetched_at,
                    extra_json
                ))
                
                return True
                
        except Exception as e:
            print(f"❌ 保存文章失败: {e}")
            return False
    
    def save_article(self, article: Article) -> bool:
        """保存单篇文章"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
            
                # 重要：将文章转换为字典，并确保category是字符串
                article_dict = article.to_dict()
            
                # 转换tags和extra为JSON
                tags_json = json.dumps(article_dict.get('tags', []), ensure_ascii=False)
                extra_json = json.dumps(article_dict.get('extra', {}), ensure_ascii=False)
            
                # 确保category是字符串
                category_value = article_dict.get('category', 'technology')
                if hasattr(category_value, 'value'):  # 如果还是枚举，取value
                    category_value = category_value.value
            
                cursor.execute('''
                    INSERT OR REPLACE INTO articles 
                    (source, source_id, title, url, description, category, 
                     tags, score, comments, author, published_at, fetched_at, extra)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article_dict.get('source', ''),
                    article_dict.get('source_id', ''),
                    article_dict.get('title', ''),
                    article_dict.get('url', ''),
                    article_dict.get('description', ''),
                    category_value,  # 使用处理后的category
                    tags_json,
                    article_dict.get('score', 0),
                    article_dict.get('comments', 0),
                    article_dict.get('author', ''),
                    article_dict.get('published_at'),
                    article_dict.get('fetched_at'),
                    extra_json
                ))
            
                return True
            
        except Exception as e:
            print(f"❌ 保存文章失败: {e}")
            return False
    
    def get_today_articles(self, source: Optional[str] = None) -> List[Article]:
        """获取今天的文章"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if source:
                cursor.execute('''
                    SELECT * FROM articles 
                    WHERE date(fetched_at) = ? AND source = ?
                    ORDER BY score DESC
                ''', (today, source))
            else:
                cursor.execute('''
                    SELECT * FROM articles 
                    WHERE date(fetched_at) = ?
                    ORDER BY source, score DESC
                ''', (today,))
            
            return self._cursor_to_articles(cursor)
    
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
        """将数据库游标结果转换为Article列表"""
        articles = []
        
        # 获取列名
        columns = [description[0] for description in cursor.description]
        
        for row in cursor.fetchall():
            # 将行转换为字典
            row_dict = dict(zip(columns, row))
            
            # 解析JSON字段
            row_dict['tags'] = json.loads(row_dict['tags']) if row_dict['tags'] else []
            row_dict['extra'] = json.loads(row_dict['extra']) if row_dict['extra'] else {}
            
            # 创建Article对象
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
            
            return {
                'total_articles': total,
                'by_source': sources,
                'today_articles': today_count,
                'database_path': self.db_path
            }
    
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