# src/data_sources/base_source.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
from ..core.models import Article

class DataSource(ABC):
    """数据源抽象基类"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"DataSource.{name}")
        self.logger.info(f"初始化数据源: {name}")
        
        # 状态跟踪
        self.last_fetch_time: Optional[datetime] = None
        self.fetch_count = 0
        self.error_count = 0
    
    @abstractmethod
    def fetch_articles(self, limit: int = 50) -> List[Article]:
        """获取文章列表 - 子类必须实现"""
        pass
    
    @abstractmethod
    def get_article_detail(self, article_id: str) -> Optional[Article]:
        """获取文章详情 - 子类必须实现"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """获取数据源状态"""
        return {
            'name': self.name,
            'last_fetch_time': self.last_fetch_time,
            'fetch_count': self.fetch_count,
            'error_count': self.error_count,
            'is_healthy': self.error_count < 5  # 简单健康检查
        }
    
    def validate_config(self) -> bool:
        """验证配置是否有效"""
        required_keys = self.get_required_config_keys()
        for key in required_keys:
            if key not in self.config:
                self.logger.error(f"缺少必要配置项: {key}")
                return False
        return True
    
    @classmethod
    @abstractmethod
    def get_required_config_keys(cls) -> List[str]:
        """返回必需的配置键列表"""
        pass
    
    def update_fetch_stats(self, success: bool = True):
        """更新抓取统计"""
        self.last_fetch_time = datetime.now()
        self.fetch_count += 1
        if not success:
            self.error_count += 1
            self.logger.error(f"数据源 {self.name} 抓取失败")