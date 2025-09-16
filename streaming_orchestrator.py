# streaming_orchestrator.py
"""
流式MCP调度器 - 支持实时SSE推送的MCP工具调度器
基于MCP工具的纯净实现，提供流式数据推送能力
"""

import json
import asyncio
from typing import Dict, Any, AsyncGenerator
from datetime import datetime

from main import (
    analysis_mcp, query_generation_mcp, outline_writer_mcp, 
    summary_writer_mcp, content_writer_mcp, search,
    orchestrator_mcp, llm_processor
)

class StreamingOrchestrator:
    """支持实时SSE推送的MCP调度器 - 基于MCP工具的纯净实现"""
    
    def __init__(self):
        self.tool_name = None
        self.current_step = 0
        self.total_steps = 0
        
    def _create_heartbeat_message(self) -> str:
        """创建心跳消息"""
        try:
            return json.dumps({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "status": "alive",
                    "tool": self.tool_name,
                    "step": f"{self.current_step}/{self.total_steps}" if self.total_steps > 0 else "0/0"
                }
            })
        except Exception as e:
            return json.dumps({"type": "error", "error": f"心跳消息生成失败: {str(e)}"})

    async def _safe_yield(self, message: str, description: str = "消息"):
        """安全的消息推送，包含错误处理"""
        try:
            if not message:
                message = json.dumps({
                    "type": "error",
                    "error": f"空{description}",
                    "timestamp": datetime.now().isoformat()
                })
            yield message
        except Exception as e:
            error_message = json.dumps({
                "type": "error", 
                "error": f"{description}推送失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
            yield error_message

    async def _call_content_writer_with_usage(self, **kwargs):
        """调用content_writer_mcp并返回内容和用量信息"""
        try:
            result = await asyncio.to_thread(content_writer_mcp, **kwargs)
            print(f"🔍 [调试] content_writer_mcp返回结果: {str(result)[:200]}...")
            
            try:
                import json
                # 处理返回结果 - generate_insight_report返回的是字符串，不是JSON
                if isinstance(result, str) and result.startswith('{'):
                    try:
                        result_data = json.loads(result)
                    except json.JSONDecodeError:
                        result_data = {"report_content": result, "status": "completed"}
                else:
                    result_data = {"report_content": result, "status": "completed"}
                
                content = result_data.get('content', result)  # 提取纯文本内容
                usage = result_data.get('usage', None)
                print(f"🔍 [调试] 解析JSON成功，提取到{len(content)}字符的内容，usage: {usage}")
                
                # 格式化内容
                if isinstance(content, str):
                    # 处理转义字符
                    content = content.replace('\\n', '\n').replace('\\t', '\t')
                    print(f"🔍 [调试] 内容格式化完成，最终长度: {len(content)}字符")
                
                return content, usage
            except (json.JSONDecodeError, TypeError) as json_error:
                print(f"⚠️ [调试] JSON解析失败: {json_error}，使用fallback方式")
                # 如果JSON解析失败，直接返回原始结果
                usage = None
                if hasattr(llm_processor, 'last_usage') and llm_processor.last_usage:
                    usage = llm_processor.last_usage
                    print(f"🔍 [调试] 从llm_processor获取到的usage: {usage}")
                return result, usage
        except Exception as e:
            print(f"❌ [调试] content_writer_mcp调用失败: {str(e)}")
            raise e

    # 删除了无用的委托方法，直接使用 stream_insight_report 等核心方法

    async def stream_insight_report(self, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """流式生成洞察报告"""
        self.tool_name = "orchestrator_mcp"
        
        try:
            topic = kwargs.get("topic", "未指定主题")
            task = kwargs.get("task", f"生成关于{topic}的报告")
            task_type = kwargs.get("task_type", "insights")
            depth_level = kwargs.get("depth_level", "detailed")
            target_audience = kwargs.get("target_audience", "行业专家")
            
            # 根据任务类型确定报告类型名称
            report_type_names = {
                "insights": "洞察报告",
                "industry": "行业动态报告",
                "academic": "学术研究报告",
                "comprehensive": "综合报告"
            }
            report_name = report_type_names.get(task_type, "报告")
            
            # 发送开始消息
            yield self._create_progress_message("started", f"开始生成{report_name}", f"正在初始化{report_name}分析流程...")
            await asyncio.sleep(0.1)
            
            # 发送进度更新
            yield self._create_progress_message("processing", "分析主题需求", f"正在分析{topic}的{task_type}需求...")
            await asyncio.sleep(0.1)
            
            # 直接生成完整报告（包括大纲）
            yield self._create_progress_message("processing", "生成报告大纲", f"正在为{topic}生成详细的报告结构...")
            await asyncio.sleep(0.1)
            
            # 生成完整报告内容（orchestrator_mcp会处理大纲生成）
            yield self._create_progress_message("processing", "生成报告内容", f"正在基于大纲生成详细的{report_name}内容...")
            await asyncio.sleep(0.1)
            
            # 清空上次用量，确保获取本次真实用量
            if hasattr(llm_processor, 'last_usage'):
                llm_processor.last_usage = None
            
            # 直接调用orchestrator_mcp生成洞察报告
            result = await asyncio.to_thread(
                orchestrator_mcp,
                task=task,
                task_type=task_type,
                topic=topic,
                depth_level=depth_level,
                target_audience=target_audience
            )
            
            # 处理返回结果 - orchestrator_mcp返回的是字符串，不是JSON
            if isinstance(result, str) and result.startswith('{'):
                try:
                    result_data = json.loads(result)
                except json.JSONDecodeError:
                    result_data = {"report_content": result, "status": "completed"}
            else:
                result_data = {"report_content": result, "status": "completed"}
            
            # 从result_data中提取usage信息并发送模型用量消息
            if result_data and 'usage' in result_data:
                usage_info = result_data['usage']
                yield self._create_model_usage_message(usage_data=usage_info)
                await asyncio.sleep(0.1)
            
            # 检查是否有报告内容 - 修复字段名匹配问题
            if result_data and result_data.get('status') == 'success' and 'report' in result_data:
                report_content = result_data['report']
                yield self._create_progress_message("completed", "洞察报告生成完成", "成功生成深度洞察分析报告")
                await asyncio.sleep(0.1)
                
                # 发送最终结果
                final_result = {
                    "jsonrpc": "2.0",
                    "result": {
                        "tool": "orchestrator_mcp",
                        "content": report_content
                    }
                }
                
                # 发送用量信息
                if result_data and 'usage' in result_data:
                    yield self._create_model_usage_message(usage_data=result_data['usage'])
                elif hasattr(llm_processor, 'last_usage') and llm_processor.last_usage:
                    yield self._create_model_usage_message(usage_data=llm_processor.last_usage)
                
                yield final_result
            else:
                # 处理失败情况
                error_msg = result_data.get('error', '报告生成失败，未知原因')
                yield self._create_error_message(f"洞察报告生成失败: {error_msg}")
                
        except Exception as e:
            print(f"❌ 洞察报告生成过程中发生错误: {str(e)}")
            yield self._create_error_message(f"洞察报告生成过程中发生错误: {str(e)}")

    def _create_progress_message(self, status: str, message: str, content: str, details: Dict = None) -> Dict[str, Any]:
        """创建符合MCP标准的进度消息"""
        msg_data = {
            "status": status,
            "message": message
        }
        
        if details:
            msg_data["details"] = details
        elif content:
            msg_data["details"] = {
                "content": content,
                "step": self.current_step,
                "total_steps": self.total_steps
            }
        
        return {
            "method": "notifications/message",
            "params": {
                "level": "info",
                "data": {
                    "msg": msg_data,
                    "extra": None
                }
            },
            "jsonrpc": "2.0"
        }

    def _create_model_usage_message(self, provider: str = None, model: str = None, input_tokens: int = None, output_tokens: int = None, total_tokens: int = None, usage_data: dict = None) -> Dict[str, Any]:
        """创建符合MCP标准的模型用量消息"""
        if usage_data:
            # 使用传入的usage_data
            usage_info = usage_data
        else:
            # 构建usage信息
            usage_info = {
                "model_provider": provider or "unknown",
                "model_name": model or "unknown", 
                "input_tokens": input_tokens or 0,
                "output_tokens": output_tokens or 0
            }
        
        return {
            "jsonrpc": "2.0",
            "method": "notifications/message",
            "params": {
                "data": {
                    "msg": {
                        "type": "model_usage",
                        "data": usage_info
                    }
                }
            }
        }

    def _create_error_message(self, error: str) -> Dict[str, Any]:
        """创建符合MCP标准的错误消息"""
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": {
                    "type": "streaming_error",
                    "message": error
                }
            }
        }
