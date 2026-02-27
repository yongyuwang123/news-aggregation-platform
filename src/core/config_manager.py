# src/core/config_manager.py
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """配置文件管理器"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if not self.config_path.exists():
            # 使用默认配置
            self.config = self._get_default_config()
            self._save_config()  # 创建配置文件
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        except Exception as e:
            raise ValueError(f"加载配置文件失败: {e}")
    
    def _save_config(self):
        """保存配置文件"""
        self.config_path.parent.mkdir(exist_ok=True, parents=True)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'app': {
                'name': 'TechPulse AI',
                'version': '1.0.0',
                'environment': 'development'
            },
            'data_sources': {
                'enabled': ['hacker_news', 'github_trending'],
                'hacker_news': {
                    'api_url': 'https://hacker-news.firebaseio.com/v0/',
                    'fetch_top_n': 30
                },
                'github_trending': {
                    'languages': ['', 'python'],
                    'since': 'daily',
                    'fetch_limit': 25
                }
            },
            'database': {
                'type': 'sqlite',
                'path': 'data/techpulse.db'
            },
            'storage': {
                'save_to_database': True,
                'save_json': True,
                'save_csv': False,
                'output_dir': 'data/exports'
            }
        }
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self.config
    
    def get_section(self, section_path: str, default: Any = None) -> Any:
        """获取配置部分"""
        keys = section_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def update_config(self, updates: Dict[str, Any]):
        """更新配置"""
        self._merge_dicts(self.config, updates)
        self._save_config()
    
    def _merge_dicts(self, target: Dict, source: Dict):
        """递归合并字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_dicts(target[key], value)
            else:
                target[key] = value