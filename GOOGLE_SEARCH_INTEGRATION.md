# Google搜索API集成指南

## 概述

本指南介绍如何将Google Custom Search API作为新的搜索渠道集成到报告生成系统中，丰富数据来源和提高搜索覆盖面。

## 功能特性

### 🔍 多类型搜索支持
- **新闻搜索**: 获取最新的新闻报道和资讯
- **学术论文搜索**: 查找研究论文和学术资料  
- **行业报告搜索**: 收集行业分析和市场报告
- **通用搜索**: 全面的网络搜索结果

### 🚀 高级功能
- **时间过滤**: 支持按天数限制搜索范围
- **站点限制**: 可指定在特定网站内搜索
- **文件类型过滤**: 支持PDF、Word等文件类型搜索
- **多语言支持**: 中英文搜索结果支持
- **结果去重**: 自动去除重复的搜索结果

## 安装和配置

### 1. 获取Google Custom Search API密钥

#### 步骤1: 创建Google Cloud项目
1. 访问 [Google Cloud Console](https://console.developers.google.com/)
2. 创建新项目或选择现有项目
3. 启用 **Custom Search API**

#### 步骤2: 创建API密钥
1. 进入 **APIs & Services > Credentials**
2. 点击 **Create Credentials > API Key**
3. 复制生成的API密钥

#### 步骤3: 创建自定义搜索引擎
1. 访问 [Google Programmable Search Engine](https://cse.google.com/cse/)
2. 点击 **Add** 创建新的搜索引擎
3. 配置搜索范围:
   - 选择 "搜索整个网络"
   - 或添加特定网站域名
4. 获取搜索引擎ID (CX)

### 2. 配置环境变量

在您的 `.env` 文件中添加以下配置：

```bash
# Google搜索API配置
GOOGLE_SEARCH_API_KEY=您的Google搜索API密钥
GOOGLE_SEARCH_CX=您的自定义搜索引擎ID
```

### 3. 验证配置

运行测试脚本验证配置是否正确：

```bash
python example_google_search_integration.py
```

## 使用方法

### 基本使用

```python
from collectors.google_search_collector import GoogleSearchCollector

# 初始化收集器
google_collector = GoogleSearchCollector()

# 基本搜索
results = google_collector.search("人工智能", days_back=7, max_results=10)

# 打印结果
for result in results:
    print(f"标题: {result['title']}")
    print(f"内容: {result['content'][:100]}...")
    print(f"来源: {result['source']}")
    print(f"链接: {result['url']}")
```

### 多渠道集成

```python
from collectors.google_search_collector import GoogleSearchCollector
from collectors.tavily_collector import TavilyCollector
from collectors.news_collector import NewsCollector

def multi_channel_search(topic):
    """多渠道搜索整合"""
    results = {}
    
    # Google搜索
    google_collector = GoogleSearchCollector()
    if google_collector.has_api_key:
        results['google'] = google_collector.get_comprehensive_research(topic)
    
    # Tavily搜索 
    tavily_collector = TavilyCollector()
    if tavily_collector.has_api_key:
        results['tavily'] = tavily_collector.search(topic, max_results=10)
    
    # 新闻搜索
    news_collector = NewsCollector()
    results['news'] = news_collector.get_news_by_topic(topic)
    
    return results
```

## API限制和配额

Google Custom Search API配额：
- **免费层**: 每天100次搜索请求
- **付费层**: 每天最多10,000次搜索请求

## 集成到现有报告生成

要将Google搜索集成到现有的报告生成流程中，只需在您的报告生成脚本中添加：

```python
from collectors.google_search_collector import GoogleSearchCollector

# 在您的数据收集函数中
google_collector = GoogleSearchCollector()
if google_collector.has_api_key:
    google_results = google_collector.get_comprehensive_research(topic)
    # 将结果合并到现有数据收集流程中
```

## 故障排除

**常见问题：**
- API密钥无效：检查密钥是否正确配置
- 搜索结果为空：调整搜索查询或时间范围
- 超出配额：升级到付费层级或优化搜索频率

运行示例脚本查看详细的集成演示：
```bash
python example_google_search_integration.py
``` 