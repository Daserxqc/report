# Search MCP Server

## 🎯 概述

**Search MCP** 是一个基于 MCP (Model Context Protocol) 协议的统一搜索服务器。它整合了多个数据源的搜索能力，提供标准化的并行搜索接口，支持Web搜索、学术搜索、新闻搜索等多种数据类型。

## 🏗️ 技术架构

### 核心组件

- **SearchMCP** - 统一搜索系统，整合所有现有搜索收集器功能
- **Document** - 标准化文档数据结构
- **多数据源支持** - Tavily、Brave、Google、ArXiv、Academic、News等

### 特点

- ⚡ 内置线程池，自动并行执行
- 🔄 基于URL的智能去重机制  
- 📊 统一的Document数据结构
- 🛡️ 自动降级和错误恢复
- 🎯 按类别搜索支持

## 📁 项目结构

```
search_mcp/
├── README.md                    # 项目说明
├── pyproject.toml              # 项目配置
├── main.py                     # MCP服务器入口
├── src/                        # 核心源码目录
│   └── search_mcp/
│       ├── __init__.py         # 模块初始化
│       ├── config.py           # 配置管理
│       ├── models.py           # 数据模型
│       ├── generators.py       # 核心搜索逻辑
│       └── logger.py           # 日志配置
├── tests/                      # 测试目录
│   ├── __init__.py
│   └── test_mcp_server.py      # 完整测试文件
└── outputs/                    # 生成的搜索输出 (运行时创建)
```

## 🚀 快速开始

### 安装依赖

```bash
pip install -e .
```

### 环境配置

```bash
# 设置API密钥
export TAVILY_API_KEY="your_tavily_key"
export BRAVE_SEARCH_API_KEY="your_brave_key" 
export GOOGLE_SEARCH_API_KEY="your_google_key"
export GOOGLE_SEARCH_CX="your_google_cx"
export NEWSAPI_KEY="your_news_api_key"
```

### 启动MCP服务器

```bash
# 使用uvx启动
uvx search-mcp

# 或直接运行
python main.py
```

## 🔧 配置选项

### 客户端配置示例

#### Cherry Studio / trae 配置

```json
{
  "mcpServers": {
    "search-mcp": {
      "name": "搜索MCP服务",
      "description": "提供统一的多源搜索服务",
      "command": "uvx",
      "args": ["search-mcp"],
      "env": {
        "TAVILY_API_KEY": "your_tavily_key",
        "BRAVE_SEARCH_API_KEY": "your_brave_key",
        "GOOGLE_SEARCH_API_KEY": "your_google_key",
        "GOOGLE_SEARCH_CX": "your_google_cx",
        "NEWSAPI_KEY": "your_news_api_key"
      }
    }
  }
}
```

## 🛠️ 可用工具

### 1. parallel_search
并行搜索多个查询和数据源

参数:
- `queries` (list[str]): 搜索查询列表
- `sources` (list[str], 可选): 指定的数据源列表
- `max_results_per_query` (int): 每个查询的最大结果数，默认5
- `days_back` (int): 搜索多少天内的内容，默认7
- `max_workers` (int): 最大并行工作线程数，默认6

### 2. search_by_category
按类别搜索

参数:
- `queries` (list[str]): 搜索查询列表
- `category` (str): 搜索类别 ('web', 'academic', 'news')
- `max_results_per_query` (int): 每个查询的最大结果数，默认5
- `days_back` (int): 搜索多少天内的内容，默认7

### 3. search_with_fallback
带降级的搜索，如果首选数据源失败，自动使用备选数据源

参数:
- `queries` (list[str]): 搜索查询列表
- `preferred_sources` (list[str], 可选): 首选数据源
- `fallback_sources` (list[str], 可选): 备选数据源
- `max_results_per_query` (int): 每个查询的最大结果数，默认5

## 📊 使用示例

### 基本搜索
```
请使用parallel_search工具搜索"人工智能最新发展"相关信息
```

### 学术搜索
```
请使用search_by_category工具在学术类别中搜索"machine learning"
```

### 降级搜索
```
请使用search_with_fallback工具搜索"量子计算"，优先使用Tavily和Brave，备选Google和ArXiv
```

## 📝 数据格式

### Document 标准格式
```python
{
    "title": "文档标题",
    "content": "文档内容/摘要",
    "url": "文档链接",
    "source": "数据源名称",
    "source_type": "数据源类型 (web/academic/news)",
    "publish_date": "发布日期",
    "authors": ["作者列表"],
    "venue": "期刊/会议名称",
    "score": 0.95,
    "language": "zh"
}
```

## 🚨 注意事项

- 搜索任务可能需要较长时间完成，请耐心等待
- 确保API密钥有足够的配额
- 某些数据源可能有访问限制
- 结果会自动去重，避免重复内容

## 🔍 故障排除

### 常见问题

1. **API密钥错误**: 确保API密钥正确且有效
2. **网络连接问题**: 检查网络连接和防火墙设置  
3. **数据源不可用**: 确认数据源服务正常

### 调试模式

启用详细日志输出：
```bash
uvx search-mcp --verbose
```

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交Issue和Pull Request来改进这个项目！ 