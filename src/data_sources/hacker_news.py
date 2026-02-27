import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

"""
Hacker News 数据采集模块
功能：获取Hacker News Top Stories，提取关键信息
API文档：https://github.com/HackerNews/API
"""

import requests
from typing import List, Dict, Optional
import time
import json
from datetime import datetime

# Hacker News API 基础URL
BASE_URL = "https://hacker-news.firebaseio.com/v0"

def fetch_top_stories(limit: int = 30) -> List[Dict]:
    """
    获取Hacker News Top Stories
    
    Args:
        limit: 获取的故事数量，默认30条
        
    Returns:
        故事列表，每个故事包含标题、链接、分数等信息
    """
    
    print(f"[Search] 正在获取Hacker News Top {limit} 故事...")
    
    try:
        # 1. 获取Top Stories ID列表
        top_stories_url = f"{BASE_URL}/topstories.json"
        response = requests.get(top_stories_url, timeout=10)
        response.raise_for_status()
        
        story_ids = response.json()
        print(f"[OK] 获取到 {len(story_ids)} 个故事ID")
        
        # 2. 只取前limit个
        story_ids = story_ids[:limit]
        
        # 3. 获取每个故事的详情
        stories = []
        for i, story_id in enumerate(story_ids, 1):
            print(f"\r正在获取第 {i}/{limit} 个故事...", end="")
            
            story = fetch_story_detail(story_id)
            if story:
                stories.append(story)
            
            # 避免请求过快
            time.sleep(0.1)
        
        print("\n[OK] 故事获取完成")
        return stories
        
    except requests.exceptions.RequestException as e:
        print(f"[Error] 请求失败: {e}")
        return []

def fetch_story_detail(story_id: int) -> Optional[Dict]:
    """
    获取单个故事的详细信息
    
    Args:
        story_id: 故事ID
        
    Returns:
        故事详细信息
    """
    try:
        story_url = f"{BASE_URL}/item/{story_id}.json"
        response = requests.get(story_url, timeout=10)
        response.raise_for_status()
        
        item = response.json()
        
        # 只返回类型为story的项目
        if item.get('type') != 'story':
            return None
        
        # 转换时间戳
        timestamp = item.get('time', 0)
        publish_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        # 构建返回数据
        story = {
            'id': story_id,
            'title': item.get('title', ''),
            'url': item.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
            'score': item.get('score', 0),
            'descendants': item.get('descendants', 0),  # 评论数
            'author': item.get('by', 'unknown'),
            'publish_time': publish_time,
            'timestamp': timestamp,
            'source': 'hacker_news',
            'fetched_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 如果有文本内容（Ask HN类型）
        if item.get('text'):
            story['text'] = item.get('text')
        
        return story
        
    except Exception as e:
        print(f"\n⚠️ 获取故事 {story_id} 失败: {e}")
        return None

def filter_tech_related(stories: List[Dict]) -> List[Dict]:
    """
    过滤出技术相关的内容（可选）
    
    可以根据标题关键词过滤，排除非技术内容
    """
    tech_keywords = [
        'python', 'javascript', 'rust', 'go', 'java', 'ai', 'ml', 
        'programming', 'code', 'software', 'web', 'app', 'startup',
        'database', 'cloud', 'dev', 'tech', 'computer', 'linux',
        'open source', 'github', 'api', 'framework', 'library'
    ]
    
    filtered = []
    for story in stories:
        title = story['title'].lower()
        # 如果标题包含任何技术关键词，保留
        if any(keyword in title for keyword in tech_keywords):
            filtered.append(story)
    
    return filtered

def save_to_json(data: List[Dict], filename: str = "hacker_news.json"):
    """保存数据到JSON文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] 数据已保存到 {filename}")

def print_sample(data: List[Dict], count: int = 5):
    """打印示例数据"""
    print("\n" + "="*60)
    print(f"[Data] Hacker News Top Stories (前{count}个)")
    print("="*60)
    
    for i, story in enumerate(data[:count], 1):
        print(f"\n{i}. {story['title']}")
        print(f"   👤 {story['author']} | ⭐ {story['score']} points | 💬 {story['descendants']} comments")
        print(f"   🕒 {story['publish_time']}")
        print(f"   🔗 {story['url']}")
    
    print("\n" + "="*60)
    print(f"[OK] 共获取 {len(data)} 个故事")
    print("="*60)

# 测试函数
def test_fetch_hacker_news():
    """测试Hacker News采集功能"""
    
    print("[Search] 正在测试Hacker News采集...\n")
    
    # 获取Top Stories
    stories = fetch_top_stories(limit=20)
    
    if stories:
        print(f"\n[OK] 成功获取 {len(stories)} 个故事")
        
        # 保存数据
        save_to_json(stories)
        
        # 打印示例
        print_sample(stories)
        
        # 可选：技术相关过滤
        tech_stories = filter_tech_related(stories)
        print(f"\n📌 技术相关故事: {len(tech_stories)}/{len(stories)}")
        
        # 统计信息
        avg_score = sum(s['score'] for s in stories) / len(stories)
        avg_comments = sum(s['descendants'] for s in stories) / len(stories)
        print(f"\n📈 统计: 平均分 {avg_score:.1f}, 平均评论 {avg_comments:.1f}")
        
    else:
        print("[Error] 获取数据失败")

if __name__ == "__main__":
    print("="*60)
    print("[Start] Hacker News 采集器")
    print("="*60)
    
    # 运行测试
    test_fetch_hacker_news()
    
    print("\n[Done] 测试完成！")