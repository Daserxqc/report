#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流式处理模块
管理所有流式处理相关功能，包括进度报告和SSE支持
"""

import json
import uuid
import time
import threading
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Generator, AsyncGenerator
from dataclasses import dataclass, asdict

from config_manager import server_config


@dataclass
class ProgressUpdate:
    """进度更新数据结构"""
    status: str
    message: str
    timestamp: str
    details: Optional[Dict] = None
    progress_percentage: Optional[float] = None


@dataclass
class ModelUsage:
    """模型使用情况数据结构"""
    model_provider: str
    model_name: str
    input_tokens: int
    output_tokens: int
    timestamp: str
    cost_estimate: Optional[float] = None


@dataclass
class StreamingSession:
    """流式会话数据结构"""
    session_id: str
    task: str
    task_type: str
    status: str  # 'running', 'completed', 'error'
    created_at: str
    completed_at: Optional[str] = None
    progress_updates: List[ProgressUpdate] = None
    model_usage: List[ModelUsage] = None
    final_result: Optional[Dict] = None
    error_info: Optional[Dict] = None
    
    def __post_init__(self):
        if self.progress_updates is None:
            self.progress_updates = []
        if self.model_usage is None:
            self.model_usage = []


class StreamingProgressReporter:
    """流式进度报告器"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.updates = []
        self.model_usage_records = []
        self.lock = threading.Lock()
    
    def report_progress(self, status: str, message: str, details: dict = None, progress_percentage: float = None):
        """报告进度更新"""
        update = ProgressUpdate(
            status=status,
            message=message,
            timestamp=datetime.now().isoformat(),
            details=details,
            progress_percentage=progress_percentage
        )
        
        with self.lock:
            self.updates.append(update)
        
        # 生成符合用户规范的进度报告格式
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
        
        print(f"📊 [进度报告] {status}: {message}")
        return json.dumps(mcp_update, ensure_ascii=False)
    
    def report_model_usage(self, model_provider: str, model_name: str, input_tokens: int, output_tokens: int, cost_estimate: float = None):
        """报告模型使用情况"""
        usage = ModelUsage(
            model_provider=model_provider,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            timestamp=datetime.now().isoformat(),
            cost_estimate=cost_estimate
        )
        
        with self.lock:
            self.model_usage_records.append(usage)
        
        # 生成符合用户规范的模型用量报告格式
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
        
        print(f"💰 [模型使用] {model_provider}/{model_name}: {input_tokens}+{output_tokens}tokens")
        return json.dumps(mcp_usage, ensure_ascii=False)
    
    def report_final_result(self, result: dict, request_id: int = 1):
        """报告最终结果"""
        # 生成符合用户规范的最终结果格式
        mcp_result = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": str(result.get('report', '')) if isinstance(result, dict) else str(result)
                    }
                ],
                "structuredContent": result,
                "isError": False
            }
        }
        
        print(f"✅ [最终结果] 会话 {self.session_id} 完成")
        return json.dumps(mcp_result, ensure_ascii=False)
    
    def report_error(self, error: str, error_code: int = -32603, error_type: str = "internal_error", request_id: int = 1):
        """报告错误"""
        # 生成符合用户规范的错误报告格式
        mcp_error = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": error_code,
                "message": error,
                "data": {
                    "type": error_type,
                    "message": error
                }
            }
        }
        
        print(f"❌ [错误报告] {error}")
        return json.dumps(mcp_error, ensure_ascii=False)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要"""
        with self.lock:
            return {
                "session_id": self.session_id,
                "total_updates": len(self.updates),
                "total_model_usage": len(self.model_usage_records),
                "session_duration": self._calculate_session_duration(),
                "latest_update": asdict(self.updates[-1]) if self.updates else None,
                "total_tokens_used": sum(usage.input_tokens + usage.output_tokens for usage in self.model_usage_records),
                "estimated_cost": sum(usage.cost_estimate or 0 for usage in self.model_usage_records)
            }
    
    def _calculate_session_duration(self) -> float:
        """计算会话持续时间（秒）"""
        if not self.updates:
            return 0.0
        
        start_time = datetime.fromisoformat(self.updates[0].timestamp)
        end_time = datetime.fromisoformat(self.updates[-1].timestamp)
        return (end_time - start_time).total_seconds()


class StreamingSessionManager:
    """流式会话管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, StreamingSession] = {}
        self.lock = threading.Lock()
    
    def create_session(self, task: str, task_type: str = "auto") -> str:
        """创建新的流式会话"""
        session_id = str(uuid.uuid4())
        session = StreamingSession(
            session_id=session_id,
            task=task,
            task_type=task_type,
            status="running",
            created_at=datetime.now().isoformat()
        )
        
        with self.lock:
            self.sessions[session_id] = session
        
        print(f"🆕 [会话创建] {session_id}: {task[:50]}...")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[StreamingSession]:
        """获取会话信息"""
        with self.lock:
            return self.sessions.get(session_id)
    
    def update_session_progress(self, session_id: str, update: ProgressUpdate):
        """更新会话进度"""
        with self.lock:
            session = self.sessions.get(session_id)
            if session:
                session.progress_updates.append(update)
    
    def add_model_usage(self, session_id: str, usage: ModelUsage):
        """添加模型使用记录"""
        with self.lock:
            session = self.sessions.get(session_id)
            if session:
                session.model_usage.append(usage)
    
    def complete_session(self, session_id: str, result: Dict[str, Any]):
        """完成会话"""
        with self.lock:
            session = self.sessions.get(session_id)
            if session:
                session.status = "completed"
                session.completed_at = datetime.now().isoformat()
                session.final_result = result
        
        print(f"✅ [会话完成] {session_id}")
    
    def error_session(self, session_id: str, error_info: Dict[str, Any]):
        """标记会话错误"""
        with self.lock:
            session = self.sessions.get(session_id)
            if session:
                session.status = "error"
                session.completed_at = datetime.now().isoformat()
                session.error_info = error_info
        
        print(f"❌ [会话错误] {session_id}: {error_info.get('message', '未知错误')}")
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """清理旧会话"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        with self.lock:
            sessions_to_remove = []
            for session_id, session in self.sessions.items():
                session_time = datetime.fromisoformat(session.created_at).timestamp()
                if session_time < cutoff_time:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.sessions[session_id]
        
        if sessions_to_remove:
            print(f"🧹 [会话清理] 清理了 {len(sessions_to_remove)} 个旧会话")
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """获取所有会话的摘要"""
        with self.lock:
            return [
                {
                    "session_id": session.session_id,
                    "task": session.task[:100] + "..." if len(session.task) > 100 else session.task,
                    "task_type": session.task_type,
                    "status": session.status,
                    "created_at": session.created_at,
                    "completed_at": session.completed_at,
                    "progress_count": len(session.progress_updates),
                    "model_usage_count": len(session.model_usage)
                }
                for session in self.sessions.values()
            ]


class SSEStreamGenerator:
    """SSE流生成器"""
    
    @staticmethod
    def generate_sse_stream(session_id: str, data_generator: Generator) -> Generator[str, None, None]:
        """生成SSE格式的数据流"""
        try:
            yield f"data: {{\"type\": \"session_start\", \"session_id\": \"{session_id}\", \"timestamp\": \"{datetime.now().isoformat()}\"}}\n\n"
            
            for data in data_generator:
                if isinstance(data, dict):
                    sse_data = json.dumps(data, ensure_ascii=False)
                else:
                    sse_data = str(data)
                
                yield f"data: {sse_data}\n\n"
                time.sleep(0.1)  # 防止过快发送
            
            yield f"data: {{\"type\": \"session_end\", \"session_id\": \"{session_id}\", \"timestamp\": \"{datetime.now().isoformat()}\"}}\n\n"
            
        except Exception as e:
            error_data = {
                "type": "error",
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    @staticmethod
    async def generate_async_sse_stream(session_id: str, data_generator: AsyncGenerator) -> AsyncGenerator[str, None]:
        """生成异步SSE格式的数据流"""
        try:
            yield f"data: {{\"type\": \"session_start\", \"session_id\": \"{session_id}\", \"timestamp\": \"{datetime.now().isoformat()}\"}}\n\n"
            
            async for data in data_generator:
                if isinstance(data, dict):
                    sse_data = json.dumps(data, ensure_ascii=False)
                else:
                    sse_data = str(data)
                
                yield f"data: {sse_data}\n\n"
                await asyncio.sleep(0.1)  # 防止过快发送
            
            yield f"data: {{\"type\": \"session_end\", \"session_id\": \"{session_id}\", \"timestamp\": \"{datetime.now().isoformat()}\"}}\n\n"
            
        except Exception as e:
            error_data = {
                "type": "error",
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"


class TaskTypeDetector:
    """任务类型检测器"""
    
    @staticmethod
    def detect_task_type(task: str) -> str:
        """检测任务类型"""
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
            return "ai_industry_report"
        
        # 报告生成类型检测
        if any(keyword in task_lower for keyword in ['报告', 'report', '分析', 'analysis']):
            if any(keyword in task_lower for keyword in ['市场', 'market', '行业', 'industry']):
                return "market_report"
            elif any(keyword in task_lower for keyword in ['新闻', 'news', '资讯']):
                return "news_report"
            elif any(keyword in task_lower for keyword in ['研究', 'research', '学术', 'academic']):
                return "research_report"
            elif any(keyword in task_lower for keyword in ['洞察', 'insight', '趋势', 'trend']):
                return "insight_report"
            else:
                return "comprehensive_report"
        
        # 搜索类型检测
        elif any(keyword in task_lower for keyword in ['搜索', 'search', '查找', 'find']):
            if any(keyword in task_lower for keyword in ['新闻', 'news']):
                return "news_search"
            elif any(keyword in task_lower for keyword in ['学术', 'academic', '论文', 'paper']):
                return "academic_search"
            else:
                return "web_search"
        
        # 分析类型检测
        elif any(keyword in task_lower for keyword in ['分析', 'analyze', '评估', 'evaluate']):
            return "analysis"
        
        # 总结类型检测
        elif any(keyword in task_lower for keyword in ['总结', 'summary', '摘要', 'abstract']):
            return "summarization"
        
        # 默认类型
        else:
            return "general"


# 全局实例
session_manager = StreamingSessionManager()
sse_generator = SSEStreamGenerator()
task_detector = TaskTypeDetector()

# 定期清理旧会话的后台任务
def _cleanup_sessions_periodically():
    """定期清理会话的后台任务"""
    import time
    while True:
        time.sleep(3600)  # 每小时清理一次
        session_manager.cleanup_old_sessions()

# 启动后台清理任务
cleanup_thread = threading.Thread(target=_cleanup_sessions_periodically, daemon=True)
cleanup_thread.start()

if __name__ == "__main__":
    # 测试流式处理功能
    print("\n📡 流式处理模块状态报告:")
    print(f"   🆔 会话管理器: ✅")
    print(f"   📊 进度报告器: ✅")
    print(f"   🌊 SSE流生成器: ✅")
    print(f"   🔍 任务类型检测器: ✅")
    print(f"   🧹 后台清理任务: ✅")
else:
    print("✅ 流式处理模块初始化完成")