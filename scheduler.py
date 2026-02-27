# scheduler.py
"""
TechPulse AI 定时任务
每天8:00和20:00自动更新数据
"""

import schedule
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 获取项目根目录
ROOT_DIR = Path(__file__).parent

def log(msg):
    """带时间戳的日志"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def run_script(script_name):
    """运行Python脚本"""
    script_path = ROOT_DIR / script_name
    log(f"运行: {script_name}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=60  # 60秒超时
        )
        
        if result.returncode == 0:
            log(f"✅ {script_name} 成功")
            if result.stdout:
                print(f"输出: {result.stdout[-200:]}")  # 只打印最后200字符
            return True
        else:
            log(f"❌ {script_name} 失败")
            if result.stderr:
                print(f"错误: {result.stderr[-200:]}")
            return False
            
    except subprocess.TimeoutExpired:
        log(f"⏰ {script_name} 超时")
        return False
    except Exception as e:
        log(f"💥 {script_name} 异常: {e}")
        return False

def update_all():
    """更新所有数据"""
    log("="*50)
    log("🚀 开始执行定时更新任务")
    log("="*50)
    
    # 1. 采集GitHub Trending
    run_script("src/data_sources/github_trending.py")
    
    # 2. 采集Hacker News
    run_script("src/data_sources/hacker_news.py")
    
    # 3. 更新数据库
    run_script("test_database.py")
    
    log("="*50)
    log("✅ 所有任务完成")
    log("="*50)
    print("\n")  # 空行分隔

def main():
    """主函数"""
    log("⏰ TechPulse AI 定时任务启动")
    log(f"📂 工作目录: {ROOT_DIR}")
    log("📅 定时计划: 每天 08:00 和 20:00")
    log("="*50)
    
    # 立即执行一次（可选，注释掉就不立即执行）
    log("🔄 立即执行一次...")
    update_all()
    
    # 设置定时任务
    schedule.every().day.at("08:00").do(update_all)
    schedule.every().day.at("20:00").do(update_all)
    
    log("⏳ 等待下一个定时任务...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n👋 定时任务已停止")