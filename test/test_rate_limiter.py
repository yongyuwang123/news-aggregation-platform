#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
频率控制测试
"""
import os
import sys
import time
import threading

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from utils.rate_limiter import RateLimiter, rate_limit

def test_basic_rate_limiting():
    """测试基础频率限制"""
    limiter = RateLimiter(max_requests=5, time_window=10)  # 10秒内最多5次
    
    print("测试基础频率限制...")
    start_time = time.time()
    
    for i in range(8):  # 超过限制
        wait_time = limiter.wait_if_needed()
        if wait_time > 0:
            print(f"请求 {i+1}: 等待了 {wait_time:.2f} 秒")
        else:
            print(f"请求 {i+1}: 立即执行")
    
    duration = time.time() - start_time
    print(f"总耗时: {duration:.2f} 秒")
    print(f"预期: 应该超过10秒（因为有等待）")

@rate_limit(max_requests=3, time_window=5)
def limited_function(i):
    """被频率限制的函数"""
    print(f"执行函数 {i} 在 {time.time()}")
    return i * 2

def test_decorator():
    """测试装饰器"""
    print("\n测试装饰器频率限制...")
    
    results = []
    for i in range(5):
        result = limited_function(i)
        results.append(result)
    
    return results

if __name__ == "__main__":
    test_basic_rate_limiting()
    test_decorator()