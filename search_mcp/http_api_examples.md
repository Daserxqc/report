# Search MCP HTTP API 调用示例

## 🌐 HTTP API 服务部署

### 1. 本地部署

```bash
# 启动HTTP API服务
cd search_mcp
python main.py

# 服务将运行在 http://localhost:8080
```

### 2. 云服务器部署

#### 使用Docker部署

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

# 安装依赖
RUN pip install -e .

# 暴露端口
EXPOSE 8080

# 启动服务
CMD ["python", "main.py"]
```

```bash
# 构建和运行
docker build -t search-mcp .
docker run -p 8080:8080 -e TAVILY_API_KEY="your_key" search-mcp
```

#### 使用云平台部署

**Railway 部署:**
```bash
# 安装Railway CLI
npm install -g @railway/cli

# 部署
railway login
railway init
railway up
```

**Heroku 部署:**
```bash
# 创建Procfile
echo "web: python main.py" > Procfile

# 部署
heroku create your-search-mcp
heroku config:set TAVILY_API_KEY="your_key"
git push heroku main
```

## 📡 HTTP API 调用方式

### 1. Python 调用示例

```python
import requests
import json

class SearchMCPClient:
    def __init__(self, base_url="http://your-server:8080"):
        self.base_url = base_url
    
    def parallel_search(self, queries, sources=None, max_results=5):
        """并行搜索"""
        payload = {
            "queries": queries,
            "sources": sources,
            "max_results_per_query": max_results,
            "days_back": 7,
            "max_workers": 6
        }
        
        response = requests.post(
            f"{self.base_url}/search/parallel",
            json=payload,
            timeout=60
        )
        
        return response.json()
    
    def search_by_category(self, queries, category="web", max_results=5):
        """按类别搜索"""
        payload = {
            "queries": queries,
            "category": category,
            "max_results_per_query": max_results,
            "days_back": 7
        }
        
        response = requests.post(
            f"{self.base_url}/search/category",
            json=payload,
            timeout=60
        )
        
        return response.json()
    
    def quick_search(self, query, category="web", max_results=5):
        """快速搜索"""
        params = {
            "q": query,
            "category": category,
            "max_results": max_results
        }
        
        response = requests.get(
            f"{self.base_url}/search/quick",
            params=params,
            timeout=30
        )
        
        return response.json()

# 使用示例
client = SearchMCPClient("http://your-server:8080")

# 并行搜索
results = client.parallel_search(
    queries=["人工智能", "机器学习"],
    sources=["tavily", "brave"],
    max_results=10
)

# 学术搜索
academic_results = client.search_by_category(
    queries=["machine learning"],
    category="academic",
    max_results=15
)

# 快速搜索
quick_results = client.quick_search("AI发展趋势")
```

### 2. JavaScript/Node.js 调用示例

```javascript
class SearchMCPClient {
    constructor(baseUrl = "http://your-server:8080") {
        this.baseUrl = baseUrl;
    }
    
    async parallelSearch(queries, sources = null, maxResults = 5) {
        const payload = {
            queries: queries,
            sources: sources,
            max_results_per_query: maxResults,
            days_back: 7,
            max_workers: 6
        };
        
        const response = await fetch(`${this.baseUrl}/search/parallel`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        return await response.json();
    }
    
    async searchByCategory(queries, category = "web", maxResults = 5) {
        const payload = {
            queries: queries,
            category: category,
            max_results_per_query: maxResults,
            days_back: 7
        };
        
        const response = await fetch(`${this.baseUrl}/search/category`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        return await response.json();
    }
    
    async quickSearch(query, category = "web", maxResults = 5) {
        const params = new URLSearchParams({
            q: query,
            category: category,
            max_results: maxResults
        });
        
        const response = await fetch(`${this.baseUrl}/search/quick?${params}`);
        return await response.json();
    }
}

// 使用示例
const client = new SearchMCPClient("http://your-server:8080");

// 并行搜索
const results = await client.parallelSearch(
    ["人工智能", "机器学习"],
    ["tavily", "brave"],
    10
);

// 学术搜索
const academicResults = await client.searchByCategory(
    ["machine learning"],
    "academic",
    15
);
```

### 3. curl 调用示例

```bash
# 并行搜索
curl -X POST "http://your-server:8080/search/parallel" \
  -H "Content-Type: application/json" \
  -d '{
    "queries": ["人工智能", "机器学习"],
    "sources": ["tavily", "brave"],
    "max_results_per_query": 10,
    "days_back": 7,
    "max_workers": 6
  }'

# 按类别搜索
curl -X POST "http://your-server:8080/search/category" \
  -H "Content-Type: application/json" \
  -d '{
    "queries": ["machine learning"],
    "category": "academic",
    "max_results_per_query": 15,
    "days_back": 7
  }'

# 快速搜索
curl "http://your-server:8080/search/quick?q=AI发展趋势&category=web&max_results=5"

# 健康检查
curl "http://your-server:8080/health"

# 获取可用数据源
curl "http://your-server:8080/sources"
```

## 🔧 客户端SDK示例

### Python SDK包装

```python
# search_mcp_sdk.py
import requests
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class SearchResult:
    title: str
    content: str
    url: str
    source: str
    source_type: str
    publish_date: Optional[str] = None

class SearchMCPSDK:
    """Search MCP Python SDK"""
    
    def __init__(self, base_url: str, timeout: int = 60):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    def search(self, 
               queries: List[str], 
               category: str = "web",
               max_results: int = 5) -> List[SearchResult]:
        """简化的搜索接口"""
        
        response = requests.post(
            f"{self.base_url}/search/category",
            json={
                "queries": queries,
                "category": category,
                "max_results_per_query": max_results
            },
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Search failed: {response.text}")
        
        data = response.json()
        if not data["success"]:
            raise Exception(f"Search failed: {data['message']}")
        
        # 转换为SearchResult对象
        results = []
        for item in data["data"]:
            results.append(SearchResult(
                title=item["title"],
                content=item["content"],
                url=item["url"],
                source=item["source"],
                source_type=item["source_type"],
                publish_date=item.get("publish_date")
            ))
        
        return results

# 使用示例
sdk = SearchMCPSDK("http://your-server:8080")
results = sdk.search(["人工智能"], category="web", max_results=10)

for result in results:
    print(f"标题: {result.title}")
    print(f"来源: {result.source}")
    print(f"链接: {result.url}")
    print("---")
```

## 🚀 部署建议

### 1. 生产环境配置

```python
# production_config.py
import os
from search_mcp.config import SearchConfig

def get_production_config():
    return SearchConfig(
        # API密钥从环境变量读取
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        brave_search_api_key=os.getenv("BRAVE_SEARCH_API_KEY"),
        
        # 生产环境优化
        max_workers=8,
        request_timeout=30.0,
        enable_cache=True,
        cache_ttl=1800,  # 30分钟
        
        # 日志配置
        log_level="INFO",
        enable_file_logging=True,
        log_file_path="/var/log/search-mcp/app.log"
    )
```

### 2. 负载均衡配置

```nginx
# nginx.conf
upstream search_mcp {
    server 127.0.0.1:8080;
    server 127.0.0.1:8081;
    server 127.0.0.1:8082;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://search_mcp;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }
}
``` 