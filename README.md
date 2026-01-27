# Sina News Crawler

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

一个基于Python的新浪新闻爬虫，支持多分类采集、数据库存储和增量更新。

## 项目简介

Sina News Crawler 是一个专业的网络爬虫工具，专门用于自动采集新浪新闻（news.sina.com.cn）的新闻内容。项目采用模块化设计，支持配置化管理，具备完善的错误处理和日志记录功能。

## 功能特性

### 🚀 核心功能
- **多分类支持**：支持首页、国内、国际、科技、体育、娱乐、财经等多个新闻分类
- **智能解析**：使用XPath精确提取新闻标题、链接和内容
- **数据库存储**：支持SQLite数据库，自动创建表结构和索引
- **增量爬取**：基于时间戳的增量更新机制，避免重复采集
- **去重检测**：基于标题哈希的重复新闻检测

### 🔧 技术特性
- **配置化管理**：YAML配置文件，支持灵活的参数调整
- **模块化设计**：清晰的代码结构，易于扩展和维护
- **错误处理**：完善的异常捕获和重试机制
- **日志记录**：详细的运行日志，便于调试和监控
- **数据导出**：支持JSON和CSV格式的数据导出

## 快速开始

### 环境要求
- Python 3.12+
- 支持的操作系统：Windows / Linux / macOS

### 安装依赖
```bash
pip install -r requirements.txt
```

### 基本使用
1. **配置爬虫参数**（可选）
   编辑 `config.yaml` 文件调整爬虫设置：

   ```yaml
   crawler:
     timeout: 10          # 请求超时时间
     max_retries: 3       # 最大重试次数
     delay_range: [1, 3]  # 请求延迟范围
   
   categories:
     enabled: true
     list:
       - name: "首页"
         url: "https://news.sina.com.cn/"
         max_news: 10
   ```

2. **运行爬虫**
   ```bash
   python main.py
   ```

3. **查看结果**
   - 数据库文件：`database/data/news.db`
   - JSON数据：`database/data/news_data_*.json`
   - CSV摘要：`database/data/news_summary_*.csv`
   - 运行日志：`logs/crawler.log`

### 高级用法
#### 定时运行
```bash
# Linux/macOS 使用 crontab
0 */6 * * * cd /path/to/sina-news-crawler && python main.py

# Windows 使用任务计划程序
```

#### 自定义新闻分类
在 `config.yaml` 中添加新的分类：

```yaml
categories:
  list:
    - name: "自定义分类"
      url: "https://news.sina.com.cn/your-category/"
      max_news: 20
```

## 配置说明

### 主要配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `crawler.timeout` | 请求超时时间(秒) | 10 |
| `crawler.max_retries` | 最大重试次数 | 3 |
| `crawler.delay_range` | 请求延迟范围 | [1, 3] |
| `database.path` | 数据库文件路径 | `database/data/news.db` |
| `output.save_json` | 是否保存JSON文件 | `true` |
| `logging.level` | 日志级别 | `INFO` |

完整配置请参考 `config.yaml` 文件。

## 数据库设计

### 主要数据表

**news表** - 新闻数据存储
- `id`: 主键
- `title`: 新闻标题
- `url`: 新闻链接
- `category`: 新闻分类
- `publish_time`: 发布时间
- `crawl_time`: 爬取时间
- `content`: 新闻内容（可选）

**crawl_log表** - 爬取日志
- 记录每次爬取的成功/失败状态
- 用于增量爬取控制

## 开发指南

### 扩展新的新闻源
1. 在 `crawler/` 目录下创建新的爬虫类
2. 实现基础的爬取和解析方法
3. 在配置文件中添加新的新闻源配置

### 添加新的数据字段
1. 修改 `database/news_db.py` 中的表结构
2. 更新爬虫的数据提取逻辑
3. 修改数据导出工具

## 注意事项

### 法律合规
- 请遵守网站的robots.txt协议
- 合理控制请求频率，避免对服务器造成压力
- 仅用于学习和研究目的

### 技术限制
- 依赖于网站HTML结构，结构变化时需要调整XPath
- 部分动态加载内容可能需要额外处理

## 贡献指南

欢迎提交Issue和Pull Request来改进项目！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 更新日志

### v1.0.0 (2026-01-27)
- 初始版本发布
- 支持新浪新闻多分类爬取
- SQLite数据库存储
- 配置化管理

