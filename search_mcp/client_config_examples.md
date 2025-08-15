# Search MCP 客户端配置示例

## 🔧 MCP客户端配置

### 1. Claude Desktop 配置

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "search-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/your-username/search_mcp.git", "search-mcp"],
      "env": {
        "TAVILY_API_KEY": "your_tavily_api_key",
        "BRAVE_SEARCH_API_KEY": "your_brave_api_key",
        "GOOGLE_SEARCH_API_KEY": "your_google_api_key",
        "GOOGLE_SEARCH_CX": "your_google_cx_id",
        "NEWSAPI_KEY": "your_newsapi_key"
      }
    }
  }
}
```

### 2. Cursor/VSCode 配置

在项目的 `.mcp/config.json` 中添加：

```json
{
  "mcpServers": {
    "search-mcp": {
      "name": "统一搜索服务",
      "description": "提供多数据源并行搜索功能",
      "command": "python",
      "args": ["-m", "search_mcp.main"],
      "cwd": "/path/to/search_mcp",
      "env": {
        "TAVILY_API_KEY": "your_api_key",
        "BRAVE_SEARCH_API_KEY": "your_api_key"
      }
    }
  }
}
```

### 3. Cherry Studio 配置

```json
{
  "mcpServers": {
    "search-mcp": {
      "name": "搜索MCP服务",
      "description": "统一多源搜索",
      "command": "uvx",
      "args": ["search-mcp"],
      "env": {
        "TAVILY_API_KEY": "${TAVILY_API_KEY}",
        "BRAVE_SEARCH_API_KEY": "${BRAVE_SEARCH_API_KEY}"
      }
    }
  }
}
```

### 4. 本地安装方式

用户可以通过以下方式安装：

```bash
# 方式1: 从GitHub安装
pip install git+https://github.com/your-username/search_mcp.git

# 方式2: 使用uvx（推荐）
uvx --from git+https://github.com/your-username/search_mcp.git search-mcp

# 方式3: 克隆后本地安装
git clone https://github.com/your-username/search_mcp.git
cd search_mcp
pip install -e .
```

## 🔑 API密钥配置

用户需要自己申请以下API密钥：

### Tavily API
1. 访问 https://tavily.com
2. 注册账号并获取API密钥
3. 设置环境变量：`export TAVILY_API_KEY="your_key"`

### Brave Search API
1. 访问 https://api.search.brave.com
2. 注册开发者账号
3. 设置环境变量：`export BRAVE_SEARCH_API_KEY="your_key"`

### Google Search API
1. 访问 Google Cloud Console
2. 启用Custom Search API
3. 创建搜索引擎ID (CX)
4. 设置环境变量：
   ```bash
   export GOOGLE_SEARCH_API_KEY="your_key"
   export GOOGLE_SEARCH_CX="your_cx_id"
   ```

### NewsAPI
1. 访问 https://newsapi.org
2. 注册获取免费API密钥
3. 设置环境变量：`export NEWSAPI_KEY="your_key"`

## 🚀 使用示例

配置完成后，用户可以在AI客户端中这样使用：

```
请使用search-mcp工具搜索"人工智能最新发展"的相关信息
```

```
请使用search-mcp的search_by_category工具在学术类别中搜索"machine learning"
```

```
请使用search-mcp的parallel_search工具同时搜索多个关键词：["AI", "机器学习", "深度学习"]
``` 