"""
数据验证模块
"""
import re
from datetime import datetime
from typing import Dict, Optional

class NewsValidator:
    """新闻数据验证器"""
    
    @staticmethod
    def validate_news(news_data: Dict) -> tuple[bool, str]:
        """验证新闻数据"""
        # 检查必需字段
        required_fields = ['title', 'url', 'content']
        for field in required_fields:
            if field not in news_data or not news_data[field]:
                return False, f"缺少必需字段: {field}"
        
        # 验证标题
        title = news_data['title']
        if len(title) < 5 or len(title) > 300:
            return False, f"标题长度无效: {len(title)}"
        
        if NewsValidator._contains_invalid_chars(title):
            return False, "标题包含无效字符"
        
        # 验证URL
        url = news_data['url']
        if not NewsValidator._is_valid_url(url):
            return False, f"URL格式无效: {url}"
        
        # 验证内容
        content = news_data['content']
        if len(content) < 50:
            return False, f"内容太短: {len(content)}字符"
        
        # 验证时间格式
        if 'publish_time' in news_data and news_data['publish_time']:
            if not NewsValidator._is_valid_date(news_data['publish_time']):
                return False, f"发布时间格式无效: {news_data['publish_time']}"
        
        return True, "验证通过"
    
    @staticmethod
    def _contains_invalid_chars(text: str) -> bool:
        """检查是否包含无效字符"""
        invalid_patterns = [
            r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]',  # 控制字符
            r'[<>\"\'&]',  # HTML特殊字符（过多）
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """验证URL格式"""
        url_patterns = [
            r'^https?://',  # 以http/https开头
            r'\.(shtml|html|htm)$',  # 常见的新闻后缀
        ]
        
        # 必须包含至少一个模式
        for pattern in url_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def _is_valid_date(date_str: str) -> bool:
        """验证日期格式"""
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$',  # YYYY-MM-DD HH:MM:SS
            r'^\d{4}年\d{1,2}月\d{1,2}日$',  # 中文日期
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, date_str):
                return True
        
        return False