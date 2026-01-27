"""
配置加载模块
"""
import os
import yaml
from typing import Dict, Any
import logging

class Config:
    """配置管理类"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_path):
                # 创建默认配置
                default_config = self._get_default_config()
                self._save_config(default_config)
                return default_config
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # 合并默认配置（确保新字段有值）
            default_config = self._get_default_config()
            config = self._merge_configs(default_config, config)
            
            logging.info(f"配置加载成功: {self.config_path}")
            return config
            
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'crawler': {
                'base_url': 'https://news.sina.com.cn/',
                'timeout': 10,
                'max_retries': 3,
                'delay_range': [1, 3],
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            'categories': {
                'enabled': True,
                'list': [
                    {'name': '首页', 'url': 'https://news.sina.com.cn/', 'max_news': 10},
                    {'name': '国内', 'url': 'https://news.sina.com.cn/china/', 'max_news': 15},
                ]
            },
            'database': {
                'type': 'sqlite',
                'path': 'database/data/news.db'  # 更新默认路径
            },
            'output': {
                'save_to_database': True,
                'save_json': True,
                'save_csv': True,
                'output_dir': 'database/data'  # 更新输出目录
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/crawler.log'
            },
            'incremental': {
                'enabled': True,
                'update_hours': 24
            }
        }
    
    def _merge_configs(self, default: Dict, custom: Dict) -> Dict:
        """合并配置（深度合并）"""
        for key, value in default.items():
            if key not in custom:
                custom[key] = value
            elif isinstance(value, dict) and isinstance(custom[key], dict):
                custom[key] = self._merge_configs(value, custom[key])
        return custom
    
    def _save_config(self, config: Dict[str, Any]):
        """保存配置到文件"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default=None) -> Any:
        """获取配置项"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def update(self, key: str, value: Any):
        """更新配置项"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self._save_config(self.config)

# 全局配置实例
config = Config()