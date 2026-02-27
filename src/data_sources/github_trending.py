# github_trending.py
"""
GitHub Trending 数据采集模块
"""

import sys
import io
from pathlib import Path

# 保存原始的标准输出
_original_stdout = sys.stdout

# 尝试设置UTF-8编码，但如果失败就使用原始输出
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
except:
    sys.stdout = _original_stdout

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
import re
import time
import urllib3
import json
from datetime import datetime

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 导入基类
try:
    from src.data_sources.base_source import DataSource
except ImportError as e:
    print(f"警告: 导入DataSource失败: {e}")
    # 定义一个简单的基类作为备选
    class DataSource:
        def __init__(self, name, config):
            self.name = name
            self.config = config
            self.logger = type('Logger', (), {'info': print, 'error': print})()
        def update_stats(self, success=True, count=0):
            pass


class GitHubTrendingDataSource(DataSource):
    """GitHub Trending 数据源类（符合插件化架构）"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.logger.info(f"初始化 GitHub Trending 数据源")
        self.status = 'active'
        self.last_run = None
        self.total_fetched = 0
        self.error_count = 0
    
    def fetch_data(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取数据（实现抽象方法）"""
        since = self.config.get('since', 'daily')
        data = fetch_github_trending(since=since)
        
        # 转换为Article格式
        articles = []
        for item in data[:limit]:
            article = {
                'source': self.name,
                'source_id': item['name'],
                'title': f"[GitHub] {item['name']}",
                'url': item['url'],
                'description': item['description'],
                'category': 'technology',
                'tags': [item['language']] if item['language'] != 'Unknown' else [],
                'score': item['total_stars'],
                'comments': item['forks'],
                'author': item['name'].split('/')[0] if '/' in item['name'] else '',
                'published_at': None,
                'fetched_at': item['fetched_at'],
                'extra': {
                    'stars_today': item['stars_today'],
                    'language': item['language']
                }
            }
            articles.append(article)
        
        self.total_fetched += len(articles)
        self.last_run = datetime.now()
        return articles
    
    def get_info(self) -> Dict[str, Any]:
        """获取数据源信息"""
        return {
            'name': self.name,
            'type': 'github_trending',
            'status': self.status,
            'last_run': self.last_run.strftime('%Y-%m-%d %H:%M:%S') if self.last_run else None,
            'total_fetched': self.total_fetched,
            'error_count': self.error_count
        }


def clean_stars_count(stars_text: str) -> int:
    """清理星标数字，处理 '1.2k', '45.6k', '1.2m' 等格式"""
    if not stars_text:
        return 0
    
    text = stars_text.replace(',', '').strip()
    match = re.search(r'([\d.]+)([km]?)', text.lower())
    if not match:
        return 0
    
    number_str, suffix = match.groups()
    
    try:
        number = float(number_str)
        if suffix == 'k':
            return int(number * 1000)
        elif suffix == 'm':
            return int(number * 1000000)
        else:
            return int(number)
    except ValueError:
        return 0


def parse_repository(repo_element) -> Optional[Dict]:
    """解析单个仓库元素"""
    try:
        # 提取项目名称
        title_element = repo_element.find('h2')
        if not title_element:
            return None
        
        link_element = title_element.find('a')
        if not link_element:
            return None
        
        full_name = link_element.get_text().strip().replace(' ', '').replace('\n', '')
        repo_url = "https://github.com" + link_element.get('href', '')
        
        # 提取描述
        description_element = repo_element.find('p', class_='col-9')
        if not description_element:
            description_element = repo_element.find('p')
        description = description_element.get_text().strip() if description_element else ""
        
        # 提取编程语言
        language_element = repo_element.find('span', itemprop='programmingLanguage')
        language = language_element.get_text().strip() if language_element else "Unknown"
        
        # 提取星标信息
        stars_elements = repo_element.find_all('a', href=re.compile(r'/stargazers'))
        total_stars = 0
        if len(stars_elements) > 0:
            stars_text = stars_elements[0].get_text().strip()
            total_stars = clean_stars_count(stars_text)
        
        # 提取今日新增星标
        today_stars_element = repo_element.find('span', class_='d-inline-block float-sm-right')
        today_stars = 0
        if today_stars_element:
            today_text = today_stars_element.get_text().strip()
            match = re.search(r'([\d,.]+[k]?)\s+stars?\s+today', today_text, re.IGNORECASE)
            if match:
                today_stars = clean_stars_count(match.group(1))
        
        # 提取Fork数
        forks = 0
        if len(stars_elements) > 1:
            forks_text = stars_elements[1].get_text().strip()
            forks = clean_stars_count(forks_text)
        
        return {
            'name': full_name,
            'url': repo_url,
            'description': description,
            'language': language,
            'total_stars': total_stars,
            'stars_today': today_stars,
            'forks': forks,
            'source': 'github_trending',
            'fetched_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        print(f"\n⚠️ 解析仓库时出错: {e}")
        return None


def fetch_github_trending(url: str = "https://github.com/trending", since: str = "daily") -> List[Dict]:
    """获取GitHub Trending项目列表"""
    
    if since in ["daily", "weekly", "monthly"]:
        full_url = f"{url}?since={since}"
    else:
        full_url = url
    
    print(f"正在请求: {full_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    try:
        response = requests.get(
            full_url, 
            headers=headers, 
            timeout=10,
            verify=False
        )
        response.raise_for_status()
        print(f"[OK] 请求成功，状态码: {response.status_code}")
        
    except requests.exceptions.RequestException as e:
        print(f"[Error] 请求失败: {e}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    repo_articles = soup.find_all('article', class_='Box-row')
    
    print(f"找到 {len(repo_articles)} 个仓库元素")
    
    repositories = []
    for i, article in enumerate(repo_articles, 1):
        print(f"\r正在解析第 {i}/{len(repo_articles)} 个仓库...", end="")
        repo_info = parse_repository(article)
        if repo_info:
            repositories.append(repo_info)
        time.sleep(0.05)
    
    print("\n[OK] 解析完成")
    return repositories


# 测试代码
if __name__ == "__main__":
    # 使用普通的print，避免编码问题
    print("="*60)
    print("[Start] GitHub Trending 采集器")
    print("="*60)
    
    # 测试 daily
    print("\n--- 测试 daily ---")
    data = fetch_github_trending(since='daily')
    
    if data:
        print(f"\n[OK] 成功获取 {len(data)} 个项目")
        
        # 保存到文件
        with open('github_trending_test.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("[OK] 数据已保存到 github_trending_test.json")
        
        # 打印前3个
        print("\n[Data] 前3个项目：")
        for i, repo in enumerate(data[:3], 1):
            print(f"\n{i}. {repo['name']}")
            print(f"   📝 {repo['description'][:80]}...")
            print(f"   🔤 {repo['language']} | ⭐ +{repo['stars_today']} today | ⭐ {repo['total_stars']} total")
    else:
        print("[Error] 获取数据失败")
    
    print("\n[Done] 测试完成！")