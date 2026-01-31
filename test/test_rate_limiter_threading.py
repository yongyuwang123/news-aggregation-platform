#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多线程频率控制测试 - 验证线程安全性
"""
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from utils.rate_limiter import RateLimiter, rate_limit

class ThreadSafeTest:
    """多线程安全性测试类"""
    
    def __init__(self):
        # 共享的频率限制器
        self.limiter = RateLimiter(max_requests=10, time_window=5)  # 5秒内最多10次
        self.results = []
        self.lock = threading.Lock()
        self.request_count = 0
        self.success_count = 0
        self.wait_time_total = 0.0

    def worker_thread(self, thread_id, num_requests):
        """工作线程函数"""
        thread_results = []
        
        for i in range(num_requests):
            start_time = time.time()
            
            # 应用频率限制
            wait_time = self.limiter.wait_if_needed()
            
            # 模拟请求处理
            process_time = time.time() - start_time
            
            with self.lock:
                self.request_count += 1
                self.wait_time_total += wait_time
                if wait_time == 0:
                    self.success_count += 1
            
            result = {
                'thread_id': thread_id,
                'request_id': i,
                'wait_time': wait_time,
                'process_time': process_time,
                'timestamp': time.time()
            }
            thread_results.append(result)
            
            # 短暂延迟，模拟实际工作
            time.sleep(0.01)
        
        return thread_results

def test_thread_safety():
    """测试线程安全性"""
    print("=" * 50)
    print("多线程频率限制器线程安全性测试")
    print("=" * 50)
    
    test = ThreadSafeTest()
    num_threads = 5
    requests_per_thread = 8  # 总共40次请求，超过限制10次/5秒
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # 提交所有任务
        futures = [
            executor.submit(test.worker_thread, i, requests_per_thread)
            for i in range(num_threads)
        ]
        
        # 收集结果
        all_results = []
        for future in futures:
            all_results.extend(future.result())
    
    total_time = time.time() - start_time
    
    # 分析结果
    print(f"\n测试结果:")
    print(f"线程数: {num_threads}")
    print(f"每线程请求数: {requests_per_thread}")
    print(f"总请求数: {test.request_count}")
    print(f"立即执行的请求: {test.success_count}")
    print(f"需要等待的请求: {test.request_count - test.success_count}")
    print(f"总等待时间: {test.wait_time_total:.2f}秒")
    print(f"实际总耗时: {total_time:.2f}秒")
    
    # 验证线程安全性
    status = test.limiter.get_status()
    print(f"\n最终状态检查:")
    print(f"当前窗口内请求数: {status['current_requests']}")
    print(f"最大限制: {status['max_requests']}")
    print(f"窗口大小: {status['time_window']}秒")
    
    # 关键验证：请求数不应超过限制
    if status['current_requests'] <= status['max_requests']:
        print("✅ 线程安全性验证通过：请求数未超过限制")
    else:
        print("❌ 线程安全性验证失败：请求数超过限制")

def test_decorator_thread_safety():
    """测试装饰器在多线程环境下的表现"""
    print("\n" + "=" * 50)
    print("装饰器多线程测试")
    print("=" * 50)
    
    # 创建装饰器限制的函数
    @rate_limit(max_requests=4, time_window=3)
    def limited_api_call(call_id, thread_id):
        """模拟API调用"""
        print(f"线程{thread_id} - 调用{call_id} 在 {time.time():.2f}")
        time.sleep(0.05)  # 模拟处理时间
        return f"result_{thread_id}_{call_id}"
    
    def decorator_worker(thread_id, num_calls):
        """装饰器测试工作线程"""
        results = []
        for i in range(num_calls):
            result = limited_api_call(i, thread_id)
            results.append(result)
        return results
    
    # 多线程测试
    num_threads = 3
    calls_per_thread = 3
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(decorator_worker, i, calls_per_thread)
            for i in range(num_threads)
        ]
        
        # 等待所有完成
        for future in futures:
            future.result()
    
    print("✅ 装饰器多线程测试完成")

def test_race_condition():
    """测试竞态条件（无锁情况下的问题）"""
    print("\n" + "=" * 50)
    print("竞态条件演示（模拟无锁情况）")
    print("=" * 50)
    
    class UnsafeLimiter:
        """不安全版本（无锁）"""
        def __init__(self, max_requests=5, time_window=5):
            self.max_requests = max_requests
            self.time_window = time_window
            self.requests = []
        
        def unsafe_wait_if_needed(self):
            """不安全版本 - 没有锁保护"""
            now = time.time()
            
            # 清理过期请求（竞态条件可能发生在这里）
            cutoff_time = now - self.time_window
            self.requests = [t for t in self.requests if t > cutoff_time]
            
            # 检查限制（竞态条件可能发生在这里）
            if len(self.requests) >= self.max_requests:
                oldest = min(self.requests)
                wait_time = oldest + self.time_window - now
                if wait_time > 0:
                    time.sleep(wait_time)
                    now = time.time()
            
            # 添加请求（竞态条件肯定发生在这里！）
            self.requests.append(now)
    
    unsafe_limiter = UnsafeLimiter(max_requests=3, time_window=2)
    violation_count = 0
    total_tests = 10
    
    for test_num in range(total_tests):
        requests_in_window = []
        
        def unsafe_worker():
            unsafe_limiter.unsafe_wait_if_needed()
            requests_in_window.append(time.time())
        
        # 同时启动多个线程
        threads = []
        for _ in range(5):  # 超过限制
            t = threading.Thread(target=unsafe_worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # 检查是否违反限制
        current_time = time.time()
        window_requests = [t for t in requests_in_window 
                          if current_time - t <= unsafe_limiter.time_window]
        
        if len(window_requests) > unsafe_limiter.max_requests:
            violation_count += 1
            print(f"测试 {test_num + 1}: ❌ 检测到竞态条件！窗口内请求数: {len(window_requests)}")
        else:
            print(f"测试 {test_num + 1}: ✅ 未检测到竞态条件")
        
        time.sleep(1)  # 等待窗口重置
    
    print(f"\n竞态条件检测结果: {violation_count}/{total_tests} 次测试出现违规")

if __name__ == "__main__":
    # 运行所有测试
    test_thread_safety()
    test_decorator_thread_safety()
    test_race_condition()
    
    print("\n" + "=" * 50)
    print("测试总结:")
    print("- 线程安全性测试验证锁的正确性")
    print("- 装饰器测试验证装饰器在多线程环境的表现")  
    print("- 竞态条件演示说明为什么需要锁")
    print("=" * 50)