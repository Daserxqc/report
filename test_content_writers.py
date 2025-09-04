#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试内容生成MCP功能
测试outline_writer, summary_writer, content_writer等模块
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入搜索管理器和MCP工具
from search_manager import SearchEngineManager
from mcp_tools import (
    get_tool_registry,
    outline_writer_mcp,
    summary_writer_mcp,
    content_writer_mcp,
    orchestrator_mcp_simple,
    comprehensive_search
)

# 初始化搜索管理器和工具注册表
print("🚀 初始化搜索管理器...")
search_manager = SearchEngineManager()
tool_registry = get_tool_registry(search_manager)
print("✅ 搜索管理器初始化完成")

def print_separator(title):
    """打印分隔符"""
    print("\n" + "="*60)
    print(f"🧪 {title}")
    print("="*60)

def print_result(result, test_name):
    """打印测试结果"""
    print(f"\n📊 {test_name} 测试结果:")
    if isinstance(result, dict):
        if result.get('success') or 'error' not in result:
            print("✅ 测试成功")
            for key, value in result.items():
                if key in ['outline', 'summary', 'content', 'report']:
                    if isinstance(value, str):
                        preview = value[:200] + "..." if len(value) > 200 else value
                        print(f"   📝 {key}: {preview}")
                    elif isinstance(value, dict):
                        print(f"   📝 {key}: {type(value).__name__} with {len(value)} items")
                elif key not in ['session_id', 'timestamp']:
                    if isinstance(value, (str, int, float)):
                        print(f"   📝 {key}: {str(value)[:100]}..." if len(str(value)) > 100 else f"   📝 {key}: {value}")
                    else:
                        print(f"   📝 {key}: {type(value).__name__}")
        else:
            print("❌ 测试失败")
            print(f"   错误: {result.get('error', '未知错误')}")
    else:
        print(f"   结果类型: {type(result).__name__}")
        print(f"   内容: {str(result)[:200]}..." if len(str(result)) > 200 else f"   内容: {result}")

def test_outline_writer():
    """测试大纲生成功能"""
    print_separator("大纲生成功能测试")
    
    # 测试主题
    test_topic = "区块链技术发展现状"
    session_id = f"outline_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"📝 测试主题: {test_topic}")
    print(f"📋 会话ID: {session_id}")
    
    # 首先获取一些搜索结果作为输入
    print("\n🔍 获取搜索结果作为输入...")
    try:
        search_result = comprehensive_search(
            topic=test_topic,
            days=7,
            max_results=3,
            session_id=session_id
        )
        
        search_results = []
        if search_result.get('search_results'):
            search_results = search_result['search_results']
            print(f"✅ 获得 {len(search_results)} 个搜索结果")
        else:
            print("⚠️ 未获得搜索结果，使用模拟数据")
            search_results = [
                {
                    "title": "区块链技术发展报告2024",
                    "content": "区块链技术在2024年取得了重大突破，特别是在去中心化金融和数字身份验证领域。",
                    "url": "https://example.com/blockchain-report",
                    "source": "tech_news"
                }
            ]
    except Exception as e:
        print(f"⚠️ 搜索失败，使用模拟数据: {str(e)}")
        search_results = [
            {
                "title": "区块链技术发展报告2024",
                "content": "区块链技术在2024年取得了重大突破，特别是在去中心化金融和数字身份验证领域。",
                "url": "https://example.com/blockchain-report",
                "source": "tech_news"
            }
        ]
    
    # 测试大纲生成
    print("\n🧪 测试: 大纲生成 (outline_writer_mcp)")
    try:
        outline_result = outline_writer_mcp(
            topic=test_topic,
            search_results=search_results,
            session_id=session_id
        )
        print_result(outline_result, "大纲生成")
        return outline_result
    except Exception as e:
        print(f"❌ 大纲生成测试失败: {str(e)}")
        return None

def test_summary_writer():
    """测试摘要生成功能"""
    print_separator("摘要生成功能测试")
    
    # 测试内容
    test_content = """
    人工智能技术正在快速发展，深度学习、机器学习等技术在各个领域都有广泛应用。
    特别是在自然语言处理、计算机视觉、语音识别等方面取得了重大突破。
    大型语言模型如GPT、BERT等的出现，极大地推动了AI技术的发展。
    同时，AI技术在医疗、金融、教育、交通等行业的应用也越来越广泛。
    然而，AI技术的发展也带来了一些挑战，如数据隐私、算法偏见、就业影响等问题需要关注。
    未来，AI技术将继续快速发展，预计在更多领域实现突破性应用。
    """
    
    session_id = f"summary_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"📝 测试内容长度: {len(test_content)} 字符")
    print(f"📋 会话ID: {session_id}")
    
    # 测试不同长度的摘要生成
    for max_length in [200, 300, 500]:
        print(f"\n🧪 测试: 生成 {max_length} 字符摘要")
        try:
            summary_result = summary_writer_mcp(
                content=test_content,
                max_length=max_length,
                session_id=session_id
            )
            print_result(summary_result, f"{max_length}字符摘要")
        except Exception as e:
            print(f"❌ {max_length}字符摘要生成失败: {str(e)}")

def test_content_writer(outline_result=None):
    """测试内容生成功能"""
    print_separator("内容生成功能测试")
    
    test_topic = "人工智能技术应用"
    session_id = f"content_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"📝 测试主题: {test_topic}")
    print(f"📋 会话ID: {session_id}")
    
    # 准备测试数据
    test_outline = None
    if outline_result and outline_result.get('outline'):
        test_outline = outline_result['outline']
        print("✅ 使用之前生成的大纲")
    else:
        test_outline = {
            "title": "人工智能技术应用报告",
            "sections": [
                {
                    "title": "技术概述",
                    "content": "介绍AI技术的基本概念和发展历程"
                },
                {
                    "title": "应用领域",
                    "content": "分析AI在各行业的具体应用案例"
                },
                {
                    "title": "发展趋势",
                    "content": "预测AI技术的未来发展方向"
                }
            ]
        }
        print("⚠️ 使用模拟大纲数据")
    
    test_search_results = [
        {
            "title": "AI技术应用案例分析",
            "content": "人工智能在医疗诊断、金融风控、智能制造等领域的应用越来越成熟。",
            "url": "https://example.com/ai-applications",
            "source": "research_paper"
        },
        {
            "title": "机器学习发展趋势",
            "content": "深度学习、强化学习等技术正在推动AI应用的边界不断扩展。",
            "url": "https://example.com/ml-trends",
            "source": "tech_news"
        }
    ]
    
    # 测试内容生成
    print("\n🧪 测试: 详细内容生成 (content_writer_mcp)")
    try:
        content_result = content_writer_mcp(
            topic=test_topic,
            outline=test_outline,
            search_results=test_search_results,
            session_id=session_id
        )
        print_result(content_result, "详细内容生成")
        return content_result
    except Exception as e:
        print(f"❌ 内容生成测试失败: {str(e)}")
        return None

def test_simple_orchestrator():
    """测试简单编排器功能"""
    print_separator("简单编排器功能测试")
    
    test_topic = "量子计算发展前景"
    session_id = f"orchestrator_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"📝 测试主题: {test_topic}")
    print(f"📋 会话ID: {session_id}")
    
    # 测试简单编排器
    print("\n🧪 测试: 简单编排器 (orchestrator_mcp_simple)")
    try:
        orchestrator_result = orchestrator_mcp_simple(
            topic=test_topic,
            session_id=session_id
        )
        print_result(orchestrator_result, "简单编排器")
        return orchestrator_result
    except Exception as e:
        print(f"❌ 简单编排器测试失败: {str(e)}")
        return None

def main():
    """主测试函数"""
    print("🚀 开始内容生成MCP功能测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试大纲生成
    outline_result = test_outline_writer()
    
    # 测试摘要生成
    test_summary_writer()
    
    # 测试内容生成
    content_result = test_content_writer(outline_result)
    
    # 测试简单编排器
    orchestrator_result = test_simple_orchestrator()
    
    print_separator("测试完成")
    print("🎉 所有内容生成MCP功能测试已完成")
    print("📝 请查看上述结果以确认各功能是否正常工作")
    
    # 统计测试结果
    tests_completed = 0
    tests_successful = 0
    
    if outline_result:
        tests_completed += 1
        if not outline_result.get('error'):
            tests_successful += 1
    
    if content_result:
        tests_completed += 1
        if not content_result.get('error'):
            tests_successful += 1
    
    if orchestrator_result:
        tests_completed += 1
        if not orchestrator_result.get('error'):
            tests_successful += 1
    
    print(f"\n📊 测试统计: {tests_successful}/{tests_completed + 1} 个功能测试成功")

if __name__ == "__main__":
    main()