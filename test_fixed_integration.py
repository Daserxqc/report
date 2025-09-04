#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的搜索-分析集成功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入必要的模块
from main import comprehensive_search, analysis_mcp
from parse_search_results import _parse_search_result_string
import json

def test_search_result_parsing():
    """测试搜索结果解析功能"""
    print("\n=== 测试搜索结果解析功能 ===")
    
    # 模拟搜索结果字符串
    test_search_result = """
标题: 人工智能发展现状分析
来源: https://example.com/ai-development
内容: 人工智能技术在近年来取得了显著进展，深度学习、机器学习等技术日趋成熟...

标题: 机器学习在医疗领域的应用
来源: https://medical-ai.com/ml-healthcare
内容: 机器学习技术在医疗诊断、药物发现、个性化治疗等方面展现出巨大潜力...

标题: 自然语言处理技术突破
来源: https://nlp-research.org/breakthroughs
内容: 大型语言模型的出现为自然语言处理带来了革命性变化，ChatGPT等应用...
    """
    
    try:
        parsed_results = _parse_search_result_string(test_search_result)
        print(f"✅ 解析成功，得到 {len(parsed_results)} 条结构化数据")
        
        for i, result in enumerate(parsed_results, 1):
            print(f"[{i}] 标题: {result.get('title', 'N/A')}")
            print(f"    来源: {result.get('source', 'N/A')}")
            print(f"    内容长度: {len(result.get('content', ''))} 字符")
            print()
        
        return parsed_results
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return []

def test_analysis_with_parsed_data():
    """测试使用解析后数据进行分析"""
    print("\n=== 测试分析功能（解析后数据）===")
    
    # 使用解析后的数据进行质量分析
    parsed_data = test_search_result_parsing()
    
    if not parsed_data:
        print("❌ 没有解析数据，跳过分析测试")
        return
    
    try:
        analysis_result = analysis_mcp(
            analysis_type="quality",
            data=parsed_data,
            topic="人工智能技术发展",
            evaluation_mode="initial"
        )
        
        print("✅ 分析完成")
        result_data = json.loads(analysis_result)
        print(f"评分: {result_data.get('score', 'N/A')}/10")
        print(f"分析类型: {result_data.get('analysis_type', 'N/A')}")
        print(f"推理: {result_data.get('reasoning', 'N/A')[:100]}...")
        
        return result_data
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return None

def test_analysis_with_string_data():
    """测试直接使用字符串数据进行分析"""
    print("\n=== 测试分析功能（字符串数据）===")
    
    # 模拟搜索结果字符串
    search_string = """
标题: 深度学习技术进展
来源: https://deeplearning.ai/progress
内容: 深度学习在计算机视觉、自然语言处理等领域取得重大突破，Transformer架构...

标题: 强化学习应用案例
来源: https://rl-applications.com/cases
内容: 强化学习在游戏AI、自动驾驶、机器人控制等领域展现出强大能力...
    """
    
    try:
        analysis_result = analysis_mcp(
            analysis_type="quality",
            data=search_string,
            topic="人工智能技术发展",
            evaluation_mode="initial"
        )
        
        print("✅ 字符串数据分析完成")
        result_data = json.loads(analysis_result)
        print(f"评分: {result_data.get('score', 'N/A')}/10")
        print(f"分析类型: {result_data.get('analysis_type', 'N/A')}")
        print(f"推理: {result_data.get('reasoning', 'N/A')[:100]}...")
        
        return result_data
        
    except Exception as e:
        print(f"❌ 字符串数据分析失败: {e}")
        return None

def test_full_search_analysis_workflow():
    """测试完整的搜索-分析工作流"""
    print("\n=== 测试完整搜索-分析工作流 ===")
    
    try:
        # 执行搜索
        print("🔍 执行搜索...")
        search_result = comprehensive_search(
            topic="人工智能发展趋势",
            days=7,
            max_results=3
        )
        
        print(f"✅ 搜索完成，结果长度: {len(search_result)} 字符")
        print(f"搜索结果类型: {type(search_result)}")
        
        # 执行分析
        print("📊 执行质量分析...")
        analysis_result = analysis_mcp(
            analysis_type="quality",
            data=search_result,
            topic="人工智能发展趋势",
            evaluation_mode="initial"
        )
        
        print("✅ 完整工作流测试完成")
        result_data = json.loads(analysis_result)
        print(f"最终评分: {result_data.get('score', 'N/A')}/10")
        print(f"分析类型: {result_data.get('analysis_type', 'N/A')}")
        
        if result_data.get('score', 0) > 0:
            print("🎉 问题已修复！搜索结果现在可以正确评分了")
        else:
            print("⚠️ 评分仍为0，可能还有其他问题")
        
        return result_data
        
    except Exception as e:
        print(f"❌ 完整工作流测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主测试函数"""
    print("🧪 开始测试修复后的搜索-分析集成功能")
    print("=" * 60)
    
    # 测试1: 搜索结果解析
    test_search_result_parsing()
    
    # 测试2: 使用解析后数据进行分析
    test_analysis_with_parsed_data()
    
    # 测试3: 直接使用字符串数据进行分析
    test_analysis_with_string_data()
    
    # 测试4: 完整工作流
    test_full_search_analysis_workflow()
    
    print("\n" + "=" * 60)
    print("🏁 所有测试完成")

if __name__ == "__main__":
    main()