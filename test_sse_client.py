#!/usr/bin/env python3
"""
测试SSE流式响应的客户端
"""

import requests
import json
import time
import os
from datetime import datetime

def save_report(result, session_id):
    """保存生成的报告到文件"""
    try:
        # 创建reports目录
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}_{session_id[:8] if session_id else 'unknown'}.json"
        filepath = os.path.join(reports_dir, filename)
        
        # 保存完整结果
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"💾 报告已保存到: {filepath}")
        
        # 保存纯文本版本
        text_filename = f"report_{timestamp}_{session_id[:8] if session_id else 'unknown'}.txt"
        text_filepath = os.path.join(reports_dir, text_filename)
        
        with open(text_filepath, 'w', encoding='utf-8') as f:
            # 从不同可能的结构中提取内容
            structured_content = result.get("structuredContent", {})
            metadata = structured_content.get("metadata", {})
            
            # 写入基本信息
            f.write(f"# {metadata.get('topic', '报告')}\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"会话ID: {session_id}\n")
            f.write(f"质量评分: {metadata.get('final_quality_score', 0):.2f}/10\n\n")
            f.write("=" * 60 + "\n\n")
            
            # 尝试从不同位置提取报告内容
            report_content = None
            
            # 方法1: 从structuredContent.report_content
            if "report_content" in structured_content:
                report_content = structured_content["report_content"]
            
            # 方法2: 从content数组中的text
            elif "content" in result and isinstance(result["content"], list):
                for item in result["content"]:
                    if isinstance(item, dict) and item.get("type") == "text":
                        report_content = item.get("text", "")
                        break
            
            # 方法3: 从sections数组
            elif "sections" in structured_content:
                sections = structured_content["sections"]
                if sections:
                    for section in sections:
                        f.write(f"## {section.get('title', '未知章节')}\n\n")
                        f.write(f"{section.get('content', '')}\n\n")
                        f.write("-" * 40 + "\n\n")
                    report_content = "已按章节保存"
            
            # 如果找到了报告内容，直接写入
            if report_content and report_content != "已按章节保存":
                f.write(report_content)
            elif not report_content:
                f.write("未找到报告内容\n")
                f.write(f"可用键: {list(result.keys())}\n")
                f.write(f"结构化内容键: {list(structured_content.keys())}\n")
        
        print(f"📄 文本版本已保存到: {text_filepath}")
            
    except Exception as e:
        print(f"❌ 保存报告失败: {e}")
        import traceback
        traceback.print_exc()

def display_analysis_results(result):
    """显示analysis_mcp的评估结果"""
    try:
        print("\n" + "=" * 60)
        print("📊 Analysis MCP 评估结果详情")
        print("=" * 60)
        
        # 首先显示收集到的实时analysis结果
        if "collected_analysis_results" in result and result["collected_analysis_results"]:
            print(f"\n🔍 实时分析结果 (共{len(result['collected_analysis_results'])}条):")
            for i, analysis_item in enumerate(result["collected_analysis_results"], 1):
                analysis = analysis_item["analysis"]
                print(f"\n   [{i}] {analysis_item['timestamp'][:19]}")
                if "score" in analysis:
                    print(f"       评分: {analysis['score']:.2f}/10")
                if "analysis_type" in analysis:
                    print(f"       类型: {analysis['analysis_type']}")
                if "reasoning" in analysis:
                    reasoning = analysis['reasoning'][:100] + "..." if len(analysis['reasoning']) > 100 else analysis['reasoning']
                    print(f"       原因: {reasoning}")
                if "quality_dimensions" in analysis:
                    dims = analysis["quality_dimensions"]
                    print(f"       质量维度:")
                    for dim, score in dims.items():
                        print(f"         {dim}: {score:.2f}/10")
                if "search_sources" in analysis:
                    sources = analysis["search_sources"]
                    print(f"       搜索源: {len(sources)}个来源")
                if "data_stats" in analysis:
                    stats = analysis["data_stats"]
                    print(f"       数据统计: {stats}")
        else:
            print("\n⚠️  未收集到实时analysis结果")
        
        # 查找分析结果
        analysis_results = []
        
        # 从structuredContent中查找分析数据
        structured_content = result.get("structuredContent", {})
        metadata = structured_content.get("metadata", {})
        
        # 显示整体质量评估
        if "quality_analysis" in metadata:
            quality_data = metadata["quality_analysis"]
            print("\n🎯 整体质量评估:")
            if isinstance(quality_data, dict):
                for key, value in quality_data.items():
                    if isinstance(value, (int, float)):
                        print(f"  - {key}: {value:.2f}")
                    else:
                        print(f"  - {key}: {value}")
        
        # 显示各章节的评估结果
        sections = structured_content.get("sections", [])
        for i, section in enumerate(sections, 1):
            section_metadata = section.get("metadata", {})
            if section_metadata:
                print(f"\n📝 章节 {i}: {section.get('title', '未知章节')}")
                
                # 显示质量评分
                if "quality_score" in section_metadata:
                    score = section_metadata["quality_score"]
                    print(f"  📈 质量评分: {score:.2f}/10")
                
                # 显示相关性分析
                if "relevance_analysis" in section_metadata:
                    rel_data = section_metadata["relevance_analysis"]
                    if isinstance(rel_data, dict):
                        print(f"  🎯 相关性分析:")
                        for key, value in rel_data.items():
                            if isinstance(value, (int, float)):
                                print(f"    - {key}: {value:.2f}")
                            elif isinstance(value, list) and len(value) <= 5:
                                print(f"    - {key}: {', '.join(map(str, value))}")
                            elif isinstance(value, str) and len(value) <= 100:
                                print(f"    - {key}: {value}")
                
                # 显示其他分析结果
                analysis_keys = ["credibility_analysis", "completeness_analysis", "timeliness_analysis"]
                for key in analysis_keys:
                    if key in section_metadata:
                        analysis_data = section_metadata[key]
                        if isinstance(analysis_data, dict) and "score" in analysis_data:
                            score = analysis_data["score"]
                            print(f"  📊 {key.replace('_analysis', '').title()}: {score:.2f}/10")
        
        # 显示搜索和数据源分析
        if "search_analysis" in metadata:
            search_data = metadata["search_analysis"]
            print(f"\n🔍 搜索质量分析:")
            if isinstance(search_data, dict):
                for key, value in search_data.items():
                    if isinstance(value, (int, float)):
                        print(f"  - {key}: {value:.2f}")
                    elif isinstance(value, list) and len(value) <= 10:
                        print(f"  - {key}: {', '.join(map(str, value))}")
                    elif isinstance(value, str) and len(value) <= 200:
                        print(f"  - {key}: {value}")
        
        # 显示改进建议
        if "improvement_suggestions" in metadata:
            suggestions = metadata["improvement_suggestions"]
            if isinstance(suggestions, list) and suggestions:
                print(f"\n💡 改进建议:")
                for i, suggestion in enumerate(suggestions[:5], 1):
                    print(f"  {i}. {suggestion}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ 显示分析结果失败: {e}")

# 全局变量收集analysis结果
analysis_results_collection = []

def test_sse_streaming(show_raw_json=False):
    """测试SSE流式响应"""
    global analysis_results_collection
    analysis_results_collection = []  # 重置收集器
    
    print("🧪 开始测试SSE流式响应...")
    if show_raw_json:
        print("📋 模式: 显示原始JSON消息")
    else:
        print("📋 模式: 友好格式显示")
    
    # 准备请求数据 - 设置高质量目标触发迭代
    request_data = {
        "task": "生成AI Agent领域最近一周的行业重大事件报告",
        "task_type": "news_report",
        "kwargs": {
            "days": 7,
            "quality_threshold": 8.5,  # 🎯 提高到8.5触发迭代优化
            "max_iterations": 4,       # 🔄 允许4轮迭代
            "auto_confirm": True
        }
    }
    
    url = "http://localhost:8001/mcp/streaming/orchestrator"
    
    try:
        print(f"📡 连接到: {url}")
        print(f"📋 任务: {request_data['task']}")
        print("=" * 60)
        
        # 发送POST请求并接收流式响应
        response = requests.post(
            url, 
            json=request_data,
            stream=True,
            headers={
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            },
            timeout=300  # 5分钟超时
        )
        
        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return
        
        print(f"✅ 连接成功，开始接收流式数据...")
        print()
        
        session_id = None
        message_count = 0
        
        # 处理流式响应
        for line in response.iter_lines(decode_unicode=True):
            if line.strip():
                if line.startswith("data: "):
                    try:
                        # 解析JSON数据
                        data_str = line[6:]  # 移除 "data: " 前缀
                        data = json.loads(data_str)
                        message_count += 1
                        
                        # 如果启用原始JSON显示
                        if show_raw_json:
                            print(f"\n📋 消息 #{message_count}:")
                            print(f"```json")
                            print(json.dumps(data, indent=2, ensure_ascii=False))
                            print("```")
                            continue
                        
                        # 提取会话ID
                        if not session_id and data.get("method") == "session/started":
                            session_id = data.get("params", {}).get("session_id")
                            print(f"🔗 会话ID: {session_id}")
                        
                        # 处理不同类型的消息
                        method = data.get("method", "")
                        
                        if method == "notifications/message":
                            params = data.get("params", {})
                            level = params.get("level", "info")
                            msg_data = params.get("data", {}).get("msg", {})
                            
                            # 检查是否是模型用量消息
                            if msg_data.get("type") == "model_usage":
                                usage_data = msg_data.get("data", {})
                                provider = usage_data.get("model_provider", "unknown")
                                model = usage_data.get("model_name", "unknown")
                                input_tokens = usage_data.get("input_tokens", 0)
                                output_tokens = usage_data.get("output_tokens", 0)
                                
                                timestamp = datetime.now().strftime("%H:%M:%S")
                                print(f"📊 [{timestamp}] 模型用量: {provider}/{model} ({input_tokens}→{output_tokens} tokens)")
                                continue
                            
                            status = msg_data.get("status", "")
                            message = msg_data.get("message", "")
                            details = msg_data.get("details", {})
                            
                            # 格式化输出
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            
                            if level == "error":
                                print(f"❌ [{timestamp}] {message}")
                            elif "completed" in status:
                                print(f"✅ [{timestamp}] {message}")
                            elif "started" in status:
                                print(f"🚀 [{timestamp}] {message}")
                            elif status == "generating_sections":
                                section_name = details.get("name", "未知章节")
                                section_id = details.get("id", "")
                                content_preview = details.get("content", "")[:100]
                                
                                if content_preview:
                                    print(f"📝 [{timestamp}] 完成章节生成: {section_name}")
                                    print(f"    💡 内容预览: {content_preview}...")
                                else:
                                    print(f"🚀 [{timestamp}] 开始生成章节: {section_name}")
                            else:
                                print(f"📡 [{timestamp}] {message}")
                            
                            # 显示详细信息（如果有）
                            if details and status != "generating_sections":
                                if "step" in details:
                                    step = details["step"]
                                    total = details.get("total_steps", "?")
                                    print(f"    📊 进度: {step}/{total}")
                                
                                if "quality_score" in details:
                                    score = details["quality_score"]
                                    print(f"    📈 质量评分: {score:.2f}/10")
                                
                                if "sections_count" in details:
                                    count = details["sections_count"]
                                    print(f"    📋 章节数量: {count}")
                                
                                if "intent" in details:
                                    intent = details["intent"]
                                    print(f"    🎯 识别意图: {intent}")
                                
                                # 显示analysis_mcp的评估结果
                                if "analysis_result" in details:
                                    analysis = details["analysis_result"]
                                    if isinstance(analysis, dict):
                                        # 收集analysis结果
                                        analysis_results_collection.append({
                                            "timestamp": datetime.now().isoformat(),
                                            "message": message,
                                            "analysis": analysis.copy()
                                        })
                                        
                                        if "score" in analysis:
                                            print(f"    🔍 分析评分: {analysis['score']:.2f}/10")
                                        if "analysis_type" in analysis:
                                            print(f"    📊 分析类型: {analysis['analysis_type']}")
                                        if "reasoning" in analysis and len(analysis['reasoning']) <= 100:
                                            print(f"    💭 分析原因: {analysis['reasoning']}")
                                
                                # 显示质量维度详情
                                quality_dimensions = ["relevance", "credibility", "completeness", "timeliness", "diversity"]
                                for dim in quality_dimensions:
                                    if dim in details:
                                        value = details[dim]
                                        if isinstance(value, (int, float)):
                                            print(f"    📈 {dim.title()}: {value:.2f}/10")
                                
                                # 显示搜索源信息
                                if "search_sources" in details:
                                    sources = details["search_sources"]
                                    if isinstance(sources, list) and sources:
                                        print(f"    🔍 搜索源: {', '.join(sources[:3])}{'...' if len(sources) > 3 else ''}")
                                
                                # 显示数据统计
                                if "data_count" in details:
                                    count = details["data_count"]
                                    print(f"    📊 数据条数: {count}")
                        
                        elif data.get("result"):  # 最终成功结果
                            print(f"🎉 [{datetime.now().strftime('%H:%M:%S')}] 任务完成!")
                            result = data.get("result", {})
                            structured_content = result.get("structuredContent", {})
                            metadata = structured_content.get("metadata", {})
                            
                            print(f"    📊 最终统计:")
                            print(f"    - 主题: {metadata.get('topic', '未知')}")
                            print(f"    - 章节数: {metadata.get('sections_count', 0)}")
                            print(f"    - 质量评分: {metadata.get('final_quality_score', 0):.2f}/10")
                            
                            # 保存完整报告（包含收集的analysis结果）
                            enhanced_result = result.copy()
                            if analysis_results_collection:
                                enhanced_result["collected_analysis_results"] = analysis_results_collection
                            save_report(enhanced_result, session_id)
                            
                            # 显示analysis_mcp评估结果
                            display_analysis_results(enhanced_result)
                        
                        elif data.get("error"):  # 错误信息
                            error_info = data.get("error", {})
                            error_code = error_info.get("code", -1)
                            error_message = error_info.get("message", "Unknown error")
                            error_data = error_info.get("data", {})
                            error_type = error_data.get("type", "unknown")
                            detailed_message = error_data.get("message", "")
                            
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            print(f"❌ [{timestamp}] 错误 [{error_code}]: {error_message}")
                            print(f"    🔍 错误类型: {error_type}")
                            print(f"    📝 详细信息: {detailed_message}")
                            
                        elif method == "session/completed":
                            print(f"🏁 [{datetime.now().strftime('%H:%M:%S')}] 会话结束")
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON解析失败: {e}")
                        print(f"原始数据: {line}")
                    except Exception as e:
                        print(f"⚠️ 处理消息失败: {e}")
        
        print()
        print("=" * 60)
        print(f"📊 测试完成统计:")
        print(f"- 会话ID: {session_id}")
        print(f"- 接收消息数: {message_count}")
        print(f"- 用时: {datetime.now().strftime('%H:%M:%S')}")
        
        # 查询会话状态
        if session_id:
            print(f"\n🔍 查询会话状态...")
            status_url = f"http://localhost:8001/mcp/streaming/sessions/{session_id}"
            status_response = requests.get(status_url)
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"✅ 会话状态: {json.dumps(status_data, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ 查询状态失败: {status_response.status_code}")
        
    except requests.exceptions.Timeout:
        print("⏰ 请求超时")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保MCP服务器正在运行")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def test_simple_connection():
    """测试简单连接"""
    try:
        response = requests.get("http://localhost:8001/docs")
        if response.status_code == 200:
            print("✅ FastAPI服务器运行正常")
            return True
        else:
            print(f"⚠️ FastAPI服务器响应异常: {response.status_code}")
            return False
    except:
        print("❌ 无法连接到FastAPI服务器")
        return False

if __name__ == "__main__":
    import sys
    
    print("🧪 MCP SSE流式响应测试客户端")
    print("=" * 60)
    
    # 检查命令行参数
    show_raw = "--raw" in sys.argv or "-r" in sys.argv
    
    # 首先测试连接
    if test_simple_connection():
        print()
        test_sse_streaming(show_raw_json=show_raw)
    else:
        print("\n💡 请先启动MCP服务器:")
        print("   python main.py")
        print("\n💡 使用方法:")
        print("   python test_sse_client.py          # 友好格式显示")
        print("   python test_sse_client.py --raw    # 显示原始JSON")
