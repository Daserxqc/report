#!/usr/bin/env python3
"""
MCP工具调用格式测试

测试MCP (Model Context Protocol) 工具调用的标准格式，包括：
1. tools/call 请求格式
2. SSE流式响应处理
3. 进度更新消息
4. 模型用量消息
5. 错误信息处理
6. 自动保存生成的报告到 reports/ 文件夹

参考格式：
- 请求：{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {...}}
- 响应：SSE流式推送，包含进度更新、模型用量、错误信息等

报告保存功能：
- 自动收集报告章节内容
- 保存为Markdown格式文件
- 文件名格式：{报告类型}_{主题}_{时间戳}.md
- 保存位置：./reports/ 文件夹
"""

import json
import asyncio
import aiohttp
import time
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class MCPToolCallRequest:
    """MCP工具调用请求结构"""
    jsonrpc: str = "2.0"
    id: int = 1
    method: str = "tools/call"
    params: Dict[str, Any] = None


@dataclass
class MCPProgressMessage:
    """MCP进度更新消息"""
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class MCPModelUsage:
    """MCP模型用量信息"""
    model_provider: str
    model_name: str
    input_tokens: int
    output_tokens: int


class MCPToolCallTester:
    """MCP工具调用测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = None
        self.report_sections = []  # 存储报告章节
        self.current_topic = ""  # 当前报告主题
        self.current_report_type = ""  # 当前报告类型
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def create_insight_report_request(self, topic: str, depth_level: str = "intermediate", target_audience: str = "professional") -> Dict[str, Any]:
        """创建洞察报告生成请求 - 使用orchestrator_mcp"""
        
        # 映射中文到英文参数
        depth_mapping = {
            "basic": "basic",
            "intermediate": "intermediate", 
            "advanced": "advanced",
            "详细": "detailed",
            "基础": "basic",
            "中等": "intermediate",
            "高级": "advanced"
        }
        
        audience_mapping = {
            "general": "general",
            "professional": "professional",
            "academic": "academic", 
            "business": "business",
            "专业人士": "professional",
            "学术": "academic",
            "商业": "business",
            "普通": "general"
        }
        
        mapped_depth = depth_mapping.get(depth_level, depth_level)
        mapped_audience = audience_mapping.get(target_audience, target_audience)
        
        return {
            "jsonrpc": "2.0",
            "id": f"insight_{int(time.time())}",
            "method": "tools/call",
            "params": {
                "name": "orchestrator_mcp",
                "arguments": {
                    "task": f"生成关于{topic}的深度洞察报告",
                    "task_type": "insights",
                    "topic": topic,
                    "depth_level": mapped_depth,
                    "target_audience": mapped_audience
                }
            }
        }
    
    def create_industry_dynamic_request(self, industry: str) -> Dict[str, Any]:
        """创建行业动态报告生成请求 - 使用orchestrator_mcp"""
        return {
            "jsonrpc": "2.0",
            "id": f"industry_{int(time.time())}",
            "method": "tools/call",
            "params": {
                "name": "orchestrator_mcp",
                "arguments": {
                    "task": f"生成{industry}行业动态报告",
                    "task_type": "industry",
                    "topic": industry,
                    "depth_level": "detailed",
                    "target_audience": "行业分析师"
                }
            }
        }
    
    def create_academic_research_request(self, research_topic: str) -> Dict[str, Any]:
        """创建学术研究报告生成请求 - 使用orchestrator_mcp"""
        return {
            "jsonrpc": "2.0",
            "id": f"academic_{int(time.time())}",
            "method": "tools/call",
            "params": {
                "name": "orchestrator_mcp",
                "arguments": {
                    "task": f"生成关于{research_topic}的学术研究报告",
                    "task_type": "academic",
                    "topic": research_topic,
                    "depth_level": "detailed",
                    "target_audience": "学术研究者"
                }
            }
        }
    
    def create_search_request(self, query: str) -> Dict[str, Any]:
        """创建搜索请求 - 使用search工具"""
        return {
            "jsonrpc": "2.0",
            "id": f"search_{int(time.time())}",
            "method": "tools/call",
            "params": {
                "name": "search",
                "arguments": {
                    "query": query,
                    "max_results": 10
                }
            }
        }
    
    async def send_tool_call_request(self, request_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """发送MCP工具调用请求并处理SSE响应"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        # 重置报告收集状态
        self.report_sections = []
        
        # 从请求中提取主题和报告类型
        params = request_data.get('params', {})
        arguments = params.get('arguments', {})
        self.current_topic = arguments.get('topic', arguments.get('industry', arguments.get('research_topic', '未知主题')))
        self.current_report_type = params.get('name', 'unknown')
        
        print(f"🚀 发送MCP工具调用请求: {request_data['params']['name']}")
        print(f"📋 请求ID: {request_data['id']}")
        print(f"🎯 报告主题: {self.current_topic}")
        
        try:
            # 设置超时时间，避免长时间等待
            timeout = aiohttp.ClientTimeout(total=3600)  # 10分钟超时
            async with self.session.post(
                f"{self.base_url}/mcp/tools/call",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=timeout
            ) as response:
                
                if response.status != 200:
                    print(f"❌ HTTP错误: {response.status}")
                    return []
                
                # 处理SSE流式响应
                messages = []
                try:
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        
                        if line_str.startswith('data: '):
                            try:
                                json_data = json.loads(line_str[6:])  # 移除 'data: ' 前缀
                                messages.append(json_data)
                                await self._process_sse_message(json_data)
                            except json.JSONDecodeError as e:
                                print(f"⚠️ JSON解析错误: {e}, 原始数据: {line_str}")
                except asyncio.TimeoutError:
                    print("⚠️ SSE流式读取超时，但可能已收到部分数据")
                except Exception as e:
                    print(f"⚠️ SSE流式读取错误: {e}")
                
                return messages
                
        except Exception as e:
            print(f"❌ 请求失败: {str(e)}")
            import traceback
            print(f"详细错误信息:")
            traceback.print_exc()
            return []
    
    async def _process_sse_message(self, message: Dict[str, Any]):
        """处理SSE消息 - 增强版，支持streaming_orchestrator发送的直接JSON消息"""
        # 检查是否为直接的JSON消息（来自streaming_orchestrator）
        if isinstance(message, dict):
            # 处理直接的JSON消息格式
            if message.get("type") == "outline":
                print(f"📋 收到大纲: {message.get('content', '')}")
                return
            elif message.get("type") == "model_usage":
                await self._handle_model_usage(message.get("data", {}))
                return
            elif message.get("type") == "progress":
                await self._handle_progress_update(message)
                return
            elif message.get("type") == "start":
                print(f"🚀 {message.get('message', '开始处理')}")
                return
            elif message.get("type") == "complete":
                print(f"✅ {message.get('message', '处理完成')}")
                return
        
        # 处理标准MCP消息格式
        if "method" in message and message["method"] == "notifications/message":
            await self._handle_notification_message(message)
        elif "error" in message:
            await self._handle_error_message(message)
        elif "result" in message:
            # 处理最终结果消息，这里包含实际的报告内容
            await self._handle_result_message(message)
        else:
            print(f"📨 收到消息: {json.dumps(message, ensure_ascii=False, indent=2)}")
    
    async def _handle_notification_message(self, message: Dict[str, Any]):
        """处理通知消息"""
        params = message.get("params", {})
        data = params.get("data", {})
        msg = data.get("msg", {})
        
        # 检查是否为模型用量消息
        if msg.get("type") == "model_usage":
            await self._handle_model_usage(msg.get("data", {}))
        else:
            # 进度更新消息
            await self._handle_progress_update(msg)
    
    async def _handle_progress_update(self, msg: Dict[str, Any]):
        """处理进度更新消息"""
        status = msg.get("status", "unknown")
        message = msg.get("message", "")
        details = msg.get("details", {})
        
        print(f"📊 进度更新: [{status}] {message}")
        
        if details:
            detail_name = details.get("name", "未知")
            detail_content = details.get("content", "")
            if detail_content:
                # 收集报告章节内容
                self.report_sections.append({
                    "name": detail_name,
                    "content": detail_content,
                    "status": status
                })
                
                # 显示内容预览（前100字符）
                preview = detail_content[:100] + "..." if len(detail_content) > 100 else detail_content
                print(f"   📝 {detail_name}: {preview}")
        
        # 注意：不在这里保存报告，等待最终结果消息
    
    async def _save_complete_report(self):
        """保存完整报告到reports文件夹"""
        try:
            # 确保reports文件夹存在
            reports_dir = os.path.join(os.path.dirname(__file__), "reports")
            print(f"🔍 [调试] reports目录路径: {reports_dir}")
            os.makedirs(reports_dir, exist_ok=True)
            print(f"🔍 [调试] reports目录创建完成，存在: {os.path.exists(reports_dir)}")
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_topic = "".join(c for c in self.current_topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_topic = safe_topic.replace(' ', '_')[:50]  # 限制长度
            filename = f"{self.current_report_type}_{safe_topic}_{timestamp}.md"
            filepath = os.path.join(reports_dir, filename)
            print(f"🔍 [调试] 生成文件路径: {filepath}")
            
            # 组装完整报告内容
            report_content = f"# {self.current_topic}\n\n"
            report_content += f"**报告类型**: {self.current_report_type}\n"
            report_content += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            report_content += "---\n\n"
            
            for section in self.report_sections:
                report_content += section['content'] + "\n\n"
            
            print(f"🔍 [调试] 报告内容长度: {len(report_content)} 字符")
            print(f"🔍 [调试] 报告章节数: {len(self.report_sections)}")
            
            # 保存到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            # 验证文件是否真的被创建
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"✅ [调试] 文件创建成功: {filepath}")
                print(f"✅ [调试] 文件大小: {file_size} 字节")
            else:
                print(f"❌ [调试] 文件创建失败: {filepath}")
            
            print(f"💾 报告已保存: {filepath}")
            print(f"📄 报告包含 {len(self.report_sections)} 个章节")
            
        except Exception as e:
            print(f"❌ 保存报告失败: {str(e)}")
            import traceback
            print(f"❌ 详细错误信息: {traceback.format_exc()}")
    
    async def _handle_model_usage(self, usage_data: Dict[str, Any]):
        """处理模型用量消息"""
        # 支持两种字段名格式：provider/model 和 model_provider/model_name
        provider = usage_data.get("provider", usage_data.get("model_provider", "unknown"))
        model_name = usage_data.get("model", usage_data.get("model_name", "unknown"))
        input_tokens = usage_data.get("input_tokens", 0)
        output_tokens = usage_data.get("output_tokens", 0)
        
        print(f"💰 模型用量: {provider}/{model_name}")
        print(f"   📥 输入Token: {input_tokens}")
        print(f"   📤 输出Token: {output_tokens}")
        print(f"   📊 总计Token: {input_tokens + output_tokens}")
    
    async def _handle_result_message(self, message: Dict[str, Any]):
        """处理结果消息，包含实际的报告内容"""
        result = message.get("result", {})
        
        # 检查是否包含报告内容
        if "content" in result:
            content = result["content"]
            if isinstance(content, list):
                # 如果内容是列表，合并所有内容
                full_content = "\n\n".join([str(item) for item in content])
            else:
                full_content = str(content)
            
            # 替换之前收集的状态消息，保存实际报告内容
            self.report_sections = [{
                "name": "完整报告",
                "content": full_content,
                "status": "completed"
            }]
            
            print(f"📄 收到完整报告内容，长度: {len(full_content)} 字符")
            
            # 立即保存报告
            await self._save_complete_report()
        
        elif "tool" in result and "content" in result:
            # 处理工具调用结果格式
            tool_name = result.get("tool", "unknown")
            content = result.get("content", "")
            
            self.report_sections = [{
                "name": f"{tool_name}报告",
                "content": content,
                "status": "completed"
            }]
            
            print(f"📄 收到{tool_name}报告内容，长度: {len(content)} 字符")
            await self._save_complete_report()
        
        else:
            print(f"📨 收到结果消息: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    async def _handle_error_message(self, message: Dict[str, Any]):
        """处理错误消息"""
        error = message.get("error", {})
        code = error.get("code", -1)
        error_message = error.get("message", "未知错误")
        error_data = error.get("data", {})
        
        print(f"❌ 错误 [{code}]: {error_message}")
        if error_data:
            error_type = error_data.get("type", "unknown")
            error_details = error_data.get("message", "")
            print(f"   🔍 错误类型: {error_type}")
            print(f"   📋 错误详情: {error_details}")
        
        # 记录错误到报告章节
        self.report_sections.append({
            "name": "错误信息",
            "content": f"错误代码: {code}\n错误消息: {error_message}",
            "status": "error"
        })


async def test_insight_report_generation():
    """测试洞察报告生成"""
    print("=" * 60)
    print("🧪 测试洞察报告生成")
    print("=" * 60)
    
    async with MCPToolCallTester() as tester:
        request = tester.create_insight_report_request("人工智能在教育领域的应用")
        messages = await tester.send_tool_call_request(request)
        
        # 确保报告被保存
        if tester.report_sections and not any("💾 报告已保存" in str(msg) for msg in messages):
            await tester._save_complete_report()
        
        print(f"\n✅ 测试完成，共收到 {len(messages)} 条消息")
        return messages


# 其他测试函数已移除，只保留洞察报告测试


async def test_insight_only():
    """只测试洞察报告生成"""
    print("🚀 开始MCP工具调用格式测试 - 洞察报告")
    print("=" * 80)
    
    try:
        # 只测试洞察报告
        messages = await test_insight_report_generation()
        
        # 生成测试报告
        print("\n" + "=" * 80)
        print("📊 测试结果汇总")
        print("=" * 80)
        
        print(f"🔧 insight_report: {len(messages)} 条消息")
        
        # 统计消息类型
        message_types = {}
        for msg in messages:
            if "method" in msg:
                method = msg["method"]
                message_types[method] = message_types.get(method, 0) + 1
            elif "error" in msg:
                message_types["error"] = message_types.get("error", 0) + 1
        
        for msg_type, count in message_types.items():
            print(f"   📨 {msg_type}: {count} 条")
        
        print("\n💾 报告保存说明: 生成的报告已自动保存到 reports/ 文件夹")
        
        return {"insight_report": messages}
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        print(f"详细错误信息:")
        traceback.print_exc()
        return {"insight_report": []}


async def test_custom_insight_report(topic: str = None, depth_level: str = "intermediate", target_audience: str = "professional"):
    """测试自定义洞察报告题目
    
    Args:
        topic: 自定义主题，如果为None则使用默认值
        depth_level: 深度等级 (basic/intermediate/advanced)
        target_audience: 目标受众 (general/professional/academic/business)
    """
    if topic is None:
        topic = "人工智能在教育领域的应用前景"
    
    print(f"🚀 开始自定义洞察报告测试")
    print(f"📋 报告主题: {topic}")
    print(f"📊 深度等级: {depth_level}")
    print(f"👥 目标受众: {target_audience}")
    print("=" * 80)
    
    try:
        async with MCPToolCallTester() as tester:
            request = tester.create_insight_report_request(topic, depth_level, target_audience)
            messages = await tester.send_tool_call_request(request)
            
            # 确保报告被保存
            if tester.report_sections:
                await tester._save_complete_report()
            
            # 生成测试报告
            print("\n" + "=" * 80)
            print("📊 自定义洞察报告测试结果")
            print("=" * 80)
            
            print(f"🎯 报告主题: {topic}")
            print(f"📝 报告类型: 洞察报告")
            print(f"📨 收到消息: {len(messages)} 条")
            
            # 统计消息类型
            message_types = {}
            for msg in messages:
                if "method" in msg:
                    method = msg["method"]
                    message_types[method] = message_types.get(method, 0) + 1
                elif "error" in msg:
                    message_types["error"] = message_types.get("error", 0) + 1
            
            for msg_type, count in message_types.items():
                print(f"   📨 {msg_type}: {count} 条")
            
            print("\n💾 报告保存说明: 生成的报告已自动保存到 reports/ 文件夹")
            
            return {"insight_report": messages}
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        print(f"详细错误信息:")
        traceback.print_exc()
        return {"insight_report": []}


def create_sample_requests():
    """创建示例请求数据"""
    print("📋 MCP工具调用请求示例")
    print("=" * 60)
    
    # 洞察报告请求示例
    insight_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "orchestrator_mcp",
            "arguments": {
                "task": "生成关于人工智能在教育领域的应用的深度洞察报告",
                "task_type": "insights",
                "topic": "人工智能在教育领域的应用",
                "depth_level": "detailed",
                "target_audience": "行业专家",
                "max_iterations": 3,
                "min_quality_score": 7.0
            }
        }
    }
    
    print("1. 洞察报告生成请求:")
    print(json.dumps(insight_request, ensure_ascii=False, indent=2))
    print()
    
    # 行业动态报告请求示例
    industry_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "orchestrator_mcp",
            "arguments": {
                "task": "生成新能源汽车行业动态报告",
                "task_type": "industry",
                "topic": "新能源汽车",
                "depth_level": "detailed",
                "target_audience": "行业分析师",
                "max_iterations": 3,
                "min_quality_score": 7.0
            }
        }
    }
    
    print("2. 行业动态报告生成请求:")
    print(json.dumps(industry_request, ensure_ascii=False, indent=2))
    print()
    
    # 学术研究报告请求示例
    academic_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "orchestrator_mcp",
            "arguments": {
                "task": "生成关于量子计算在密码学中的应用的学术研究报告",
                "task_type": "academic",
                "topic": "量子计算在密码学中的应用",
                "depth_level": "detailed",
                "target_audience": "学术研究者",
                "writing_style": "academic",
                "max_iterations": 3,
                "min_quality_score": 8.0
            }
        }
    }
    
    print("3. 学术研究报告生成请求:")
    print(json.dumps(academic_request, ensure_ascii=False, indent=2))
    print()
    
    # 搜索请求示例
    search_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "search",
            "arguments": {
                "query": "区块链技术在供应链管理中的应用",
                "max_results": 10
            }
        }
    }
    
    print("4. 搜索请求:")
    print(json.dumps(search_request, ensure_ascii=False, indent=2))
    print()


def create_sample_responses():
    """创建示例响应数据"""
    print("📨 MCP工具调用响应示例")
    print("=" * 60)
    
    # 进度更新消息示例
    progress_message = {
        "method": "notifications/message",
        "params": {
            "level": "info",
            "data": {
                "msg": {
                    "status": "generating_sections",
                    "message": "完成市场分析章节的生成任务",
                    "details": {
                        "id": 1,
                        "name": "市场分析",
                        "content": "## 市场分析\n\n### 市场规模与增长\n\n根据最新数据显示，全球人工智能教育市场规模预计将从2023年的XX亿美元增长到2030年的XX亿美元，年复合增长率达到XX%。\n\n### 主要驱动因素\n\n1. **技术进步**: 机器学习、自然语言处理等技术的快速发展\n2. **政策支持**: 各国政府对AI教育的政策支持和资金投入\n3. **需求增长**: 个性化学习需求的不断增长"
                    }
                },
                "extra": None
            }
        },
        "jsonrpc": "2.0"
    }
    
    print("1. 进度更新消息:")
    print(json.dumps(progress_message, ensure_ascii=False, indent=2))
    print()
    
    # 模型用量消息示例
    model_usage_message = {
        "jsonrpc": "2.0",
        "method": "notifications/message",
        "params": {
            "data": {
                "msg": {
                    "type": "model_usage",
                    "data": {
                        "model_provider": "dashscope",
                        "model_name": "qwen-max",
                        "input_tokens": 1250,
                        "output_tokens": 890
                    }
                }
            }
        }
    }
    
    print("2. 模型用量消息:")
    print(json.dumps(model_usage_message, ensure_ascii=False, indent=2))
    print()
    
    # 错误信息示例
    error_message = {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32603,
            "message": "Internal error",
            "data": {
                "type": "report_generation_failed",
                "message": "内容生成模型未能返回有效内容，请检查输入参数或稍后重试。"
            }
        }
    }
    
    print("3. 错误信息:")
    print(json.dumps(error_message, ensure_ascii=False, indent=2))
    print()


async def main():
    """主函数 - 只测试洞察报告"""
    print("[测试] MCP工具调用格式测试 - 洞察报告专用")
    print("=" * 80)
    
    # 显示示例请求和响应
    create_sample_requests()
    create_sample_responses()
    
    # 测试选项菜单
    print("\n[选项] 测试选项:")
    print("1. 默认洞察报告测试")
    print("2. 自定义洞察报告测试")
    print("3. 显示示例后退出")
    print("\n[提示] 提示: 可以直接修改代码中的参数来测试不同题目")
    
    # 为了演示，提供几个预设的自定义测试
    print("\n[运行] 运行自定义洞察报告测试示例...")
    
    try:
        # 示例: 自定义洞察报告
        print("\n" + "=" * 60)
        print("[示例] 示例: 自定义洞察报告")
        await test_custom_insight_report("生成式人工智能+教育")
        
        print("\n" + "=" * 80)
        print("[完成] 所有洞察报告测试完成!")
        print("\n[保存] 报告保存功能已启用:")
        print("   - 生成的报告自动保存到 reports/ 文件夹")
        print("   - 文件格式: Markdown (.md)")
        print("   - 文件名包含报告类型、主题和时间戳")
        print("\n[提示] 如需测试其他题目，请修改以下代码:")
        print("   await test_custom_insight_report('您的自定义题目')")
        print("   只支持洞察报告类型")
        
    except Exception as e:
        print(f"[错误] 测试失败: {str(e)}")
        print("[提示] 请确保MCP服务器正在运行 (http://localhost:8001)")


# 使用说明:
# 1. 运行此脚本将测试多个预设的洞察报告题目
# 2. 如需测试其他题目，可以修改main()函数中的test_custom_insight_report调用
# 3. 或者直接调用: await test_custom_insight_report("您的题目")
# 4. 只支持洞察报告类型

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "custom":
            # 自定义洞察报告测试
            if len(sys.argv) > 2:
                topic = sys.argv[2]
                print(f"[自定义] 测试自定义题目: {topic}")
                asyncio.run(test_custom_insight_report(topic))
            else:
                # 交互式输入
                print("[交互] 请输入自定义题目:")
                topic = input("题目: ").strip()
                if topic:
                    print(f"[自定义] 测试题目: {topic}")
                    asyncio.run(test_custom_insight_report(topic))
                else:
                    print("❌ 未输入题目，运行默认测试")
                    asyncio.run(main())
        elif sys.argv[1] == "insight":
            # 只测试洞察报告
            asyncio.run(test_insight_only())
        elif sys.argv[1] == "interactive":
            # 交互式模式
            print("\n[交互模式] 自定义洞察报告生成")
            print("=" * 50)
            topic = input("请输入报告题目: ").strip()
            if not topic:
                print("❌ 未输入题目，退出")
                sys.exit(1)
            
            # 可选参数
            print("\n[可选参数] 以下参数可选 (直接回车使用默认值):")
            depth_level = input("深度等级 (basic/intermediate/advanced) [intermediate]: ").strip() or "intermediate"
            target_audience = input("目标受众 (general/professional/academic/business) [professional]: ").strip() or "professional"
            
            print(f"\n[配置] 报告配置:")
            print(f"  题目: {topic}")
            print(f"  深度等级: {depth_level}")
            print(f"  目标受众: {target_audience}")
            print(f"\n[开始] 开始生成报告...")
            
            async def run_interactive():
                await test_custom_insight_report(topic, depth_level, target_audience)
            
            asyncio.run(run_interactive())
        else:
            print("❌ 不支持的测试类型")
            print("支持的参数:")
            print("  python test_mcp_tool_call_format.py custom [题目]     # 自定义题目")
            print("  python test_mcp_tool_call_format.py interactive       # 交互式模式") 
            print("  python test_mcp_tool_call_format.py insight           # 默认洞察测试")
            sys.exit(1)
    else:
        # 运行默认洞察报告测试
        asyncio.run(main())
