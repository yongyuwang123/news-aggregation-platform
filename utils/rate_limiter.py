#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
请求频率控制模块
"""
import time
import threading
import logging
from typing import Optional, Callable
from datetime import datetime, timedelta

class RateLimiter:
    """简单的请求频率控制器"""
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        初始化频率限制器
        
        Args:
            max_requests: 时间窗口内的最大请求数
            time_window: 时间窗口长度（秒）
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []  # 存储请求时间戳
        self.lock = threading.Lock()  # 线程安全锁
        self.logger = logging.getLogger(__name__)
        
        # 如果没有配置日志处理器，添加一个简单的
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def wait_if_needed(self) -> float:
        """
        如果需要等待，则进行等待并返回等待时间
        
        Returns:
            float: 实际等待的时间（秒）
        """
        with self.lock:
            now = time.time()
            
            # 清理过期的请求记录
            cutoff_time = now - self.time_window
            self.requests = [t for t in self.requests if t > cutoff_time]
            
            # 检查是否超过限制
            if len(self.requests) >= self.max_requests:
                # 计算需要等待的时间
                oldest_request = min(self.requests)
                wait_time = oldest_request + self.time_window - now
                
                if wait_time > 0:
                    self.logger.info(f"频率限制：等待 {wait_time:.2f} 秒")
                    time.sleep(wait_time)
                    
                    # 更新当前时间
                    now = time.time()
                    return wait_time
            
            # 记录当前请求
            self.requests.append(now)
            return 0.0
    
    def get_status(self) -> dict:
        """获取当前频率限制状态"""
        with self.lock:
            now = time.time()
            cutoff_time = now - self.time_window
            recent_requests = [t for t in self.requests if t > cutoff_time]
            
            return {
                'current_requests': len(recent_requests),
                'max_requests': self.max_requests,
                'time_window': self.time_window,
                'remaining': max(0, self.max_requests - len(recent_requests)),
                'reset_in': max(0, (min(recent_requests) + self.time_window - now) if recent_requests else 0)
            }

class AdaptiveRateLimiter(RateLimiter):
    """自适应频率限制器（根据响应状态动态调整）"""
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        super().__init__(max_requests, time_window)
        self.consecutive_errors = 0
        self.error_threshold = 3  # 连续错误阈值
        self.backoff_factor = 2   # 退避因子
    
    def record_error(self):
        """记录错误并触发退避机制"""
        self.consecutive_errors += 1
        
        if self.consecutive_errors >= self.error_threshold:
            # 触发退避：减少请求频率
            new_max_requests = max(1, self.max_requests // self.backoff_factor)
            if new_max_requests != self.max_requests:
                self.logger.warning(f"检测到连续错误，降低频率限制: {self.max_requests} -> {new_max_requests}")
                self.max_requests = new_max_requests
            
            # 增加延迟
            extra_delay = self.consecutive_errors * 2
            self.logger.info(f"错误退避：额外延迟 {extra_delay} 秒")
            time.sleep(extra_delay)
    
    def record_success(self):
        """记录成功并恢复频率限制"""
        if self.consecutive_errors > 0:
            self.consecutive_errors = 0
            # 可以在这里实现恢复逻辑（可选）

def rate_limit(max_requests: int = 10, time_window: int = 60):
    """
    频率限制装饰器
    
    Args:
        max_requests: 时间窗口内的最大请求数
        time_window: 时间窗口长度（秒）
    """
    limiter = RateLimiter(max_requests, time_window)
    
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            wait_time = limiter.wait_if_needed()
            
            # 记录请求开始时间
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # 记录成功
                if hasattr(limiter, 'record_success'):
                    limiter.record_success()
                
                return result
                
            except Exception as e:
                # 记录错误
                if hasattr(limiter, 'record_error'):
                    limiter.record_error()
                raise e
            finally:
                # 记录请求耗时
                duration = time.time() - start_time
                limiter.logger.debug(f"请求耗时: {duration:.2f}s, 等待: {wait_time:.2f}s")
        
        return wrapper
    return decorator

# 全局频率限制器实例
global_limiter = RateLimiter(max_requests=15, time_window=60)

def global_rate_limit():
    """全局频率限制装饰器"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            global_limiter.wait_if_needed()
            return func(*args, **kwargs)
        return wrapper
    return decorator