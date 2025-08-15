# Search MCP 完整部署与使用指南

## 🎯 概述

Search MCP 提供三种主要的调用方式，适应不同的使用场景：

1. **MCP协议调用** - 在支持MCP的AI客户端中使用
2. **HTTP API调用** - 作为独立服务供其他系统调用
3. **Python库调用** - 直接在Python项目中导入使用

## 🚀 快速开始

### 方式一：MCP协议调用（推荐）

#### 步骤1：发布到GitHub
```bash
# 将您的项目推送到GitHub
git add .
git commit -m "Initial commit"
git push origin main
```

#### 步骤2：用户安装配置

**Claude Desktop配置:**
```json
{
  "mcpServers": {
    "search-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/YOUR_USERNAME/search_mcp.git", "search-mcp"],
      "env": {
        "TAVILY_API_KEY": "用户的API密钥",
        "BRAVE_SEARCH_API_KEY": "用户的API密钥"
      }
    }
  }
}
```

**Cursor/VSCode配置:**
```json
{
  "mcpServers": {
    "search-mcp": {
      "name": "统一搜索服务",
      "command": "python",
      "args": ["-m", "search_mcp.main"],
      "cwd": "/path/to/search_mcp",
      "env": {
        "TAVILY_API_KEY": "用户的API密钥"
      }
    }
  }
}
```

#### 步骤3：用户使用
```
请使用search-mcp工具搜索"人工智能最新发展"相关信息
```

### 方式二：HTTP API服务部署

#### 选项A：Docker部署（推荐）

**用户操作步骤：**
```bash
# 1. 克隆项目
git clone https://github.com/YOUR_USERNAME/search_mcp.git
cd search_mcp

# 2. 创建环境配置文件
cat > .env << EOF
TAVILY_API_KEY=your_tavily_api_key
BRAVE_SEARCH_API_KEY=your_brave_api_key
GOOGLE_SEARCH_API_KEY=your_google_api_key
GOOGLE_SEARCH_CX=your_google_cx_id
NEWSAPI_KEY=your_newsapi_key
EOF

# 3. 启动服务
docker-compose up -d

# 4. 验证服务
curl http://localhost:8080/health
```

#### 选项B：云平台部署

**Railway部署:**
```bash
# 用户操作
railway login
railway init
railway up

# 设置环境变量
railway variables set TAVILY_API_KEY=your_key
railway variables set BRAVE_SEARCH_API_KEY=your_key
```

**Heroku部署:**
```bash
# 用户操作
heroku create your-search-mcp
heroku config:set TAVILY_API_KEY=your_key
git push heroku main
```

#### HTTP API调用示例

**Python调用:**
```python
import requests

# 调用部署的服务
response = requests.post("http://your-server:8080/search/parallel", json={
    "queries": ["人工智能", "机器学习"],
    "max_results_per_query": 10
})

results = response.json()
```

**curl调用:**
```bash
curl -X POST "http://your-server:8080/search/category" \
  -H "Content-Type: application/json" \
  -d '{"queries": ["AI"], "category": "web"}'
```

### 方式三：Python库直接调用

#### 用户安装
```bash
# 从GitHub安装
pip install git+https://github.com/YOUR_USERNAME/search_mcp.git

# 或克隆后本地安装
git clone https://github.com/YOUR_USERNAME/search_mcp.git
cd search_mcp
pip install -e .
```

#### 使用示例
```python
from search_mcp.generators import SearchOrchestrator
from search_mcp.config import SearchConfig
import os

# 配置API密钥
os.environ["TAVILY_API_KEY"] = "your_api_key"
os.environ["BRAVE_SEARCH_API_KEY"] = "your_api_key"

# 创建搜索服务
config = SearchConfig()
orchestrator = SearchOrchestrator(config)

# 执行搜索
results = orchestrator.parallel_search(
    queries=["人工智能发展"],
    max_results_per_query=10
)

# 处理结果
for doc in results:
    print(f"标题: {doc.title}")
    print(f"来源: {doc.source}")
    print(f"链接: {doc.url}")
    print("---")
```

## 🔑 API密钥获取指南

### Tavily API
1. 访问 https://tavily.com
2. 注册账号并获取API密钥
3. 免费额度：1000次搜索/月

### Brave Search API
1. 访问 https://api.search.brave.com
2. 注册开发者账号
3. 免费额度：2000次查询/月

### Google Search API
1. 访问 Google Cloud Console
2. 启用Custom Search API
3. 创建搜索引擎ID (CX)
4. 免费额度：100次查询/天

### NewsAPI
1. 访问 https://newsapi.org
2. 注册获取免费API密钥
3. 免费额度：1000次请求/月

## 🛠️ 高级配置

### 生产环境优化

**配置文件 (production.env):**
```bash
# API密钥
TAVILY_API_KEY=your_key
BRAVE_SEARCH_API_KEY=your_key

# 性能优化
SEARCH_MAX_WORKERS=8
SEARCH_REQUEST_TIMEOUT=30
SEARCH_MAX_RESULTS_PER_QUERY=10

# 缓存配置
SEARCH_ENABLE_CACHE=true
SEARCH_CACHE_TTL=1800

# 日志配置
SEARCH_LOG_LEVEL=INFO
SEARCH_LOG_FILE=/var/log/search-mcp/app.log
```

### 负载均衡配置

**nginx.conf:**
```nginx
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
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

## 📊 监控与日志

### 健康检查
```bash
# 检查服务状态
curl http://localhost:8080/health

# 检查可用数据源
curl http://localhost:8080/sources
```

### 日志查看
```bash
# Docker环境
docker-compose logs -f search-mcp

# 本地环境
tail -f logs/search-mcp.log
```

## 🔧 故障排除

### 常见问题

**1. API密钥错误**
```bash
# 检查环境变量
echo $TAVILY_API_KEY

# 验证API密钥
curl -H "Authorization: Bearer $TAVILY_API_KEY" https://api.tavily.com/search
```

**2. 端口冲突**
```bash
# 检查端口占用
lsof -i :8080

# 修改端口
export PORT=8081
python main.py
```

**3. 依赖问题**
```bash
# 重新安装依赖
pip install --force-reinstall -e .
```

## 📈 性能优化建议

### 1. 并发配置
```python
# 根据服务器性能调整
max_workers = min(32, (cpu_count() + 4))
```

### 2. 缓存策略
```python
# 启用缓存减少API调用
enable_cache = True
cache_ttl = 3600  # 1小时
```

### 3. 超时设置
```python
# 合理设置超时时间
request_timeout = 30.0
search_timeout = 120.0
```

## 🚀 扩展开发

### 添加新的数据源
```python
class CustomCollector:
    def search(self, query, max_results=5):
        # 实现自定义搜索逻辑
        return results

# 在generators.py中注册
self.collectors['custom'] = CustomCollector()
```

### 自定义响应格式
```python
class CustomSearchResponse(BaseModel):
    results: List[Document]
    metadata: Dict[str, Any]
    custom_field: str
```

## 📄 许可与支持

- **许可证**: MIT License
- **GitHub**: https://github.com/YOUR_USERNAME/search_mcp
- **Issues**: 提交问题和建议
- **文档**: 查看README.md获取更多信息

---

## 📞 联系方式

如有问题或需要技术支持，请：
1. 查看GitHub Issues
2. 提交新的Issue
3. 参与Discussions讨论 