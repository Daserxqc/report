#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试标准MCP工具调用协议格式
包含完整的MCP协议请求和响应处理示例
"""

import json
import requests
import time
from typing import Dict, Any

def create_mcp_insight_report_request() -> Dict[str, Any]:
    """创建洞察报告生成的MCP工具调用请求"""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "generate_insights_report",
            "arguments": {
                "request": {
                    "topic": "AI Agent领域最近一周的行业重大事件报告",
                    "report_type": "insight",
                    "time_range": "recent_week",
                    "quality_threshold": 0.8,
                    "max_iterations": 3,
                    "include_citations": True,
                    "language": "zh-CN"
                }
            }
        }
    }

def create_mcp_industry_report_request() -> Dict[str, Any]:
    """创建行业动态报告的MCP工具调用请求"""
    return {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "generate_industry_report",
            "arguments": {
                "request": {
                    "industry": "人工智能",
                    "focus_area": "医疗健康应用",
                    "report_depth": "comprehensive",
                    "include_market_analysis": True,
                    "include_technology_trends": True,
                    "target_audience": "专业投资者"
                }
            }
        }
    }

def create_mcp_research_report_request() -> Dict[str, Any]:
    """创建学术研究报告的MCP工具调用请求"""
    return {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "generate_research_report",
            "arguments": {
                "request": {
                    "research_topic": "大语言模型在科学研究中的应用",
                    "academic_level": "graduate",
                    "citation_style": "APA",
                    "min_references": 20,
                    "include_methodology": True,
                    "include_future_work": True
                }
            }
        }
    }

def create_mcp_search_request() -> Dict[str, Any]:
    """创建搜索检索的MCP工具调用请求"""
    return {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "comprehensive_search",
            "arguments": {
                "request": {
                    "query": "ChatGPT-4o 最新功能更新",
                    "search_sources": ["academic", "news", "official"],
                    "max_results": 10,
                    "time_filter": "past_month",
                    "language_preference": "zh-CN",
                    "quality_filter": "high"
                }
            }
        }
    }

def parse_progress_update(message: Dict[str, Any]) -> None:
    """解析进度更新消息"""
    if (message.get("method") == "notifications/message" and 
        "msg" in message.get("params", {}).get("data", {}) and
        message["params"]["data"]["msg"].get("type") != "model_usage"):
        
        msg = message["params"]["data"]["msg"]
        status = msg.get("status", "unknown")
        message_text = msg.get("message", "")
        details = msg.get("details", {})
        
        print(f"📊 进度更新: {status}")
        print(f"   消息: {message_text}")
        
        if details:
            if "name" in details:
                print(f"   章节: {details['name']}")
            if "content" in details:
                content_preview = details["content"][:100] + "..." if len(details["content"]) > 100 else details["content"]
                print(f"   内容预览: {content_preview}")
        print("---")

def parse_model_usage(message: Dict[str, Any]) -> None:
    """解析模型用量消息"""
    if (message.get("method") == "notifications/message" and 
        message.get("params", {}).get("data", {}).get("msg", {}).get("type") == "model_usage"):
        
        usage_data = message["params"]["data"]["msg"]["data"]
        
        print(f"🤖 模型用量:")
        print(f"   提供商: {usage_data.get('model_provider', 'unknown')}")
        print(f"   模型: {usage_data.get('model_name', 'unknown')}")
        print(f"   输入Token: {usage_data.get('input_tokens', 0)}")
        print(f"   输出Token: {usage_data.get('output_tokens', 0)}")
        print("---")

def parse_error_message(message: Dict[str, Any]) -> None:
    """解析错误消息"""
    if "error" in message:
        error = message["error"]
        print(f"❌ 错误信息:")
        print(f"   代码: {error.get('code', 'unknown')}")
        print(f"   消息: {error.get('message', 'unknown')}")
        
        if "data" in error:
            error_data = error["data"]
            print(f"   类型: {error_data.get('type', 'unknown')}")
            print(f"   详情: {error_data.get('message', 'unknown')}")
        print("---")

def convert_api_to_mcp_format(task: str, task_type: str = "auto", **kwargs) -> Dict[str, Any]:
    """将现有API格式转换为标准MCP协议格式"""
    # 根据任务内容确定MCP工具名称
    tool_name_mapping = {
        "洞察报告": "generate_insights_report",
        "行业动态": "generate_industry_report", 
        "学术研究": "generate_research_report",
        "搜索": "comprehensive_search",
        "检索": "comprehensive_search"
    }
    
    # 默认工具名称
    tool_name = "generate_insights_report"
    
    # 根据任务内容匹配工具名称
    for keyword, name in tool_name_mapping.items():
        if keyword in task:
            tool_name = name
            break
    
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": {
                "request": {
                    "task": task,
                    "task_type": task_type,
                    **kwargs
                }
            }
        }
    }

def test_mcp_protocol_format():
    """测试MCP协议格式的完整流程"""
    print("🧪 开始测试MCP协议格式...\n")
    
    # 测试不同类型的MCP请求
    test_requests = [
        ("洞察报告", create_mcp_insight_report_request()),
        ("行业动态报告", create_mcp_industry_report_request()),
        ("学术研究报告", create_mcp_research_report_request()),
        ("搜索检索", create_mcp_search_request())
    ]
    
    for request_name, request_data in test_requests:
        print(f"📋 {request_name} MCP请求格式:")
        print(json.dumps(request_data, ensure_ascii=False, indent=2))
        print("\n" + "="*50 + "\n")
    
    # 演示API格式转换为MCP格式
    print("🔄 API格式转MCP格式示例:\n")
    
    api_examples = [
        {
            "task": "生成AI Agent领域最近一周的行业重大事件洞察报告",
            "task_type": "auto",
            "quality_threshold": 0.8,
            "max_iterations": 3
        },
        {
            "task": "检索ChatGPT最新功能更新信息",
            "task_type": "search",
            "max_results": 10
        }
    ]
    
    for i, api_data in enumerate(api_examples, 1):
        task = api_data.pop("task")
        task_type = api_data.pop("task_type", "auto")
        
        print(f"示例 {i} - 原始API格式:")
        original_format = {"task": task, "task_type": task_type, **api_data}
        print(json.dumps(original_format, ensure_ascii=False, indent=2))
        
        print(f"\n转换后的MCP格式:")
        mcp_format = convert_api_to_mcp_format(task, task_type, **api_data)
        print(json.dumps(mcp_format, ensure_ascii=False, indent=2))
        print("\n" + "-"*40 + "\n")
    
    # 模拟SSE响应处理
    print("🌊 模拟SSE响应处理示例:\n")
    
    # 示例进度更新消息
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
                        "content": "## 二、市场分析\n\n当前AI Agent市场呈现快速增长态势，主要驱动因素包括：\n- 企业数字化转型需求增加\n- 大语言模型技术成熟\n- 成本效益显著提升"
                    }
                },
                "extra": None
            }
        },
        "jsonrpc": "2.0"
    }
    
    # 示例模型用量消息
    usage_message = {
        "jsonrpc": "2.0",
        "method": "notifications/message",
        "params": {
            "data": {
                "msg": {
                    "type": "model_usage",
                    "data": {
                        "model_provider": "doubao",
                        "model_name": "doubao-1-5-pro-32k-250115",
                        "input_tokens": 1250,
                        "output_tokens": 2100
                    }
                }
            }
        }
    }
    
    # 示例错误消息
    error_message = {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32603,
            "message": "Internal error",
            "data": {
                "type": "report_generation_failed",
                "message": "报告生成模型未能返回有效内容，请检查输入参数。"
            }
        }
    }
    
    # 解析各种消息类型
    parse_progress_update(progress_message)
    parse_model_usage(usage_message)
    parse_error_message(error_message)

def test_real_mcp_call(endpoint_url: str = "http://localhost:8001/mcp/streaming/orchestrator"):
    """测试真实的MCP调用并保存生成的报告"""
    print(f"🚀 尝试连接MCP服务器: {endpoint_url}\n")
    
    try:
        # 适配现有API格式的请求
        api_request_data = {
            "task": "生成AI Agent领域最近一周的行业重大事件报告",
            "task_type": "auto",
            "kwargs": {
                "quality_threshold": 0.8,
                "max_iterations": 3
            }
        }
        
        print("📋 发送的API请求格式:")
        print(json.dumps(api_request_data, ensure_ascii=False, indent=2))
        print("\n" + "="*40 + "\n")
        
        # 发送请求
        response = requests.post(
            endpoint_url,
            json=api_request_data,
            stream=True,
            timeout=600,  # 10分钟超时，给报告生成足够时间
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ 成功连接MCP服务器，开始接收SSE流...\n")
            
            message_count = 0
            report_content = ""
            report_sections = []
            final_report_received = False
            
            try:
                for line in response.iter_lines(decode_unicode=True, chunk_size=1024):
                    if not line or not line.strip():
                        continue
                    
                    # 处理SSE事件
                    if line.startswith('event: '):
                        event_type = line[7:].strip()
                        print(f"🎯 SSE事件类型: {event_type}")
                        continue
                        
                    if line.startswith('data: '):
                        try:
                            json_str = line[6:].strip()
                            if not json_str or json_str == '[DONE]':
                                print("🏁 接收到流结束标记")
                                break
                                
                            data = json.loads(json_str)
                            message_count += 1
                            
                            # 打印原始消息用于调试
                            print(f"🔍 [调试] 收到消息 #{message_count}: {json.dumps(data, ensure_ascii=False)[:200]}...")
                            
                            # 解析不同类型的消息
                            parse_progress_update(data)
                            parse_model_usage(data)
                            parse_error_message(data)
                            
                            # 收集报告内容 - 更全面的解析
                            if 'method' in data:
                                if data['method'] == 'notifications/message':
                                    params = data.get('params', {})
                                    msg_data = params.get('data', {})
                                    msg = msg_data.get('msg', {})
                                    
                                    # 检查是否是章节内容
                                    if 'details' in msg and isinstance(msg['details'], dict) and 'content' in msg['details']:
                                        section_content = msg['details']['content']
                                        report_sections.append(section_content)
                                        print(f"📝 收集到章节内容: {len(section_content)} 字符")
                                    
                                    # 检查是否是最终报告
                                    if 'final_report' in msg:
                                        report_content = msg['final_report']
                                        final_report_received = True
                                        print(f"📄 收到最终报告: {len(report_content)} 字符")
                                    
                                    # 检查消息内容是否包含报告文本
                                    if isinstance(msg, str) and len(msg) > 100:
                                        report_sections.append(msg)
                                        print(f"📝 收集到消息内容: {len(msg)} 字符")
                                    
                                    # 检查status字段是否包含报告内容
                                    if 'status' in msg and isinstance(msg['status'], str) and len(msg['status']) > 500:
                                        report_sections.append(msg['status'])
                                        print(f"📝 从status收集到内容: {len(msg['status'])} 字符")
                                
                                elif data['method'] == 'notifications/progress':
                                    # 处理进度通知
                                    params = data.get('params', {})
                                    if 'message' in params:
                                        print(f"📊 进度: {params['message']}")
                                
                                elif data['method'] == 'notifications/result':
                                    # 处理结果通知
                                    params = data.get('params', {})
                                    if 'result' in params and isinstance(params['result'], str) and len(params['result']) > 100:
                                        report_content = params['result']
                                        final_report_received = True
                                        print(f"📄 从notifications/result收到报告: {len(report_content)} 字符")
                            
                            # 检查是否有直接的报告内容
                            if 'result' in data and isinstance(data['result'], str) and len(data['result']) > 100:
                                report_content = data['result']
                                final_report_received = True
                                print(f"📄 从result字段收到报告: {len(report_content)} 字符")
                            
                            # 检查params中是否有报告内容
                            if 'params' in data and isinstance(data['params'], dict):
                                params = data['params']
                                if 'report' in params and isinstance(params['report'], str) and len(params['report']) > 100:
                                    report_content = params['report']
                                    final_report_received = True
                                    print(f"📄 从params.report收到报告: {len(report_content)} 字符")
                            
                        except json.JSONDecodeError as e:
                            print(f"⚠️ JSON解析错误: {e}")
                            print(f"   原始数据: {line[:200]}...")
                        except Exception as e:
                            print(f"⚠️ 消息处理错误: {e}")
                            print(f"   原始数据: {line[:200]}...")
                            
            except Exception as stream_error:
                print(f"⚠️ 流处理异常: {stream_error}")
                print(f"📊 已处理消息数: {message_count}")
            
            print(f"\n🎉 SSE流处理完成！共接收到 {message_count} 条消息")
            print(f"📊 收集状态: 最终报告={final_report_received}, 章节数量={len(report_sections)}")
            
            # 保存报告到文件
            import os
            from datetime import datetime
            
            # 确保reports目录存在
            reports_dir = "reports"
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"AI_Agent行业报告_{timestamp}.md"
            filepath = os.path.join(reports_dir, filename)
            
            # 准备要保存的内容
            if report_content:
                content_to_save = report_content
                print(f"💾 使用最终报告内容: {len(content_to_save)} 字符")
            elif report_sections:
                content_to_save = "\n\n".join(report_sections)
                print(f"💾 合并章节内容: {len(content_to_save)} 字符")
            else:
                content_to_save = f"# AI Agent领域行业报告\n\n⚠️ 未能获取到完整的报告内容。\n\n## 调试信息\n- 接收消息数: {message_count}\n- 最终报告: {final_report_received}\n- 章节数量: {len(report_sections)}\n\n请检查服务器响应格式。"
                print("⚠️ 未能获取到报告内容，将保存调试信息")
            
            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content_to_save)
            
            print(f"\n💾 报告已保存到: {filepath}")
            print(f"📊 报告长度: {len(content_to_save)} 字符")
            
            return filepath
            
        else:
            print(f"❌ 服务器响应错误: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到MCP服务器，请确保服务器正在运行")
        return None
    except requests.exceptions.Timeout:
        print("⏰ 请求超时，服务器可能正在处理中...")
        return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

if __name__ == "__main__":
    print("🔧 MCP协议格式测试工具\n")
    
    # 运行协议格式测试
    test_mcp_protocol_format()
    
    print("\n" + "="*60)
    print("\n🚀 开始测试真实MCP服务器连接...")
    
    # 直接测试MCP服务器连接
    result_file = test_real_mcp_call()
    
    if result_file:
        print(f"\n✅ 测试成功！报告已保存到: {result_file}")
    else:
        print("\n❌ 测试失败，请检查服务器状态")
    
    print("\n✨ 测试完成！")