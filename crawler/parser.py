"""
页面解析模块
"""
import re
import logging
from datetime import datetime
from typing import List, Dict, Optional
from lxml import etree

class NewsParser:
    """新闻页面解析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 各分类的选择器配置
        self.list_selectors = {
            '首页': [
                '//div[@class="blk122"]//a',
                '//div[contains(@class, "part")]//a',
                '//div[@class="feed-card-item"]//a',
                '//h2[contains(text(), "要闻")]/following-sibling::div//a',
            ],
            '国内': [
                '//div[@class="content"]//a[contains(@href, "/doc-")]',
                '//ul[@class="news-list"]//a',
                '//div[contains(@class, "news-item")]//a',
            ],
            '国际': [
                '//div[@class="content"]//a[contains(@href, "/doc-")]',
                '//ul[@class="news-list"]//a',
            ],
            '科技': [
                '//div[@class="con"]//a[contains(@href, "/doc-")]',
                '//ul[contains(@class, "list")]//a',
            ],
            '体育': [
                '//div[contains(@class, "news")]//a[contains(@href, ".shtml")]',
                '//ul[@class="list"]//a',
            ],
            '娱乐': [
                '//div[@class="main-content"]//a[contains(@href, "/doc-")]',
                '//ul[contains(@class, "news")]//a',
            ],
            '财经': [
                '//div[contains(@class, "list")]//a[contains(@href, ".shtml")]',
                '//ul[@class="newsList"]//a',
            ],
        }
    
    def parse_news_list(self, html: str, category: str) -> List[Dict]:
        """解析新闻列表页"""
        if not html:
            return []
        
        tree = etree.HTML(html)
        news_links = []
        
        # 获取该分类的选择器
        selectors = self.list_selectors.get(category, self._get_default_selectors())
        
        for selector in selectors:
            elements = tree.xpath(selector)
            if elements and len(elements) > 2:
                self.logger.debug(f"使用选择器找到 {len(elements)} 个元素: {selector[:50]}...")
                
                for elem in elements:
                    try:
                        news_item = self._parse_list_item(elem)
                        if news_item and self._is_valid_news_item(news_item):
                            news_item['category'] = category
                            news_links.append(news_item)
                    except Exception as e:
                        self.logger.debug(f"解析列表项失败: {e}")
                        continue
                
                if news_links:
                    break
        
        # 去重
        unique_news = []
        seen_urls = set()
        for news in news_links:
            if news['url'] not in seen_urls:
                unique_news.append(news)
                seen_urls.add(news['url'])
        
        self.logger.info(f"解析到 {len(unique_news)} 个新闻链接 (分类: {category})")
        return unique_news
    
    def _parse_list_item(self, elem) -> Optional[Dict]:
        """解析单个列表项"""
        try:
            href = elem.xpath('./@href')
            title = elem.xpath('string(.)').strip()
            
            if not href or not title:
                return None
            
            url = self._normalize_url(href[0])
            
            # 过滤非新闻链接
            if not self._is_news_url(url) or len(title) < 5:
                return None
            
            return {
                'title': title,
                'url': url,
                'source': 'sina'
            }
            
        except Exception as e:
            self.logger.debug(f"解析列表项元素失败: {e}")
            return None
    
    def parse_news_detail(self, html: str, url: str, category: str) -> Optional[Dict]:
        """解析新闻详情页"""
        if not html:
            return None
        
        tree = etree.HTML(html)
        
        try:
            # 提取标题
            title = self._extract_title(tree)
            if not title:
                self.logger.warning(f"未找到标题: {url}")
                return None
            
            # 提取发布时间
            publish_time = self._extract_publish_time(tree)
            
            # 提取来源
            source = self._extract_source(tree)
            
            # 提取内容
            content = self._extract_content(tree)
            
            # 提取摘要
            summary = self._extract_summary(tree, content)
            
            # 提取关键词
            keywords = self._extract_keywords(tree)
            
            # 提取图片
            images = self._extract_images(tree)
            
            news_detail = {
                'title': title,
                'url': url,
                'category': category,
                'publish_time': publish_time,
                'source': source,
                'content': content,
                'content_length': len(content),
                'summary': summary,
                'keywords': keywords,
                'images': images,
            }
            
            self.logger.debug(f"成功解析新闻: {title[:50]}... (内容长度: {len(content)})")
            return news_detail
            
        except Exception as e:
            self.logger.error(f"解析新闻详情失败 {url}: {e}")
            return None
    
    def _extract_title(self, tree) -> str:
        """提取标题"""
        title_selectors = [
            '//h1[@class="main-title"]/text()',
            '//h1[contains(@class, "title")]/text()',
            '//div[@class="article-header"]/h1/text()',
            '//h1/text()',
            '//title/text()',
        ]
        
        for selector in title_selectors:
            result = tree.xpath(selector)
            if result:
                title = result[0].strip()
                # 清理标题中的网站名
                title = re.sub(r'[-_]\s*新浪网.*$', '', title)
                title = re.sub(r'[-_]\s*新浪新闻.*$', '', title)
                return title
        
        return ""
    
    def _extract_publish_time(self, tree) -> str:
        """提取发布时间"""
        time_selectors = [
            '//span[@class="date"]/text()',
            '//div[@class="date-source"]/span/text()',
            '//span[contains(@class, "time")]/text()',
            '//meta[@property="article:published_time"]/@content',
            '//meta[@name="weibo: article:create_at"]/@content',
        ]
        
        for selector in time_selectors:
            result = tree.xpath(selector)
            if result:
                time_str = result[0].strip()
                # 尝试格式化时间
                try:
                    # 移除可能的中文字符
                    time_str = re.sub(r'[年月日时分秒]', '-', time_str)
                    time_str = time_str.replace('--', '-').strip('-')
                    return time_str
                except:
                    return time_str
        
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def _extract_source(self, tree) -> str:
        """提取来源"""
        source_selectors = [
            '//span[@class="source"]/text()',
            '//a[@class="source"]/text()',
            '//div[@class="date-source"]/a/text()',
            '//meta[@property="article:author"]/@content',
        ]
        
        for selector in source_selectors:
            result = tree.xpath(selector)
            if result:
                source = result[0].strip()
                if source and source != "新浪网":
                    return source
        
        return "新浪新闻"
    
    def _extract_content(self, tree) -> str:
        """提取内容"""
        content_selectors = [
            '//div[@class="article"]//p',
            '//div[@id="artibody"]//p',
            '//div[contains(@class, "article_body")]//p',
            '//div[@class="article-content"]//p',
            '//div[contains(@class, "content")]//p',
        ]
        
        content_parts = []
        for selector in content_selectors:
            elems = tree.xpath(selector)
            if elems:
                for elem in elems:
                    text = elem.xpath('string(.)').strip()
                    # 过滤广告、空行、短文本
                    if (text and len(text) > 10 and 
                        not text.startswith('[') and 
                        '广告' not in text and
                        'function(' not in text.lower()):
                        content_parts.append(text)
                
                if content_parts:
                    break
        
        # 合并内容并清理
        content = '\n\n'.join(content_parts)
        
        # 清理内容
        content = re.sub(r'\s*\n\s*\n\s*', '\n\n', content)  # 多个空行合并
        content = re.sub(r'^[【\[].*?[】\]]\s*', '', content, flags=re.MULTILINE)  # 删除括号内容
        content = content.strip()
        
        return content
    
    def _extract_summary(self, tree, content: str) -> str:
        """提取摘要"""
        summary_selectors = [
            '//meta[@name="description"]/@content',
            '//div[contains(@class, "summary")]/text()',
            '//p[contains(@class, "summary")]/text()',
        ]
        
        for selector in summary_selectors:
            result = tree.xpath(selector)
            if result:
                summary = result[0].strip()
                if summary and len(summary) > 20:
                    return summary
        
        # 如果没有找到摘要，从内容生成
        if content:
            # 取前200字作为摘要
            summary = content[:200].strip()
            if len(content) > 200:
                summary += "..."
            return summary
        
        return ""
    
    def _extract_keywords(self, tree) -> List[str]:
        """提取关键词"""
        keywords_elem = tree.xpath('//meta[@name="keywords"]/@content')
        if keywords_elem:
            keywords_str = keywords_elem[0].strip()
            if keywords_str:
                # 分割关键词
                keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
                return keywords
        
        return []
    
    def _extract_images(self, tree) -> List[Dict]:
        """提取图片信息"""
        img_selectors = [
            '//div[@class="article"]//img',
            '//div[@id="artibody"]//img',
            '//div[contains(@class, "article_body")]//img',
        ]
        
        images = []
        for selector in img_selectors:
            img_elements = tree.xpath(selector)
            for img in img_elements[:5]:  # 最多取5张
                try:
                    src = img.xpath('./@src')
                    alt = img.xpath('./@alt')
                    
                    if src and src[0]:
                        img_info = {
                            'url': self._normalize_url(src[0]),
                            'alt': alt[0] if alt and alt[0] else "",
                            'caption': img.xpath('./following-sibling::span/text()')
                        }
                        images.append(img_info)
                except:
                    continue
        
        return images
    
    def _normalize_url(self, url: str) -> str:
        """URL规范化"""
        if not url:
            return ""
        
        if url.startswith('//'):
            url = 'https:' + url
        elif url.startswith('/'):
            url = 'https://news.sina.com.cn' + url
        
        # 清理URL参数
        url = re.sub(r'[\?&]from=\w+', '', url)
        url = re.sub(r'[\?&]ch=\d+', '', url)
        url = re.sub(r'\?$', '', url)  # 删除末尾的?
        
        return url
    
    def _is_news_url(self, url: str) -> bool:
        """判断是否为新闻URL"""
        if not url:
            return False
        
        # 新闻URL特征
        news_patterns = [
            r'/doc-',
            r'\.shtml$',
            r'news\.sina\.com\.cn/[a-z]/.*\.shtml',
            r'https://news\.sina\.com\.cn/.*/\d{4}-\d{2}-\d{2}/.*\.html',
        ]
        
        for pattern in news_patterns:
            if re.search(pattern, url):
                return True
        
        return False
    
    def _is_valid_news_item(self, news_item: Dict) -> bool:
        """验证新闻项是否有效"""
        # 排除标题中的无效关键词
        exclude_keywords = ['更多', '专题', '直播', '视频', '图片集', '滚动']
        
        title = news_item.get('title', '')
        if any(keyword in title for keyword in exclude_keywords):
            return False
        
        # 标题长度检查
        if len(title) < 5 or len(title) > 200:
            return False
        
        # URL检查
        url = news_item.get('url', '')
        if not url or 'javascript:' in url:
            return False
        
        return True
    
    def _get_default_selectors(self):
        """获取默认选择器"""
        return [
            '//a[contains(@href, "/doc-")]',
            '//a[contains(@href, ".shtml")]',
            '//a[contains(text(), "新闻")]',
        ]