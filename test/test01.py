# 先写个简单的测试
import requests
from lxml import etree
import os

url = "https://news.sina.com.cn/"
# 查看HTML结构，找到新闻列表
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)
    response.encoding = "utf-8"  # 设置编码，避免中文乱码
    html = response.text  # 获取网页的HTML文本内容
    
    # 保存HTML到文件以便查看结构
    with open("sina_news_structure.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML结构已保存到 sina_news_structure.html 文件")
    
except Exception as e:
    print(f"请求失败：{e}")
    html = ""
    
if html:
    tree = etree.HTML(html)  # 解析HTML
    
    # 先尝试几种常见的新闻列表选择器
    selectors = [
        '//div[contains(@class, "news")]//a',
        '//ul[contains(@class, "news")]//a',
        '//div[contains(@class, "list")]//a',
        '//ul[contains(@class, "list")]//a',
        '//h2[contains(text(), "新闻")]/following-sibling::*//a'
    ]
    
    print("尝试查找新闻列表...")
    for i, selector in enumerate(selectors, 1):
        news_items = tree.xpath(selector)
        if news_items:
            print(f"\n选择器 {i} 找到 {len(news_items)} 个新闻项:")
            for j, item in enumerate(news_items[:3]):  # 只显示前3个
                title = item.xpath('string(.)').strip()
                link = item.xpath('./@href')
                if link:
                    print(f"  {j+1}. 标题: {title[:50]}...")
                    print(f"     链接: {link[0]}")
            break
    else:
        print("未找到新闻列表，请查看保存的HTML文件分析结构")