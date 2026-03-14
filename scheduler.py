# scheduler.py
"""
TechPulse AI 定时任务
每天8:00和20:00自动更新数据
"""
import os
import schedule
import time
import subprocess
import json
import sys
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime
from pathlib import Path

# 获取项目根目录
ROOT_DIR = Path(__file__).parent

def log(msg):
    """带时间戳的日志"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def run_script(script_name):
    """运行Python脚本（正确处理编码）"""
    script_path = ROOT_DIR / script_name
    log(f"运行: {script_name}")
    
    try:
        # 设置环境变量，强制子进程使用 UTF-8 输出
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'          # Python 3.7+ 支持，进一步确保 UTF-8

        # 运行子进程，指定编码和错误处理策略
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',             # 以 UTF-8 解码输出
            errors='replace',               # 遇到无法解码的字符用 � 替换
            timeout=300,                    # 延长超时，因为采集可能较慢
            env=env
        )
        
        if result.returncode == 0:
            log(f"✅ {script_name} 成功")
            if result.stdout:
                # 打印最后一部分输出，方便查看
                print(f"输出: {result.stdout[-300:]}")
            return True
        else:
            log(f"❌ {script_name} 失败，返回码 {result.returncode}")
            if result.stderr:
                print(f"错误: {result.stderr[-300:]}")
            return False
            
    except subprocess.TimeoutExpired:
        log(f"⏰ {script_name} 超时")
        return False
    except Exception as e:
        log(f"💥 {script_name} 异常: {e}")
        return False

def generate_daily_report():
    """生成每日趋势报告并保存"""
    log("📊 开始生成每日趋势报告...")
    
    try:
        sys.path.insert(0, str(ROOT_DIR / 'src'))
        from src.analyzers.ai_analyzer import AIAnalyzer
        from src.storage.database import Database
        
        db = Database()
        today_articles = db.get_today_articles()
        
        if not today_articles:
            log("📭 今日无文章，跳过报告生成")
            return
        
        log(f"📝 分析今日 {len(today_articles)} 篇文章...")
        
        analyzer = AIAnalyzer()
        report = analyzer.analyze_daily_trends(today_articles)
        
        # 保存到数据库
        with db.get_connection() as conn:
            cursor = conn.cursor()
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                INSERT OR REPLACE INTO daily_reports (report_date, summary, recommendations)
                VALUES (?, ?, ?)
            ''', (today, report['summary'], json.dumps(report['recommendations'], ensure_ascii=False)))
            conn.commit()
        
        log("✅ 每日报告生成完成")
        
    except Exception as e:
        log(f"💥 报告生成失败: {e}")

def update_all():
    log("="*50)
    log("🚀 开始执行定时更新任务")
    log("="*50)
    
    # 1. 采集GitHub Trending
    if not run_script("src/data_sources/github_trending.py"):
        log("❌ GitHub Trending 采集失败，终止后续任务")
        return
    
    # 2. 采集Hacker News
    if not run_script("src/data_sources/hacker_news.py"):
        log("❌ Hacker News 采集失败，终止后续任务")
        return
    
    # 3. 更新数据库
    if not run_script("test_database.py"):
        log("❌ 数据库更新失败")
        return
    
    # 生成每日报告
    generate_daily_report()
    
    log("="*50)
    log("✅ 所有任务完成")
    log("="*50)
    log("\n")  # 空行分隔

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