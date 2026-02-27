"""
GitHub Trending 数据采集模块（带SSL问题修复）
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
import time
import urllib3
import json

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def clean_stars_count(stars_text: str) -> int:
    """清理星标数字"""
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
        # 关键修复：添加 verify=False
        response = requests.get(
            full_url, 
            headers=headers, 
            timeout=10,
            verify=False
        )
        response.raise_for_status()
        print(f"✅ 请求成功，状态码: {response.status_code}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
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
    
    print("\n✅ 解析完成")
    return repositories

# 测试代码
if __name__ == "__main__":
    print("="*60)
    print("🚀 GitHub Trending 采集器（SSL修复版）")
    print("="*60)
    
    # 只测试daily，避免多次请求
    print("\n--- 测试 daily ---")
    data = fetch_github_trending(since='daily')
    
    if data:
        print(f"\n✅ 成功获取 {len(data)} 个项目")
        
        # 保存到文件
        with open('github_trending_test.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✅ 数据已保存到 github_trending_test.json")
        
        # 打印前3个
        print("\n📊 前3个项目：")
        for i, repo in enumerate(data[:3], 1):
            print(f"\n{i}. {repo['name']}")
            print(f"   📝 {repo['description'][:80]}...")
            print(f"   🔤 {repo['language']} | ⭐ +{repo['stars_today']} today | ⭐ {repo['total_stars']} total")
    else:
        print("❌ 获取数据失败")
    
    print("\n✨ 测试完成！")