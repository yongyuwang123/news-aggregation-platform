"""
数据库操作模块
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json

class NewsDatabase:
    """新闻数据库管理"""
    
    def __init__(self, db_path: str = "database/data/news.db"):  # 更新默认路径
        self.db_path = db_path
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            # 确保目录存在
            import os
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # 返回字典格式
            
            # 创建新闻表
            self._create_tables()
            
            logging.info(f"数据库初始化成功: {self.db_path}")
            
        except Exception as e:
            logging.error(f"数据库初始化失败: {e}")
            raise
    
    def _create_tables(self):
        """创建数据表"""
        cursor = self.conn.cursor()
        
        # 新闻表（移除内联索引定义）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            summary TEXT,
            category TEXT,
            publish_time TEXT,
            source TEXT,
            url TEXT UNIQUE NOT NULL,
            keywords TEXT,  -- JSON格式存储
            content_length INTEGER DEFAULT 0,
            crawl_time TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 爬取日志表（移除内联索引定义）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawl_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            url TEXT NOT NULL,
            crawl_time TEXT NOT NULL,
            success BOOLEAN DEFAULT 1,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 重复新闻检测表（移除内联索引定义）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS duplicate_check (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title_hash TEXT UNIQUE NOT NULL,  -- 标题的哈希值
            url TEXT NOT NULL,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 单独创建索引（SQLite语法）
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_news_category ON news(category)",
            "CREATE INDEX IF NOT EXISTS idx_news_publish_time ON news(publish_time)",
            "CREATE INDEX IF NOT EXISTS idx_news_crawl_time ON news(crawl_time)",
            "CREATE INDEX IF NOT EXISTS idx_news_url ON news(url)",
            "CREATE INDEX IF NOT EXISTS idx_crawl_log_category_time ON crawl_log(category, crawl_time)",
            "CREATE INDEX IF NOT EXISTS idx_duplicate_check_title_hash ON duplicate_check(title_hash)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                logging.warning(f"创建索引失败 {index_sql}: {e}")
        
        self.conn.commit()
    
    def save_news(self, news_data: Dict[str, any]) -> bool:
        """保存新闻数据"""
        try:
            cursor = self.conn.cursor()
            
            # 检查是否已存在（通过URL）
            cursor.execute("SELECT id FROM news WHERE url = ?", (news_data['url'],))
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有记录
                sql = '''
                UPDATE news SET 
                    title = ?, content = ?, summary = ?, category = ?,
                    publish_time = ?, source = ?, keywords = ?,
                    content_length = ?, crawl_time = ?
                WHERE url = ?
                '''
                params = (
                    news_data['title'],
                    news_data.get('content', ''),
                    news_data.get('summary', ''),
                    news_data.get('category', '未知'),
                    news_data.get('publish_time', ''),
                    news_data.get('source', '未知'),
                    json.dumps(news_data.get('keywords', []), ensure_ascii=False),
                    news_data.get('content_length', 0),
                    news_data['crawl_time'],
                    news_data['url']
                )
            else:
                # 插入新记录
                sql = '''
                INSERT INTO news 
                (title, content, summary, category, publish_time, source, url, keywords, content_length, crawl_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''
                params = (
                    news_data['title'],
                    news_data.get('content', ''),
                    news_data.get('summary', ''),
                    news_data.get('category', '未知'),
                    news_data.get('publish_time', ''),
                    news_data.get('source', '未知'),
                    news_data['url'],
                    json.dumps(news_data.get('keywords', []), ensure_ascii=False),
                    news_data.get('content_length', 0),
                    news_data['crawl_time']
                )
            
            cursor.execute(sql, params)
            self.conn.commit()
            
            # 记录爬取日志
            self._log_crawl(news_data['url'], news_data.get('category', '未知'), True)
            
            # 记录标题哈希用于去重
            self._record_title_hash(news_data['title'], news_data['url'])
            
            return True
            
        except Exception as e:
            logging.error(f"保存新闻数据失败 {news_data['url']}: {e}")
            self._log_crawl(news_data['url'], news_data.get('category', '未知'), False, str(e))
            return False
    
    def _log_crawl(self, url: str, category: str, success: bool, error_message: str = None):
        """记录爬取日志"""
        try:
            cursor = self.conn.cursor()
            sql = '''
            INSERT INTO crawl_log (category, url, crawl_time, success, error_message)
            VALUES (?, ?, ?, ?, ?)
            '''
            cursor.execute(sql, (
                category,
                url,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                success,
                error_message
            ))
            self.conn.commit()
        except Exception as e:
            logging.error(f"记录爬取日志失败: {e}")
    
    def _record_title_hash(self, title: str, url: str):
        """记录标题哈希用于去重"""
        try:
            import hashlib
            title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()
            
            cursor = self.conn.cursor()
            sql = '''
            INSERT OR IGNORE INTO duplicate_check (title_hash, url)
            VALUES (?, ?)
            '''
            cursor.execute(sql, (title_hash, url))
            self.conn.commit()
        except Exception as e:
            logging.debug(f"记录标题哈希失败: {e}")
    
    def is_duplicate_title(self, title: str) -> bool:
        """检查标题是否重复"""
        try:
            import hashlib
            title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()
            
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM duplicate_check WHERE title_hash = ?", (title_hash,))
            return cursor.fetchone() is not None
        except Exception as e:
            logging.error(f"检查标题重复失败: {e}")
            return False
    
    def get_recent_news(self, category: str = None, hours: int = 24, limit: int = 100) -> List[Dict]:
        """获取最近N小时内的新闻"""
        try:
            cursor = self.conn.cursor()
            
            time_threshold = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
            
            if category:
                sql = '''
                SELECT * FROM news 
                WHERE category = ? AND crawl_time >= ?
                ORDER BY crawl_time DESC 
                LIMIT ?
                '''
                cursor.execute(sql, (category, time_threshold, limit))
            else:
                sql = '''
                SELECT * FROM news 
                WHERE crawl_time >= ?
                ORDER BY crawl_time DESC 
                LIMIT ?
                '''
                cursor.execute(sql, (time_threshold, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logging.error(f"获取最近新闻失败: {e}")
            return []
    
    def get_news_count(self, category: str = None) -> Dict[str, int]:
        """获取新闻数量统计"""
        try:
            cursor = self.conn.cursor()
            
            if category:
                cursor.execute("SELECT COUNT(*) as count FROM news WHERE category = ?", (category,))
                total = cursor.fetchone()['count']
                
                cursor.execute('''
                SELECT category, COUNT(*) as count 
                FROM news 
                WHERE category = ?
                GROUP BY category
                ''', (category,))
            else:
                cursor.execute("SELECT COUNT(*) as count FROM news")
                total = cursor.fetchone()['count']
                
                cursor.execute('''
                SELECT category, COUNT(*) as count 
                FROM news 
                GROUP BY category
                ''')
            
            rows = cursor.fetchall()
            category_counts = {row['category']: row['count'] for row in rows}
            
            return {
                'total': total,
                'by_category': category_counts
            }
            
        except Exception as e:
            logging.error(f"获取新闻统计失败: {e}")
            return {'total': 0, 'by_category': {}}
    
    def get_latest_crawl_time(self, category: str) -> Optional[str]:
        """获取指定分类最近一次爬取时间"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT crawl_time FROM crawl_log 
            WHERE category = ? AND success = 1 
            ORDER BY crawl_time DESC 
            LIMIT 1
            ''', (category,))
            
            row = cursor.fetchone()
            return row['crawl_time'] if row else None
            
        except Exception as e:
            logging.error(f"获取最近爬取时间失败: {e}")
            return None
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()