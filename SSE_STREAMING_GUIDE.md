# MCP Server-Sent Events (SSE) 流式响应实现指南

## 概述

您的MCP服务器现在已经完全实现了符合JSON-RPC 2.0规范的Server-Sent Events流式响应功能。这个实现包括：

- ✅ **进度更新消息** - 实时反馈任务执行进度
- ✅ **模型用量消息** - 跟踪AI模型的Token消耗
- ✅ **最终成功结果** - 任务完成时返回结构化结果
- ✅ **错误信息** - 任务失败时的详细错误报告

## 消息格式规范

### 1. 进度更新消息

符合规范的进度更新消息格式：

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/message",
  "params": {
    "level": "info",
    "data": {
      "msg": {
        "status": "generating_sections",
        "message": "完成教学目标的生成任务",
        "details": {
          "id": 0,
          "name": "教学目标",
          "content": "## 一、教学目标\n\n- 通过案例分析..."
        }
      }
    },
    "extra": null
  }
}
```

### 2. 模型用量消息

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/message",
  "params": {
    "data": {
      "msg": {
        "type": "model_usage",
        "data": {
          "model_provider": "doubao",
          "model_name": "doubao-1-5-pro-32k-250115",
          "input_tokens": 560,
          "output_tokens": 830
        }
      }
    }
  }
}
```

### 3. 最终成功结果

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"status\":\"completed\",\"task\":\"生成报告\"...}"
      }
    ],
    "structuredContent": {
      "status": "completed",
      "task": "生成AI Agent领域报告",
      "report_content": "# 完整报告内容...",
      "metadata": {
        "topic": "AI Agent",
        "sections_count": 5,
        "final_quality_score": 8.2
      }
    },
    "isError": false
  }
}
```

### 4. 错误信息

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": {
      "type": "report_generation_failed",
      "message": "报告生成模型未能返回有效内容。"
    }
  }
}
```

## 服务器端点

### 主要服务器
- **MCP服务器**: `http://localhost:8000/mcp` (FastMCP)
- **SSE服务器**: `http://localhost:8001` (FastAPI)

### SSE流式端点
- **POST** `/mcp/streaming/orchestrator` - 启动流式报告生成
- **GET** `/mcp/streaming/sessions/{session_id}` - 查询会话状态

## 使用方法

### 1. 启动服务器

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务器（同时启动MCP和SSE服务）
python main.py
```

服务器启动后会看到：
```
🚀 启动MCP服务器...
📡 FastAPI SSE服务器已启动 (端口8001)
```

### 2. 测试流式响应

使用提供的测试客户端：

```bash
python test_sse_client.py
```

### 3. 手动调用SSE端点

```bash
curl -X POST http://localhost:8001/mcp/streaming/orchestrator \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "task": "生成AI Agent领域最近一周的行业重大事件报告",
    "task_type": "news_report",
    "kwargs": {
      "days": 7,
      "quality_threshold": 7.0,
      "max_iterations": 2,
      "auto_confirm": true
    }
  }'
```

### 4. 在Cursor中使用MCP工具

配置Cursor的MCP客户端后，可以直接调用：

```
orchestrator_mcp_streaming("生成AI Agent行业报告", task_type="news_report")
```

## 流式响应流程

1. **会话启动** - 返回session_id
2. **意图识别** - 分析任务意图
3. **大纲生成** - 创建报告结构
4. **内容检索** - 并行搜索相关信息
5. **质量评估** - 5维度质量分析
6. **内容生成** - 逐章节生成内容（带实时进度）
7. **摘要生成** - 创建执行摘要
8. **报告组装** - 最终报告组装
9. **会话结束** - 返回完整结果

## 主要特性

### 🔄 实时进度反馈
- 7步骤工作流程的实时进度
- 每个章节生成的详细进度
- 质量评估的5维度评分

### 📊 模型用量跟踪
- Token消耗统计
- 模型提供商和名称
- 输入/输出Token计数

### 🎯 智能内容生成
- AI意图识别
- 5维度质量评估（相关性、深度、准确性、完整性、时效性）
- 智能缺口分析和补充搜索
- 专业内容撰写

### 🔧 错误处理
- 完善的错误捕获和报告
- 符合JSON-RPC 2.0错误格式
- 详细的错误类型和消息

## 配置选项

### 任务参数
- `task`: 任务描述
- `task_type`: 任务类型 (`news_report`, `research_report`, `industry_analysis`, `auto`)
- `days`: 搜索时间范围（默认7天）
- `quality_threshold`: 质量门槛（默认7.0/10）
- `max_iterations`: 最大迭代次数（默认3）
- `auto_confirm`: 自动确认大纲（默认true）

### 环境变量
确保在`.env`文件中配置必要的API密钥：
```
TAVILY_API_KEY=your_key
BRAVE_API_KEY=your_key
GOOGLE_API_KEY=your_key
OPENAI_API_KEY=your_key
```

## 故障排除

### 常见问题

1. **连接失败**
   - 确保服务器正在运行
   - 检查端口8000和8001是否可用

2. **搜索服务不可用**
   - 检查API密钥配置
   - 验证网络连接

3. **模型调用失败**
   - 确认LLM API密钥正确
   - 检查模型服务可用性

### 日志查看
服务器会输出详细的执行日志：
```
📡 [流式进度] task_started: 开始执行任务
🤖 AI成功生成 3 个针对性查询
📊 [第1轮评估] 5维度质量分析: 相关性8.5/10
```

## 技术架构

- **FastMCP**: 主MCP服务器框架
- **FastAPI**: SSE流式响应服务器
- **ThreadPoolExecutor**: 并行搜索和处理
- **JSON-RPC 2.0**: 标准消息协议
- **Server-Sent Events**: 流式数据传输

这个实现完全符合您提供的SSE消息格式规范，提供了专业级的流式报告生成能力。

