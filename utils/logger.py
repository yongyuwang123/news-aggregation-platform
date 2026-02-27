# src/utils/logger.py
import logging
import logging.config
import yaml
import os
from pathlib import Path

def setup_logging(
    config_path: str = "config/logging.yaml",
    default_level: int = logging.INFO,
    logs_dir: str = "logs"
):
    """设置日志配置"""
    
    # 创建日志目录
    Path(logs_dir).mkdir(exist_ok=True)
    
    config_file = Path(config_path)
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            logging.config.dictConfig(config)
            logging.info(f"日志配置已从 {config_path} 加载")
            
        except Exception as e:
            logging.basicConfig(level=default_level)
            logging.warning(f"加载日志配置文件失败，使用基础配置: {e}")
    else:
        # 基础配置
        logging.basicConfig(
            level=default_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        logging.info("使用基础日志配置")

class LoggerMixin:
    """为类提供logger的混入类"""
    
    @property
    def logger(self):
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger