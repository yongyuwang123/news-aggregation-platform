"""数据源模块 - 支持多种数据源的插件化架构"""

from .base_source import DataSource
from typing import Dict, List, Any, Type, Optional
import logging

logger = logging.getLogger(__name__)

class DataSourceManager:
    """数据源管理器"""
    
    def __init__(self):
        self.sources: Dict[str, DataSource] = {}
        self.available_types: Dict[str, Type[DataSource]] = {}
        self.logger = logging.getLogger(__name__)  # 添加这一行
        
    def register_source_type(self, name: str, source_class: Type[DataSource]):
        """注册数据源类型"""
        self.available_types[name] = source_class
        self.logger.info(f"注册数据源类型: {name}")
    
    def create_source(self, name: str, source_type: str, config: Dict[str, Any]) -> DataSource:
        """创建数据源实例"""
        if source_type not in self.available_types:
            raise ValueError(f"未知的数据源类型: {source_type}")
        
        source_class = self.available_types[source_type]
        source = source_class(name, config)
        self.sources[name] = source
        self.logger.info(f"创建数据源: {name} ({source_type})")
        return source
    
    def get_source(self, name: str) -> Optional[DataSource]:
        """获取数据源实例"""
        return self.sources.get(name)
    
    def list_sources(self) -> List[Dict[str, Any]]:
        """列出所有数据源信息"""
        return [source.get_info() for source in self.sources.values()]
    
    def run_source(self, name: str, **kwargs) -> List[Dict[str, Any]]:
        """运行指定数据源"""
        source = self.get_source(name)
        if not source:
            raise ValueError(f"数据源不存在: {name}")
        
        if not source.config.get('enabled', True):
            self.logger.warning(f"数据源 {name} 已禁用，跳过执行")
            return []
        
        try:
            self.logger.info(f"开始执行数据源: {name}")
            data = source.fetch_data(**kwargs)
            source.update_stats(success=True, count=len(data))
            self.logger.info(f"数据源 {name} 执行成功，获取 {len(data)} 条数据")
            return data
        except Exception as e:
            source.update_stats(success=False, error=str(e))
            self.logger.error(f"数据源 {name} 执行失败: {e}")
            raise

# 创建全局管理器实例
data_source_manager = DataSourceManager()

# 注册可用的数据源类型（在文件末尾）
from .sina_news_source import SinaNewsDataSource
from .github_trending import GitHubTrendingDataSource
from .rss_source import RSSDataSource

data_source_manager.register_source_type('rss', RSSDataSource)
data_source_manager.register_source_type('sina_news', SinaNewsDataSource)
data_source_manager.register_source_type('github_trending', GitHubTrendingDataSource)

__all__ = ['DataSource', 'DataSourceManager', 'data_source_manager', 
           'SinaNewsDataSource', 'GitHubTrendingDataSource']