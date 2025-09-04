# MCP服务部署和API调用指南

## 概述

您的理解完全正确！您只需要将MCP服务部署到一个公网可访问的服务器上，其他开发者就可以通过HTTP API调用您的报告生成服务。

## 部署步骤

### 1. 服务器部署

#### 云服务器部署（推荐）

```bash
# 1. 上传代码到服务器
scp -r report_generation/ user@your-server.com:/home/user/

# 2. 登录服务器
ssh user@your-server.com

# 3. 进入项目目录
cd /home/user/report_generation

# 4. 安装依赖
pip install -r requirements.txt
pip install -r requirements_api.txt

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，添加您的API密钥

# 6. 启动服务
python start_server.py
```

#### 修改配置以支持公网访问

在 `config_manager.py` 中，确保服务绑定到 `0.0.0.0`：

```python
# 已经配置好了，无需修改
FASTAPI_HOST = "0.0.0.0"  # 监听所有网络接口
FASTAPI_PORT = 8001
```

### 2. 域名和端口配置

假设您的服务器IP是 `123.456.789.0`，那么API端点将是：

- **基础URL**: `http://123.456.789.0:8001`
- **流式报告生成**: `POST http://123.456.789.0:8001/mcp/streaming/orchestrator`
- **简单报告生成**: `POST http://123.456.789.0:8001/mcp/orchestrator`
- **API文档**: `GET http://123.456.789.0:8001/docs`

如果有域名（如 `api.yourcompany.com`），则端点为：
- `POST https://api.yourcompany.com/mcp/streaming/orchestrator`

### 3. 防火墙配置

确保服务器防火墙开放8001端口：

```bash
# Ubuntu/Debian
sudo ufw allow 8001

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8001/tcp
sudo firewall-cmd --reload
```

## API调用示例

### 基本调用格式

其他开发者只需要向您的API端点发送HTTP POST请求：

```bash
curl -X POST "http://your-server.com:8001/mcp/orchestrator" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "生成AI行业最近一周的动态报告",
    "task_type": "industry_dynamics",
    "kwargs": {
      "days": 7,
      "quality_threshold": 0.8,
      "auto_confirm": true
    }
  }'
```

### 各语言调用示例

#### Python调用

```python
import requests
import json

# 您的API服务地址
API_BASE_URL = "http://your-server.com:8001"

def generate_report(task, task_type="industry_dynamics", **kwargs):
    url = f"{API_BASE_URL}/mcp/orchestrator"
    payload = {
        "task": task,
        "task_type": task_type,
        "kwargs": kwargs
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API调用失败: {response.status_code}")

# 使用示例
result = generate_report(
    task="生成AI行业最近一周的动态报告",
    days=7,
    quality_threshold=0.8
)
print(result)
```

#### JavaScript调用

```javascript
const API_BASE_URL = "http://your-server.com:8001";

async function generateReport(task, taskType = "industry_dynamics", options = {}) {
    const response = await fetch(`${API_BASE_URL}/mcp/orchestrator`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            task: task,
            task_type: taskType,
            kwargs: options
        })
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
}

// 使用示例
generateReport("生成AI行业最近一周的动态报告", "industry_dynamics", {
    days: 7,
    quality_threshold: 0.8
}).then(result => {
    console.log(result);
}).catch(error => {
    console.error('Error:', error);
});
```

#### Java调用

```java
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import com.fasterxml.jackson.databind.ObjectMapper;

public class ReportGenerator {
    private static final String API_BASE_URL = "http://your-server.com:8001";
    private final HttpClient client = HttpClient.newHttpClient();
    private final ObjectMapper mapper = new ObjectMapper();
    
    public String generateReport(String task, String taskType, Map<String, Object> kwargs) throws Exception {
        Map<String, Object> payload = Map.of(
            "task", task,
            "task_type", taskType,
            "kwargs", kwargs
        );
        
        String json = mapper.writeValueAsString(payload);
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(API_BASE_URL + "/mcp/orchestrator"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(json))
            .build();
            
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        
        if (response.statusCode() == 200) {
            return response.body();
        } else {
            throw new Exception("API调用失败: " + response.statusCode());
        }
    }
}
```

### 流式调用示例

对于需要实时进度的场景，可以使用流式端点：

```python
import requests
import json

def generate_streaming_report(task, task_type="industry_dynamics", **kwargs):
    url = f"{API_BASE_URL}/mcp/streaming/orchestrator"
    payload = {
        "task": task,
        "task_type": task_type,
        "kwargs": kwargs
    }
    
    response = requests.post(url, json=payload, stream=True)
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                try:
                    data = json.loads(line_str[6:])
                    if data['type'] == 'progress':
                        print(f"进度: {data['data']}")
                    elif data['type'] == 'result':
                        print(f"完成: {data['data']}")
                        return data['data']
                    elif data['type'] == 'error':
                        raise Exception(f"生成失败: {data['data']}")
                except json.JSONDecodeError:
                    continue

# 使用示例
result = generate_streaming_report(
    task="生成AI行业最近一周的动态报告",
    days=7
)
```

## API文档

部署后，其他开发者可以访问自动生成的API文档：

- **Swagger UI**: `http://your-server.com:8001/docs`
- **ReDoc**: `http://your-server.com:8001/redoc`

## 生产环境建议

### 1. 使用进程管理器

```bash
# 安装PM2
npm install -g pm2

# 启动服务
pm2 start "python start_server.py" --name mcp-service

# 设置开机自启
pm2 startup
pm2 save
```

### 2. 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name api.yourcompany.com;
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. HTTPS配置

```bash
# 使用Let's Encrypt获取SSL证书
sudo certbot --nginx -d api.yourcompany.com
```

## 监控和维护

### 健康检查端点

您的服务已经包含健康检查：
- `GET http://your-server.com:8001/health`

### 日志监控

```bash
# 查看服务日志
pm2 logs mcp-service

# 监控系统资源
pm2 monit
```

## 给其他开发者的使用说明

### API端点

**基础URL**: `http://your-server.com:8001`

#### 1. 简单报告生成
- **端点**: `POST /mcp/orchestrator`
- **说明**: 生成完整报告后返回结果

#### 2. 流式报告生成
- **端点**: `POST /mcp/streaming/orchestrator`
- **说明**: 实时返回生成进度和结果

### 请求格式

```json
{
  "task": "报告主题描述",
  "task_type": "报告类型",
  "kwargs": {
    "days": 7,
    "quality_threshold": 0.8,
    "max_iterations": 3,
    "auto_confirm": true
  }
}
```

### 支持的报告类型

- `industry_dynamics`: 行业动态报告
- `research_trends`: 研究趋势报告
- `market_insights`: 市场洞察报告
- `comprehensive_report`: 综合报告

### 响应格式

```json
{
  "success": true,
  "data": {
    "content": "报告内容...",
    "metadata": {
      "sources_count": 25,
      "generation_time": "2024-01-15T10:30:00Z"
    }
  }
}
```

## 总结

您只需要：

1. **部署服务**：将代码部署到云服务器，运行 `python start_server.py`
2. **配置网络**：确保8001端口可访问
3. **提供API地址**：告诉其他开发者您的API端点地址

其他开发者就可以直接调用您的API来生成报告，无需了解内部实现细节。您专注于维护和优化MCP工具本身即可。