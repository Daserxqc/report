#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试流式响应中的质量评估功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import analysis_mcp, comprehensive_search, _extract_topic_from_task
import json

def test_streaming_quality_assessment():
    """测试流式响应中的质量评估逻辑"""
    print("\n=== 测试流式响应中的质量评估逻辑 ===")
    
    # 模拟流式响应中的步骤
    task = "分析人工智能在医疗领域的最新发展"
    topic = _extract_topic_from_task(task)
    print(f"提取的主题: {topic}")
    
    # 步骤1: 获取搜索结果
    print("\n1. 获取搜索结果...")
    search_result = comprehensive_search(topic, 7, 4)
    print(f"搜索结果类型: {type(search_result)}")
    print(f"搜索结果长度: {len(search_result) if search_result else 0}")
    print(f"搜索结果前200字符: {str(search_result)[:200]}...")
    
    # 步骤2: 准备评估数据（模拟流式响应中的逻辑）
    print("\n2. 准备评估数据...")
    evaluation_data = [{"title": "搜索结果汇总", "content": str(search_result)[:800], "source": "综合搜索"}]
    print(f"评估数据: {evaluation_data}")
    
    # 步骤3: 执行质量评估
    print("\n3. 执行质量评估...")
    try:
        quality_result = analysis_mcp("quality", evaluation_data, topic)
        print(f"质量评估结果: {quality_result}")
        
        # 解析结果
        quality_data = json.loads(quality_result)
        current_score = quality_data.get('score', 0)
        print(f"质量评分: {current_score}/10")
        print(f"评估详情: {quality_data.get('details', {})}")
        
        if current_score > 0:
            print("✅ 流式响应质量评估成功")
        else:
            print("❌ 流式响应质量评估失败，评分为0")
            
    except Exception as e:
        print(f"❌ 质量评估出错: {str(e)}")
        import traceback
        traceback.print_exc()

def test_direct_quality_with_string_data():
    """测试直接使用字符串数据进行质量评估"""
    print("\n=== 测试直接使用字符串数据进行质量评估 ===")
    
    # 模拟字符串格式的搜索结果
    string_data = """
    标题: 人工智能在医疗诊断中的应用
    内容: 人工智能技术在医疗领域的应用越来越广泛，特别是在医疗诊断方面取得了显著进展。
    来源: 医疗科技网
    URL: https://example.com/ai-medical
    
    标题: 机器学习辅助药物发现
    内容: 机器学习算法能够加速新药研发过程，通过分析大量分子数据来预测药物效果。
    来源: 生物技术期刊
    URL: https://example.com/ml-drug
    """
    
    topic = "人工智能医疗应用"
    
    try:
        # 直接传递字符串数据
        quality_result = analysis_mcp("quality", string_data, topic)
        print(f"质量评估结果: {quality_result}")
        
        # 解析结果
        quality_data = json.loads(quality_result)
        current_score = quality_data.get('score', 0)
        print(f"质量评分: {current_score}/10")
        
        if current_score > 0:
            print("✅ 字符串数据质量评估成功")
        else:
            print("❌ 字符串数据质量评估失败，评分为0")
            
    except Exception as e:
        print(f"❌ 字符串数据质量评估出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始测试流式响应质量评估功能...")
    
    test_streaming_quality_assessment()
    test_direct_quality_with_string_data()
    
    print("\n测试完成！")