import time
import logging
from functools import wraps
from typing import Callable, Any, Optional

def simple_retry(max_retries: int = 3, delay: float = 1, backoff_factor: float = 1.0):
    """
    简单的重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试延迟时间（秒）
        backoff_factor: 延迟时间倍增因子，1.0表示固定延迟，>1.0表示指数退避
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[Any]:
            current_delay = delay
            for attempt in range(max_retries + 1):  # +1 包括第一次尝试
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:  # 最后一次尝试也失败
                        logging.error(f"函数 {func.__name__} 重试{max_retries}次后失败: {e}")
                        raise
                    logging.warning(f"函数 {func.__name__} 第{attempt+1}次失败，{current_delay}秒后重试: {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor  # 指数退避
            return None
        return wrapper
    return decorator

def retry_on_exception(exceptions: tuple, max_retries: int = 3, delay: float = 1):
    """
    针对特定异常的重试装饰器
    
    Args:
        exceptions: 需要重试的异常类型元组
        max_retries: 最大重试次数
        delay: 重试延迟时间（秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[Any]:
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logging.error(f"函数 {func.__name__} 重试{max_retries}次后失败: {e}")
                        raise
                    logging.warning(f"函数 {func.__name__} 第{attempt+1}次失败，{delay}秒后重试: {e}")
                    time.sleep(delay)
                except Exception as e:
                    # 其他异常直接抛出，不重试
                    logging.error(f"函数 {func.__name__} 遇到非重试异常: {e}")
                    raise
            return None
        return wrapper
    return decorator

# 使用示例
if __name__ == "__main__":
    import requests
    
    # 基本用法
    @simple_retry(max_retries=3, delay=2)
    def fetch_url(url):
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 如果状态码不是200，抛出异常
        return response.text
    
    # 针对网络异常的重试
    @retry_on_exception((requests.RequestException,), max_retries=3, delay=2)
    def fetch_url_safe(url):
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    
    # 指数退避重试
    @simple_retry(max_retries=3, delay=1, backoff_factor=2.0)
    def fetch_with_backoff(url):
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text