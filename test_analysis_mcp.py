#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AnalysisMcp功能
"""

import sys
import os
from pathlib import Path

# 添加collectors路径
collectors_path = Path(__file__).parent / "collectors"
if str(collectors_path) not in sys.path:
    sys.path.insert(0, str(collectors_path))

def test_analysis_mcp():
    """测试AnalysisMcp的基本功能"""
    print("🧪 开始测试AnalysisMcp...")
    
    try:
        # 导入AnalysisMcp
        from collectors.analysis_mcp import AnalysisMcp
        print("✅ 成功导入AnalysisMcp")
        
        # 创建实例
        analysis_mcp = AnalysisMcp()
        print(f"✅ 成功创建AnalysisMcp实例，has_llm: {analysis_mcp.has_llm}")
        
        # 测试数据
        test_data = [
            {
                "title": "人工智能发展趋势",
                "content": "人工智能技术正在快速发展，特别是在机器学习和深度学习领域取得了重大突破。",
                "source": "tech_news.com",
                "url": "https://example.com/ai-trends"
            },
            {
                "title": "AI在医疗领域的应用",
                "content": "人工智能在医疗诊断、药物发现和个性化治疗方面展现出巨大潜力。",
                "source": "medical_journal.com",
                "url": "https://example.com/ai-medical"
            }
        ]
        
        topic = "人工智能发展现状"
        
        # 测试质量分析
        print("\n🔍 测试质量分析...")
        result = analysis_mcp.analyze_quality(
            data=test_data,
            topic=topic,
            evaluation_mode="initial"
        )
        
        print(f"分析类型: {result.analysis_type}")
        print(f"评分: {result.score}")
        print(f"推理: {result.reasoning}")
        print(f"详细信息: {result.details}")
        print(f"元数据: {result.metadata}")
        
        # 测试相关性分析
        print("\n🔍 测试相关性分析...")
        relevance_result = analysis_mcp.analyze_relevance(
            content=test_data[0],
            topic=topic
        )
        
        print(f"相关性分析类型: {relevance_result.analysis_type}")
        print(f"相关性评分: {relevance_result.score}")
        print(f"相关性推理: {relevance_result.reasoning}")
        
        # 测试意图分析
        print("\n🔍 测试意图分析...")
        intent_result = analysis_mcp.analyze_intent(
            user_query="请分析人工智能的发展趋势",
            context="用户想了解AI技术的最新进展"
        )
        
        print(f"意图分析类型: {intent_result.analysis_type}")
        print(f"意图评分: {intent_result.score}")
        print(f"意图推理: {intent_result.reasoning}")
        
        print("\n✅ AnalysisMcp测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_analysis_mcp()