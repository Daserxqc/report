#!/usr/bin/env python3
"""
MCP工具调用格式测试

测试MCP (Model Context Protocol) 工具调用的标准格式，包括：
1. tools/call 请求格式
2. SSE流式响应处理
3. 进度更新消息
4. 模型用量消息
5. 错误信息处理

参考格式：
- 请求：{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {...}}
- 响应：SSE流式推送，包含进度更新、模型用量、错误信息等
"""

import json
import asyncio
import aiohttp
import time
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
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def create_insight_report_request(self, topic: str, report_type: str = "insight") -> Dict[str, Any]:
        """创建洞察报告生成请求"""
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "generate_insight_report",
                "arguments": {
                    "topic": topic,
                    "report_type": report_type,
                    "depth_level": "detailed",
                    "target_audience": "行业专家",
                    "include_citations": True,
                    "max_sections": 8
                }
            }
        }
    
    def create_industry_dynamic_request(self, industry: str, time_range: str = "recent") -> Dict[str, Any]:
        """创建行业动态报告生成请求"""
        return {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "generate_industry_dynamic_report",
                "arguments": {
                    "industry": industry,
                    "time_range": time_range,
                    "focus_areas": ["市场趋势", "技术创新", "政策影响", "竞争格局"],
                    "include_analysis": True,
                    "data_sources": ["news", "research", "market_data"],
                    # "use_local_data": True  # 注释掉，使用真实网络搜索
                }
            }
        }
    
    def create_academic_research_request(self, research_topic: str, academic_level: str = "advanced") -> Dict[str, Any]:
        """创建学术研究报告生成请求"""
        return {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "generate_academic_research_report",
                "arguments": {
                    "research_topic": research_topic,
                    "academic_level": academic_level,
                    "research_methodology": "comprehensive",
                    "include_literature_review": True,
                    "citation_style": "academic",
                    "max_pages": 20
                }
            }
        }
    
    def create_search_request(self, query: str, search_type: str = "comprehensive") -> Dict[str, Any]:
        """创建搜索请求"""
        return {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "comprehensive_search",
                "arguments": {
                    "topic": query,
                    "search_type": search_type,
                    "max_results": 10,
                    "days": 30,
                    "sources": ["web", "academic", "news"]
                }
            }
        }
    
    async def send_tool_call_request(self, request_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """发送MCP工具调用请求并处理SSE响应"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        print(f"🚀 发送MCP工具调用请求: {request_data['params']['name']}")
        print(f"📋 请求ID: {request_data['id']}")
        
        try:
            # 设置超时时间，避免长时间等待
            timeout = aiohttp.ClientTimeout(total=3000)  # 10分钟超时
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
        """处理SSE消息"""
        if "method" in message and message["method"] == "notifications/message":
            await self._handle_notification_message(message)
        elif "error" in message:
            await self._handle_error_message(message)
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
                # 显示内容预览（前100字符）
                preview = detail_content[:100] + "..." if len(detail_content) > 100 else detail_content
                print(f"   📝 {detail_name}: {preview}")
    
    async def _handle_model_usage(self, usage_data: Dict[str, Any]):
        """处理模型用量消息"""
        provider = usage_data.get("model_provider", "unknown")
        model_name = usage_data.get("model_name", "unknown")
        input_tokens = usage_data.get("input_tokens", 0)
        output_tokens = usage_data.get("output_tokens", 0)
        
        print(f"💰 模型用量: {provider}/{model_name}")
        print(f"   📥 输入Token: {input_tokens}")
        print(f"   📤 输出Token: {output_tokens}")
        print(f"   📊 总计Token: {input_tokens + output_tokens}")
    
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


async def test_insight_report_generation():
    """测试洞察报告生成"""
    print("=" * 60)
    print("🧪 测试洞察报告生成")
    print("=" * 60)
    
    async with MCPToolCallTester() as tester:
        request = tester.create_insight_report_request("人工智能在教育领域的应用", "insight")
        messages = await tester.send_tool_call_request(request)
        
        print(f"\n✅ 测试完成，共收到 {len(messages)} 条消息")
        return messages


async def test_industry_dynamic_report():
    """测试行业动态报告生成"""
    print("=" * 60)
    print("🧪 测试行业动态报告生成")
    print("=" * 60)
    
    async with MCPToolCallTester() as tester:
        request = tester.create_industry_dynamic_request("新能源汽车", "recent")
        messages = await tester.send_tool_call_request(request)
        
        print(f"\n✅ 测试完成，共收到 {len(messages)} 条消息")
        return messages


async def test_academic_research_report():
    """测试学术研究报告生成"""
    print("=" * 60)
    print("🧪 测试学术研究报告生成")
    print("=" * 60)
    
    async with MCPToolCallTester() as tester:
        request = tester.create_academic_research_request("量子计算在密码学中的应用", "advanced")
        messages = await tester.send_tool_call_request(request)
        
        print(f"\n✅ 测试完成，共收到 {len(messages)} 条消息")
        return messages


async def test_comprehensive_search():
    """测试综合搜索功能"""
    print("=" * 60)
    print("🧪 测试综合搜索功能")
    print("=" * 60)
    
    async with MCPToolCallTester() as tester:
        request = tester.create_search_request("区块链技术在供应链管理中的应用", "comprehensive")
        messages = await tester.send_tool_call_request(request)
        
        print(f"\n✅ 测试完成，共收到 {len(messages)} 条消息")
        return messages


async def test_industry_dynamic_only():
    """只测试行业动态报告生成"""
    print("🚀 开始MCP工具调用格式测试 - 行业动态报告")
    print("=" * 80)
    
    try:
        # 只测试行业动态报告
        messages = await test_industry_dynamic_report()
        
        # 生成测试报告
        print("\n" + "=" * 80)
        print("📊 测试结果汇总")
        print("=" * 80)
        
        print(f"🔧 industry_dynamic: {len(messages)} 条消息")
        
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
        
        return {"industry_dynamic": messages}
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        print(f"详细错误信息:")
        traceback.print_exc()
        return {"industry_dynamic": []}


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
            "name": "generate_insight_report",
            "arguments": {
                "request": {
                    "topic": "人工智能在教育领域的应用",
                    "report_type": "insight",
                    "depth_level": "detailed",
                    "target_audience": "行业专家",
                    "include_citations": True,
                    "max_sections": 8
                }
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
            "name": "generate_industry_dynamic_report",
            "arguments": {
                "industry": "新能源汽车",
                "time_range": "recent",
                "focus_areas": ["市场趋势", "技术创新", "政策影响", "竞争格局"],
                "include_analysis": True,
                "data_sources": ["news", "research", "market_data"],
                # "use_local_data": True  # 注释掉，使用真实网络搜索
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
            "name": "generate_academic_research_report",
            "arguments": {
                "request": {
                    "research_topic": "量子计算在密码学中的应用",
                    "academic_level": "advanced",
                    "research_methodology": "comprehensive",
                    "include_literature_review": True,
                    "citation_style": "academic",
                    "max_pages": 20
                }
            }
        }
    }
    
    print("3. 学术研究报告生成请求:")
    print(json.dumps(academic_request, ensure_ascii=False, indent=2))
    print()
    
    # 综合搜索请求示例
    search_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "comprehensive_search",
            "arguments": {
                "topic": "区块链技术在供应链管理中的应用",
                "search_type": "comprehensive",
                "max_results": 10,
                "days": 30,
                "sources": ["web", "academic", "news"]
            }
        }
    }
    
    print("4. 综合搜索请求:")
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
    """主函数"""
    print("🧪 MCP工具调用格式测试")
    print("=" * 80)
    
    # 显示示例请求和响应
    create_sample_requests()
    create_sample_responses()
    
    # 询问是否运行实际测试
    print("是否运行实际的MCP工具调用测试？(需要服务器运行)")
    print("输入 'y' 或 'yes' 继续，其他任意键跳过...")
    
    # 在实际环境中，这里可以添加用户输入处理
    # 为了演示，我们直接运行测试
    try:
        await test_industry_dynamic_only()
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        print("💡 请确保MCP服务器正在运行 (http://localhost:8001)")


if __name__ == "__main__":
    asyncio.run(main())
