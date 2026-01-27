"""
数据导出模块
"""
import os
import json
import csv
import logging
from datetime import datetime
from typing import List, Dict
from .retry import simple_retry

class DataExporter:
    """数据导出器"""
    
    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
    
    def save_to_json(self, news_data: Dict[str, List[Dict]], filename: str = None):
        """保存为JSON文件"""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"news_data_{timestamp}.json"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # 格式化数据
            formatted_data = self._format_for_json(news_data)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(formatted_data, f, 
                         ensure_ascii=False, 
                         indent=2,
                         default=str)
            
            self.logger.info(f"JSON数据已保存: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"保存JSON失败: {e}")
            return None
    
    def save_to_csv(self, news_data: Dict[str, List[Dict]], filename: str = None):
        """保存为CSV文件"""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"news_summary_{timestamp}.csv"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # 转换为CSV格式
            csv_data = self._format_for_csv(news_data)
            
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_data['fields'])
                writer.writeheader()
                writer.writerows(csv_data['rows'])
            
            self.logger.info(f"CSV数据已保存: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"保存CSV失败: {e}")
            return None
    
    def _format_for_json(self, news_data: Dict[str, List[Dict]]) -> Dict:
        """格式化数据为JSON"""
        formatted = {
            'metadata': {
                'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_categories': len(news_data),
                'total_articles': sum(len(articles) for articles in news_data.values())
            },
            'categories': {}
        }
        
        for category, articles in news_data.items():
            formatted['categories'][category] = {
                'count': len(articles),
                'articles': articles
            }
        
        return formatted
    
    def _format_for_csv(self, news_data: Dict[str, List[Dict]]) -> Dict:
        """格式化数据为CSV"""
        fields = [
            'category', 'title', 'publish_time', 'source', 
            'content_length', 'url', 'crawl_time'
        ]
        
        rows = []
        for category, articles in news_data.items():
            for article in articles:
                row = {
                    'category': category,
                    'title': article.get('title', '')[:100],  # 限制标题长度
                    'publish_time': article.get('publish_time', ''),
                    'source': article.get('source', ''),
                    'content_length': article.get('content_length', 0),
                    'url': article.get('url', ''),
                    'crawl_time': article.get('crawl_time', '')
                }
                rows.append(row)
        
        return {
            'fields': fields,
            'rows': rows
        }
    
    def export_statistics(self, stats: Dict, filename: str = None):
        """导出统计信息"""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"crawl_stats_{timestamp}.json"
            
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"统计信息已保存: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"保存统计信息失败: {e}")
            return None
    
    @simple_retry(max_retries=2, delay=0.5)
    def save_to_json_with_retry(self, news_data: Dict[str, List[Dict]]):
        """带重试的JSON导出方法"""
        return self.save_to_json(news_data)
    
    @simple_retry(max_retries=2, delay=0.5)
    def save_to_csv_with_retry(self, news_data: Dict[str, List[Dict]]):
        """带重试的CSV导出方法"""
        return self.save_to_csv(news_data)