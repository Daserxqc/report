#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web服务模块 - 提供FastAPI HTTP端点和SSE流式支持

本模块包含:
- FastAPI应用配置
- SSE流式端点
- 任务类型检测
- 流式报告生成
- 会话管理
"""

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import time
import uuid
import json
from typing import Dict, Any
from datetime import datetime

# 导入必要的模块
from streaming import StreamingProgressReporter
from mcp_tools import MCPToolRegistry

class WebServer:
    """Web服务器类"""
    
    def __init__(self, tool_registry: MCPToolRegistry):
        self.tool_registry = tool_registry
        self.app = FastAPI(title="MCP Server with SSE Support")
        self.streaming_sessions = {}
        self._setup_middleware()
        self._setup_routes()
    
    def _setup_middleware(self):
        """设置中间件"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.get("/health")
        async def health_check():
            """健康检查端点"""
            return {"status": "ok", "message": "FastAPI SSE服务器运行正常"}
        
        @self.app.post("/mcp/streaming/orchestrator")
        async def streaming_orchestrator_endpoint(request_data: dict):
            """流式调度器端点 - 返回SSE流式响应"""
            try:
                task = request_data.get('task', '')
                session_id = str(uuid.uuid4())
                
                if not task:
                    # 返回错误的SSE流
                    def error_generator():
                        error_data = {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "error": {
                                "code": -32602,
                                "message": "Invalid params",
                                "data": {
                                    "type": "invalid_task",
                                    "message": "任务描述不能为空"
                                }
                            }
                        }
                        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                    
                    return StreamingResponse(
                        error_generator(),
                        media_type="text/event-stream",
                        headers={
                            "Cache-Control": "no-cache",
                            "Connection": "keep-alive",
                            "Access-Control-Allow-Origin": "*"
                        }
                    )
                
                # 创建流式会话
                self.streaming_sessions[session_id] = {
                    "status": "running",
                    "task": task,
                    "start_time": datetime.now().isoformat(),
                    "messages": [],
                    "result": None,
                    "error": None
                }
                
                # 创建SSE流生成器
                def sse_generator():
                    try:
                        # 发送会话开始消息
                        session_start = {
                            "jsonrpc": "2.0",
                            "method": "session/started",
                            "params": {
                                "session_id": session_id,
                                "task": task,
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                        yield f"data: {json.dumps(session_start, ensure_ascii=False)}\n\n"
                        
                        # 创建实时SSE流式Reporter
                        class RealTimeSSEReporter(StreamingProgressReporter):
                            def __init__(self, session_id, generator_ref):
                                super().__init__(session_id)
                                self.generator_ref = generator_ref
                                self.message_queue = []
                            
                            def report_progress(self, status: str, message: str, details: dict = None, progress_percentage: float = None):
                                # 生成符合规范的进度更新消息
                                mcp_update = {
                                    "jsonrpc": "2.0",
                                    "method": "notifications/message",
                                    "params": {
                                        "level": "info",
                                        "data": {
                                            "msg": {
                                                "status": status,
                                                "message": message,
                                                "details": details or {}
                                            }
                                        },
                                        "extra": None
                                    }
                                }
                                self.message_queue.append(mcp_update)
                                return json.dumps(mcp_update, ensure_ascii=False)
                            
                            def report_model_usage(self, model_provider: str, model_name: str, input_tokens: int, output_tokens: int, cost_estimate: float = None):
                                # 生成符合规范的模型用量消息
                                mcp_usage = {
                                    "jsonrpc": "2.0",
                                    "method": "notifications/message",
                                    "params": {
                                        "data": {
                                            "msg": {
                                                "type": "model_usage",
                                                "data": {
                                                    "model_provider": model_provider,
                                                    "model_name": model_name,
                                                    "input_tokens": input_tokens,
                                                    "output_tokens": output_tokens
                                                }
                                            }
                                        }
                                    }
                                }
                                self.message_queue.append(mcp_usage)
                                return json.dumps(mcp_usage, ensure_ascii=False)
                            
                            def report_error(self, error_message: str, error_code: int = -32603):
                                # 生成符合规范的错误消息
                                mcp_error = {
                                    "jsonrpc": "2.0",
                                    "id": 1,
                                    "error": {
                                        "code": error_code,
                                        "message": "Internal error",
                                        "data": {
                                            "type": "execution_error",
                                            "message": error_message
                                        }
                                    }
                                }
                                self.message_queue.append(mcp_error)
                                return json.dumps(mcp_error, ensure_ascii=False)
                            
                            def get_and_clear_messages(self):
                                messages = self.message_queue.copy()
                                self.message_queue.clear()
                                return messages
                        
                        reporter = RealTimeSSEReporter(session_id, sse_generator)
                        
                        # 检测任务类型
                        task_type = self._detect_task_type(task)
                        
                        # 在后台线程中执行任务
                        import threading
                        result_container = {'result': None, 'error': None, 'completed': False}
                        
                        def execute_task():
                            try:
                                if task_type in ['comprehensive_search', 'parallel_search']:
                                    result_container['result'] = self._generate_single_mcp_stream(task, task_type, reporter, **request_data.get('kwargs', {}))
                                else:
                                    result_container['result'] = self._generate_full_report_stream(task, reporter, **request_data.get('kwargs', {}))
                            except Exception as e:
                                result_container['error'] = str(e)
                                reporter.report_error(f"报告生成失败: {str(e)}")
                            finally:
                                result_container['completed'] = True
                        
                        # 启动任务执行线程
                        task_thread = threading.Thread(target=execute_task)
                        task_thread.start()
                        
                        # 实时发送消息
                        while not result_container['completed']:
                            # 获取并发送新消息
                            messages = reporter.get_and_clear_messages()
                            for msg in messages:
                                yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
                            
                            time.sleep(0.5)  # 检查间隔
                        
                        # 发送剩余消息
                        messages = reporter.get_and_clear_messages()
                        for msg in messages:
                            yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
                        
                        # 等待任务完成
                        task_thread.join()
                        
                        if result_container['error']:
                            # 更新会话状态为失败
                            self.streaming_sessions[session_id].update({
                                "status": "failed",
                                "error": result_container['error'],
                                "end_time": datetime.now().isoformat()
                            })
                        else:
                            # 发送最终成功结果
                            final_result = {
                                "jsonrpc": "2.0",
                                "id": 1,
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": json.dumps(result_container['result'], ensure_ascii=False)
                                        }
                                    ],
                                    "structuredContent": result_container['result'],
                                    "isError": False
                                }
                            }
                            yield f"data: {json.dumps(final_result, ensure_ascii=False)}\n\n"
                            
                            # 更新会话状态为完成
                            self.streaming_sessions[session_id].update({
                                "status": "completed",
                                "result": result_container['result'],
                                "end_time": datetime.now().isoformat()
                            })
                        
                    except Exception as e:
                        # 发送错误消息
                        error_data = {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "error": {
                                "code": -32603,
                                "message": "Internal error",
                                "data": {
                                    "type": "execution_error",
                                    "message": str(e)
                                }
                            }
                        }
                        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                        
                        # 更新会话状态
                        self.streaming_sessions[session_id].update({
                            "status": "failed",
                            "error": str(e),
                            "end_time": datetime.now().isoformat()
                        })
                
                return StreamingResponse(
                    sse_generator(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Access-Control-Allow-Origin": "*"
                    }
                )
                
            except Exception as e:
                # 返回错误的SSE流
                def error_generator():
                    error_data = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "error": {
                            "code": -32603,
                            "message": "Internal error",
                            "data": {
                                "type": "server_error",
                                "message": f"启动任务失败: {str(e)}"
                            }
                        }
                    }
                    yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                
                return StreamingResponse(
                    error_generator(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Access-Control-Allow-Origin": "*"
                    }
                )
        
        @self.app.get("/mcp/streaming/sessions/{session_id}")
        async def get_session_status(session_id: str):
            """获取会话状态"""
            if session_id not in self.streaming_sessions:
                return {"error": "会话不存在"}
            
            session = self.streaming_sessions[session_id]
            return {
                "session_id": session_id,
                "status": session["status"],
                "task": session["task"],
                "messages": session["messages"],
                "result": session.get("result"),
                "error": session.get("error"),
                "start_time": session["start_time"],
                "end_time": session.get("end_time")
            }
    
    def _detect_task_type(self, task: str) -> str:
        """智能检测任务类型"""
        task_lower = task.lower()
        
        # AI行业动态报告特殊检测（优先级最高）
        ai_keywords = ['ai', '人工智能', 'artificial intelligence', 'machine learning', '机器学习', 
                      'deep learning', '深度学习', 'llm', '大模型', 'gpt', 'chatgpt', 'claude', 
                      'ai agent', '智能体', 'openai', 'anthropic', '百度', 'baidu', '阿里', 'alibaba', 
                      '腾讯', 'tencent', '字节', 'bytedance', '科大讯飞', 'iflytek']
        
        industry_keywords = ['行业', 'industry', '动态', 'dynamics', '发展', 'development', 
                           '趋势', 'trend', '事件', 'event', '重大', 'major', '最新', 'latest', 
                           '新闻', 'news', '资讯', 'information', '进展', 'progress']
        
        if (any(ai_kw in task_lower for ai_kw in ai_keywords) and 
            any(ind_kw in task_lower for ind_kw in industry_keywords) and 
            any(report_kw in task_lower for report_kw in ['报告', 'report'])):
            return "full_report"  # AI行业动态报告使用完整报告流程
        
        # 单个MCP工具关键词检测
        if any(keyword in task_lower for keyword in ['搜索', 'search', '查找', '检索']):
            if any(keyword in task_lower for keyword in ['并行', 'parallel', '多渠道']):
                return "parallel_search"
            else:
                return "comprehensive_search"
        
        elif any(keyword in task_lower for keyword in ['分析', 'analysis', '评估', '质量']):
            return "quality_analysis"
        
        elif any(keyword in task_lower for keyword in ['大纲', 'outline', '结构', '框架']):
            return "outline_generation"
        
        elif any(keyword in task_lower for keyword in ['摘要', 'summary', '总结']):
            return "summary_generation"
        
        elif any(keyword in task_lower for keyword in ['内容', 'content', '写作', '生成']):
            return "content_generation"
        
        elif any(keyword in task_lower for keyword in ['交互', 'interaction', '用户', '选择']):
            return "user_interaction"
        
        # 复合任务检测
        elif any(keyword in task_lower for keyword in ['报告', 'report', '调研', '研究']):
            return "full_report"
        
        else:
            return "orchestrator"  # 默认使用调度器
    
    def _generate_single_mcp_stream(self, task: str, task_type: str, reporter: StreamingProgressReporter, **kwargs):
        """生成单个MCP工具的流式输出"""
        try:
            reporter.report_progress("🚀 启动单个MCP工具处理...", 0.1)
            
            # 根据任务类型调用相应的MCP工具
            if task_type == "comprehensive_search":
                reporter.report_progress("🔍 执行综合搜索...", 0.3)
                result = self.tool_registry.execute_tool(
                    "comprehensive_search",
                    queries=[task],
                    max_results=kwargs.get('max_results', 10),
                    days=kwargs.get('days', 30)
                )
            
            elif task_type == "parallel_search":
                reporter.report_progress("🔄 执行并行搜索...", 0.3)
                result = self.tool_registry.execute_tool(
                    "parallel_search",
                    queries=[task],
                    max_results_per_query=kwargs.get('max_results', 5),
                    days=kwargs.get('days', 30)
                )
            
            elif task_type == "quality_analysis":
                reporter.report_progress("📊 执行质量分析...", 0.3)
                # 需要先获取一些内容进行分析
                search_result = self.tool_registry.execute_tool(
                    "comprehensive_search",
                    queries=[task],
                    max_results=5,
                    days=30
                )
                result = self.tool_registry.execute_tool(
                    "analysis_mcp",
                    content_data=[{"content": search_result, "source": "搜索结果"}],
                    analysis_criteria=["相关性", "准确性", "时效性", "完整性"]
                )
            
            else:
                reporter.report_progress("🤖 使用默认处理方式...", 0.3)
                result = self.tool_registry.execute_tool(
                    "comprehensive_search",
                    queries=[task],
                    max_results=10,
                    days=30
                )
            
            reporter.report_progress("✅ 处理完成", 1.0)
            
            return {
                "task_type": task_type,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            reporter.report_error(f"处理失败: {str(e)}")
            return {
                "task_type": task_type,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_full_report_stream(self, task: str, reporter, **kwargs):
        """生成完整报告的流式输出"""
        try:
            reporter.report_progress("🚀 启动完整报告生成...", 0.1)
            
            # 使用调度器生成完整报告
            reporter.report_progress("🤖 调用智能调度器...", 0.2)
            
            # 过滤 orchestrator_mcp 支持的参数
            supported_params = {
                'report_type': kwargs.get('report_type', 'comprehensive'),
                'include_analysis': kwargs.get('include_analysis', True),
                'session_id': getattr(reporter, 'session_id', None),
                'days': kwargs.get('days', 30),
                'reporter': reporter  # 传递reporter实例
            }
            # 移除 None 值
            supported_params = {k: v for k, v in supported_params.items() if v is not None}
            
            result = self.tool_registry.execute_tool(
                "orchestrator_mcp_streaming",
                topic=task,
                **supported_params
            )
            
            reporter.report_progress("✅ 报告生成完成", 1.0)
            
            return {
                "task_type": "full_report",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            reporter.report_error(f"报告生成失败: {str(e)}")
            return {
                "task_type": "full_report",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def start_server(self, host: str = "0.0.0.0", port: int = 8001):
        """启动服务器"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)
    
    def start_server_thread(self, host: str = "0.0.0.0", port: int = 8001):
        """在后台线程启动服务器"""
        def run_server():
            import uvicorn
            uvicorn.run(self.app, host=host, port=port)
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        return thread

# 全局web服务器实例
web_server = None

def initialize_web_server(tool_registry: MCPToolRegistry):
    """初始化web服务器"""
    global web_server
    web_server = WebServer(tool_registry)
    return web_server

def start_fastapi_server(host: str = "0.0.0.0", port: int = 8001):
    """启动FastAPI服务器"""
    if web_server is None:
        raise RuntimeError("Web服务器未初始化，请先调用initialize_web_server()")
    
    return web_server.start_server_thread(host, port)