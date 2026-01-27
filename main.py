#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新浪新闻爬虫 - 主入口
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logger import setup_logging
from crawler.sina_crawler import SinaNewsCrawler

def main():
    """主函数"""
    # 设置日志
    setup_logging()
    
    print("=" * 60)
    print("新浪新闻爬虫 - 配置化版本")
    print("=" * 60)
    
    # 创建爬虫实例
    crawler = SinaNewsCrawler()
    
    # 运行爬虫
    try:
        news_data = crawler.run()
        
        if any(news_data.values()):
            print("\n✅ 爬取完成！")
            print(f"📁 数据已保存到数据库: {crawler.db.db_path}")
        else:
            print("\n⚠️ 未爬取到新闻数据")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断")
    except Exception as e:
        print(f"\n❌ 爬虫运行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        crawler.db.close()

if __name__ == "__main__":
    main()