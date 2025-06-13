# Brave搜索API集成指南

## 概述

Brave搜索API是一个独立的搜索引擎API，提供不依赖Google的搜索结果。本指南介绍如何将Brave Web Search API集成到报告生成系统中，为您的应用提供多样化的搜索渠道。

## 功能特性

### 🔍 核心搜索功能
- **网络搜索**: 全面的网络内容搜索
- **新闻搜索**: 最新新闻和资讯获取
- **研究内容搜索**: 学术和专业内容检索
- **行业洞察搜索**: 行业趋势和市场分析
- **本地搜索**: 基于地理位置的本地信息搜索

### 🚀 高级特性
- **时间过滤**: 支持多种时间范围（天、周、月、年）
- **语言支持**: 多语言搜索（中文、英文等）
- **安全搜索**: 内容过滤级别控制
- **地理定位**: 支持地理位置相关搜索
- **站点限制**: 在特定网站内搜索
- **结果去重**: 自动处理重复内容

### 🌟 独特优势
- **独立搜索引擎**: 不依赖Google，提供多样化视角
- **隐私保护**: Brave注重用户隐私保护
- **快速响应**: 优化的API性能
- **丰富元数据**: 详细的搜索结果信息

## 安装和配置

### 1. 获取Brave搜索API密钥

#### 步骤1: 访问Brave搜索API官网
1. 访问 [Brave Search API](https://brave.com/search/api/)
2. 点击 "Get Started" 开始注册

#### 步骤2: 创建账户并订阅
1. 注册Brave账户
2. 选择适合的订阅计划：
   - **免费层**: 每月2,000次免费搜索
   - **基础层**: 每月更多搜索次数
   - **专业层**: 高级功能和更高配额

#### 步骤3: 获取API密钥
1. 在控制台中创建新的API密钥
2. 复制生成的API密钥（格式类似：BSA4bcKQe6t46PvsVgwVmTNSSvynmbI）

### 2. 配置环境变量

在您的 `.env` 文件中添加以下配置：

```bash
# Brave搜索API配置
BRAVE_SEARCH_API_KEY=您的Brave搜索API密钥
```

### 3. 验证配置

运行测试脚本验证配置是否正确：

```bash
python example_google_search_integration.py
```

## 使用方法

### 基本使用

```python
from collectors.brave_search_collector import BraveSearchCollector

# 初始化收集器
brave_collector = BraveSearchCollector()

# 基本搜索
results = brave_collector.search("人工智能", count=10)

# 打印结果
for result in results:
    print(f"标题: {result['title']}")
    print(f"内容: {result['content'][:100]}...")
    print(f"来源: {result['source']}")
    print(f"链接: {result['url']}")
    print("-" * 50)
```

### 新闻搜索

```python
# 搜索最新新闻
news_results = brave_collector.search_news("区块链技术", days_back=7, max_results=5)

print(f"找到 {len(news_results)} 条新闻")
for news in news_results:
    print(f"新闻: {news['title']}")
    print(f"来源: {news['source']}")
    print(f"时间: {news.get('published_date', '未知')}")
```

### 研究内容搜索

```python
# 搜索研究内容
research_results = brave_collector.search_research_content("机器学习", days_back=30, max_results=5)

print(f"找到 {len(research_results)} 条研究内容")
for research in research_results:
    print(f"研究: {research['title']}")
    print(f"来源: {research['source']}")
```

### 行业洞察搜索

```python
# 搜索行业洞察
insight_results = brave_collector.search_industry_insights("电动汽车", days_back=90, max_results=5)

print(f"找到 {len(insight_results)} 条行业洞察")
for insight in insight_results:
    print(f"洞察: {insight['title']}")
    print(f"来源: {insight['source']}")
```

### 本地搜索

```python
# 本地搜索
local_results = brave_collector.local_search("人工智能公司", location="北京", count=5)

print(f"找到 {len(local_results)} 个本地结果")
for local in local_results:
    print(f"公司: {local['title']}")
    print(f"地址: {local.get('address', '未知地址')}")
    print(f"电话: {local.get('phone', '未知电话')}")
```

### 综合搜索

```python
# 一次性获取所有类型的内容
comprehensive_results = brave_collector.get_comprehensive_research("5G技术", days_back=7)

print(f"总结果数: {comprehensive_results['total_count']}")
print(f"新闻: {len(comprehensive_results['news'])} 条")
print(f"研究: {len(comprehensive_results['research'])} 条")
print(f"行业洞察: {len(comprehensive_results['industry_insights'])} 条")
print(f"通用: {len(comprehensive_results['general'])} 条")
```

### 高级搜索选项

```python
# 高级搜索参数
advanced_results = brave_collector.search(
    query="人工智能",
    count=15,
    freshness='pw',  # 过去一周
    country='CN',    # 中国
    language='zh',   # 中文
    safesearch='moderate',  # 适中的安全搜索
    location_data={
        'latitude': 39.9042,    # 北京纬度
        'longitude': 116.4074,  # 北京经度
        'city': '北京',
        'country_code': 'CN'
    }
)
```

## API参数说明

### search()方法参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| query | str | 搜索查询 | 必需 |
| count | int | 返回结果数量(1-20) | 10 |
| offset | int | 结果偏移量 | 0 |
| freshness | str | 时间过滤('pd', 'pw', 'pm', 'py') | None |
| country | str | 国家代码('US', 'CN'等) | None |
| language | str | 语言代码('en', 'zh'等) | None |
| safesearch | str | 安全搜索('off', 'moderate', 'strict') | 'moderate' |

### freshness参数值

- **'pd'**: 过去一天
- **'pw'**: 过去一周
- **'pm'**: 过去一个月
- **'py'**: 过去一年

## 集成到现有报告生成流程

### 多搜索引擎集成

```python
from collectors.brave_search_collector import BraveSearchCollector
from collectors.google_search_collector import GoogleSearchCollector
from collectors.tavily_collector import TavilyCollector

def multi_engine_search(topic):
    """多搜索引擎整合搜索"""
    results = {}
    
    # Brave搜索
    brave_collector = BraveSearchCollector()
    if brave_collector.has_api_key:
        results['brave'] = brave_collector.get_comprehensive_research(topic)
    
    # Google搜索
    google_collector = GoogleSearchCollector()
    if google_collector.has_api_key:
        results['google'] = google_collector.get_comprehensive_research(topic)
    
    # Tavily搜索
    tavily_collector = TavilyCollector()
    if tavily_collector.has_api_key:
        results['tavily'] = tavily_collector.search(topic, max_results=10)
    
    return results
```

### 报告生成器增强

```python
# 在您的报告生成脚本中
from collectors.brave_search_collector import BraveSearchCollector

def enhanced_data_collection(topic):
    """增强的数据收集，包含Brave搜索"""
    all_results = {}
    
    # Brave搜索
    brave_collector = BraveSearchCollector()
    if brave_collector.has_api_key:
        brave_results = brave_collector.get_comprehensive_research(topic)
        all_results['brave'] = brave_results
        print(f"Brave搜索获得 {brave_results['total_count']} 条结果")
    
    # 合并其他搜索源...
    return all_results
```

## API限制和配额

### 配额限制

- **免费层**: 每月2,000次搜索请求
- **付费层**: 根据订阅计划提供更高配额

### 速率限制

- 建议在请求间添加100ms延迟
- 避免短时间内大量并发请求

## 最佳实践

### 1. 错误处理

```python
try:
    results = brave_collector.search(query)
    if not results:
        print("搜索未返回结果")
except Exception as e:
    print(f"Brave搜索出错: {e}")
    # 使用备用搜索方法
```

### 2. 结果缓存

```python
import json
from datetime import datetime

def cache_search_results(topic, results):
    cache_data = {
        'topic': topic,
        'timestamp': datetime.now().isoformat(),
        'results': results
    }
    with open(f'brave_cache_{topic}.json', 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
```

### 3. 搜索优化

```python
# 使用更具体的搜索词
specific_query = f"{topic} 2024 最新发展"

# 组合多个搜索策略
search_strategies = [
    f"{topic} 新闻",
    f"{topic} research",
    f"{topic} industry report"
]
```

## 与其他搜索引擎对比

| 特性 | Brave搜索 | Google搜索 | Tavily搜索 |
|------|-----------|------------|------------|
| 独立性 | ✅ 完全独立 | ❌ 依赖Google | ✅ 独立 |
| 隐私保护 | ✅ 强调隐私 | ⚠️ 数据收集 | ✅ 隐私友好 |
| 免费配额 | 2,000/月 | 100/天 | 1,000/月 |
| 本地搜索 | ✅ 支持 | ✅ 支持 | ❌ 不支持 |
| 时间过滤 | ✅ 多种选项 | ✅ 支持 | ⚠️ 有限支持 |
| 语言支持 | ✅ 多语言 | ✅ 多语言 | ✅ 多语言 |

## 故障排除

### 常见问题

**Q: API返回401错误**
A: 检查API密钥是否正确配置，确保在环境变量中设置了`BRAVE_SEARCH_API_KEY`

**Q: 搜索结果为空**
A: 可能的原因：
- 搜索查询过于具体
- 时间过滤参数过于严格
- API配额已用完

**Q: 超出API配额限制**
A: 解决方案：
- 升级到付费计划
- 实施搜索结果缓存
- 优化搜索频率

### 调试模式

启用详细日志输出：

```python
import logging

logging.basicConfig(level=logging.DEBUG)
brave_collector = BraveSearchCollector()
```

## 总结

Brave搜索API的集成为您的报告生成系统带来：

- ✅ **多样化信息源**: 独立于Google的搜索结果
- ✅ **隐私保护**: 注重用户数据隐私
- ✅ **全面功能**: 支持网络、新闻、本地等多种搜索
- ✅ **易于集成**: 与现有系统无缝集成
- ✅ **成本效益**: 提供免费层级供测试使用

通过结合Brave搜索与其他搜索引擎（Google、Tavily等），您可以获得更全面、更多样化的搜索结果，提高报告内容的质量和覆盖面。

---

运行示例脚本查看详细的集成演示：
```bash
python example_google_search_integration.py
``` 