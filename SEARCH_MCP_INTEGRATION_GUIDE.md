# SearchMcp 集成指南

## 概述

SearchMcp (Search Model Context Protocol) 是一个统一的搜索系统，整合了现有六个agent中的所有搜索功能，提供标准化的并行搜索接口。

## 🏗️ 架构特点

### 核心优势
- **🎯 统一接口**: 所有数据源使用相同的API调用方式
- **⚡ 并行处理**: 内置线程池，自动并行执行多个搜索任务  
- **🔄 自动去重**: 基于URL的智能去重机制
- **📊 数据标准化**: 统一的Document数据结构
- **🛡️ 容错机制**: 自动降级和错误恢复
- **📈 易于扩展**: 简单添加新的数据源

### 支持的数据源
- **Web搜索**: Tavily, Brave, Google Custom Search
- **学术搜索**: ArXiv, Semantic Scholar, IEEE, Springer
- **新闻搜索**: News API, RSS Feeds, Google News

## 🚀 快速开始

### 基础使用

```python
from collectors.search_mcp import SearchMcp

# 初始化SearchMcp
search_mcp = SearchMcp()

# 执行并行搜索
results = search_mcp.parallel_search(
    queries=["生成式AI", "ChatGPT应用", "大模型发展"],
    max_results_per_query=5,
    days_back=30,
    max_workers=6
)

# 处理结果
for doc in results:
    print(f"标题: {doc.title}")
    print(f"来源: {doc.source} ({doc.source_type})")
    print(f"内容: {doc.content[:100]}...")
```

### 按类别搜索

```python
# 只搜索学术内容
academic_results = search_mcp.search_by_category(
    queries=["machine learning", "deep learning"],
    category='academic',
    max_results_per_query=3
)

# 只搜索新闻内容
news_results = search_mcp.search_by_category(
    queries=["AI行业动态", "科技新闻"],
    category='news',
    max_results_per_query=5,
    days_back=7
)
```

### 降级搜索

```python
# 首选网络搜索，如果结果不足则使用学术搜索补充
results = search_mcp.search_with_fallback(
    queries=["量子计算", "quantum computing"],
    preferred_sources=['tavily', 'brave'],
    fallback_sources=['arxiv', 'academic'],
    max_results_per_query=3
)
```

## 🔧 现有Agent集成示例

### 1. generate_outline_report.py 集成

**原始代码 (OutlineDataCollector):**
```python
# 原来需要管理多个收集器
class OutlineDataCollector:
    def __init__(self, llm_processor=None):
        self.tavily_collector = TavilyCollector()
        self.brave_collector = BraveSearchCollector()
        # ... 更多初始化代码
        
    def _execute_single_query(self, query):
        # 手动管理多个收集器
        search_results = []
        for name, collector in self.collectors.items():
            # ... 复杂的搜索逻辑
```

**使用SearchMcp后:**
```python
from collectors.search_mcp import SearchMcp

class OutlineDataCollector:
    def __init__(self, llm_processor=None):
        self.search_mcp = SearchMcp()  # 一行搞定！
        
    def parallel_collect_main_sections(self, outline_structure, topic, target_audience="通用", max_workers=4):
        # 为每个章节生成查询
        all_queries = []
        for section_title, section_info in outline_structure.items():
            queries = self._generate_section_queries(topic, section_title, section_info, target_audience)
            all_queries.extend(queries)
        
        # 使用SearchMcp并行搜索
        raw_results = self.search_mcp.parallel_search(
            queries=all_queries,
            max_results_per_query=5,
            days_back=7,
            max_workers=max_workers
        )
        
        # 按章节组织结果
        sections_data = self._organize_results_by_section(raw_results, outline_structure)
        return sections_data
```

### 2. generate_news_report_parallel.py 集成

**原始代码:**
```python
class ParallelDataCollector:
    def parallel_comprehensive_search(self, topic, days=7, max_workers=3):
        # 复杂的多收集器管理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            if 'brave' in self.collectors:
                futures.append(executor.submit(self._execute_brave_search, topic, days))
            # ... 更多手动提交
```

**使用SearchMcp后:**
```python
from collectors.search_mcp import SearchMcp

class ParallelDataCollector:
    def __init__(self):
        self.search_mcp = SearchMcp()
    
    def parallel_comprehensive_search(self, topic, days=7, max_workers=3):
        # 生成多角度查询
        queries = [
            f"{topic} 最新动态",
            f"{topic} 行业分析", 
            f"{topic} 发展趋势",
            f"{topic} 市场表现"
        ]
        
        # 一行代码完成并行搜索
        results = self.search_mcp.parallel_search(
            queries=queries,
            max_results_per_query=5,
            days_back=days,
            max_workers=max_workers
        )
        
        return results
```

### 3. intent_search_agent.py 集成

**原始代码:**
```python
class IntentSearchAgent:
    def parallel_content_search(self, intent_data, max_results=5):
        # 手动管理多个搜索收集器
        results = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            for collector_name, collector in self.collectors.items():
                # ... 复杂的并行逻辑
        
        # 手动去重
        return self._deduplicate_results(results)
```

**使用SearchMcp后:**
```python
from collectors.search_mcp import SearchMcp

class IntentSearchAgent:
    def __init__(self):
        self.search_mcp = SearchMcp()
    
    def parallel_content_search(self, intent_data, max_results=5):
        queries = intent_data.get('search_queries', [])
        
        # SearchMcp自动处理并行和去重
        results = self.search_mcp.parallel_search(
            queries=queries,
            max_results_per_query=max_results,
            days_back=7
        )
        
        return results
```

## 📊 Document数据结构

SearchMcp返回标准化的Document对象：

```python
@dataclass
class Document:
    title: str              # 标题
    content: str            # 内容摘要
    url: str               # 链接
    source: str            # 数据源 (tavily, brave, arxiv等)
    source_type: str       # 类型 (web, academic, news)
    publish_date: str      # 发布日期 (可选)
    authors: List[str]     # 作者列表 (可选)
    venue: str             # 期刊/会议名 (可选)
    score: float           # 相关性评分 (可选)
    language: str          # 语言 (可选)
    
    def to_dict(self) -> Dict    # 转换为字典
    @property
    def domain(self) -> str      # 提取域名
```

## 🔄 迁移步骤

### 步骤1: 替换收集器初始化
```python
# 原来
self.tavily_collector = TavilyCollector()
self.brave_collector = BraveSearchCollector()
# ... 更多收集器

# 现在
from collectors.search_mcp import SearchMcp
self.search_mcp = SearchMcp()
```

### 步骤2: 替换搜索调用
```python
# 原来 - 手动管理多个收集器
results = []
for collector in self.collectors.values():
    try:
        collector_results = collector.search(query)
        results.extend(collector_results)
    except Exception as e:
        print(f"搜索失败: {e}")

# 现在 - 一行调用
results = self.search_mcp.parallel_search(
    queries=[query],
    max_results_per_query=10
)
```

### 步骤3: 更新数据处理逻辑
```python
# 现在所有结果都是标准化的Document对象
for doc in results:
    title = doc.title
    content = doc.content
    url = doc.url
    source_type = doc.source_type  # 'web', 'academic', 'news'
    authors = doc.authors         # 自动处理的作者列表
```

## 🎛️ 高级配置

### 自定义数据源选择
```python
# 只使用特定数据源
results = search_mcp.parallel_search(
    queries=queries,
    sources=['tavily', 'arxiv'],  # 只使用这两个数据源
    max_results_per_query=5
)

# 检查可用数据源
available = search_mcp.get_available_sources()
print(available)
# {'web': ['tavily', 'brave'], 'academic': ['arxiv'], 'news': ['news']}
```

### 性能调优
```python
# 调整并行度
results = search_mcp.parallel_search(
    queries=queries,
    max_workers=8,  # 增加并行线程数
    max_results_per_query=3  # 减少每个查询的结果数
)

# 调整搜索时间范围
results = search_mcp.parallel_search(
    queries=queries,
    days_back=365,  # 搜索一年内的内容
)
```

## 🧪 测试和验证

运行测试文件验证集成效果：

```bash
python test_search_mcp.py
```

测试包括：
- 基础并行搜索功能
- 按类别搜索测试
- 降级搜索机制
- Document标准化验证
- 集成潜力演示

## 🔮 未来扩展

### 添加新数据源
```python
# 在SearchMcp中添加新的收集器
class SearchMcp:
    def _initialize_collectors(self):
        # 现有收集器...
        
        # 添加新的收集器
        try:
            new_collector = NewDataSourceCollector()
            if new_collector.has_api_key:
                self.collectors['new_source'] = new_collector
                print("✅ 新数据源收集器已启用")
        except Exception as e:
            print(f"⚠️ 新数据源收集器初始化失败: {str(e)}")
```

### 异步版本支持
未来可以添加异步版本的搜索方法：

```python
async def async_parallel_search(self, queries: List[str]) -> List[Document]:
    # 使用aiohttp进行异步搜索
    pass
```

## 📞 支持和反馈

如果在集成过程中遇到问题，请：

1. 检查API密钥配置
2. 运行测试文件验证功能
3. 查看控制台输出的详细日志
4. 参考现有agent的集成示例

SearchMcp设计为向后兼容，可以逐步迁移现有的搜索逻辑，不需要一次性重写所有代码。 