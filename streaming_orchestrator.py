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
        """流式生成报告 - 根据类型选择不同的处理流程"""
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
            
            # 学术报告使用专门的处理流程，不走大纲生成
            if task_type == "academic":
                # 学术报告专门流程
                yield self._create_progress_message("processing", "分析学术研究需求", f"正在分析{topic}的学术研究需求...")
                await asyncio.sleep(0.1)
                
                yield self._create_progress_message("processing", "生成学术搜索关键词", f"正在为{topic}生成学术搜索关键词...")
                await asyncio.sleep(0.1)
                
                yield self._create_progress_message("processing", "执行学术文献搜索", f"正在搜索{topic}相关的学术文献...")
                await asyncio.sleep(0.1)
                
                yield self._create_progress_message("processing", "分析研究数据", f"正在分析和组织{topic}的研究数据...")
                await asyncio.sleep(0.1)
                
                yield self._create_progress_message("processing", "论文分析与分类", f"正在对收集的25-30篇论文进行深入分析和分类...")
                await asyncio.sleep(0.1)
                
                yield self._create_progress_message("processing", "生成学术研究报告", f"正在生成包含详细论文分析的{topic}学术研究报告...")
                await asyncio.sleep(0.1)
            else:
                # 其他报告类型的常规流程
                yield self._create_progress_message("processing", "分析主题需求", f"正在分析{topic}的{task_type}需求...")
                await asyncio.sleep(0.1)
                
                yield self._create_progress_message("processing", "生成报告大纲", f"正在为{topic}生成详细的报告结构...")
                await asyncio.sleep(0.1)
                
                yield self._create_progress_message("processing", "生成报告内容", f"正在基于大纲生成详细的{report_name}内容...")
                await asyncio.sleep(0.1)
            
            # 清空上次用量，确保获取本次真实用量
            if hasattr(llm_processor, 'last_usage'):
                llm_processor.last_usage = None
            
            # 调用orchestrator_mcp生成报告
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
            
            # 检查是否有报告内容 - 处理不同报告类型的字段名
            report_content = None
            if result_data and result_data.get('status') == 'success':
                # 学术报告使用 'content' 字段
                if task_type == "academic" and 'content' in result_data:
                    report_content = result_data['content']
                # 其他报告使用 'report' 字段
                elif 'report' in result_data:
                    report_content = result_data['report']
                # 兜底处理
                elif 'content' in result_data:
                    report_content = result_data['content']
            
            if report_content:
                completion_message = f"{report_name}生成完成"
                completion_detail = f"成功生成{report_name}"
                yield self._create_progress_message("completed", completion_message, completion_detail)
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
                error_msg = result_data.get('error', f'{report_name}生成失败，未知原因')
                yield self._create_error_message(f"{report_name}生成失败: {error_msg}")
                
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
