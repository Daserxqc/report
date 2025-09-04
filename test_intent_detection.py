#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试意图识别功能
验证task_detector模块是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from streaming import TaskTypeDetector

def test_task_type_detection():
    """测试任务类型检测"""
    print("\n🧠 测试意图识别功能")
    print("=" * 50)
    
    try:
        # 初始化任务类型检测器
        detector = TaskTypeDetector()
        print("✅ TaskTypeDetector初始化成功")
        
        # 测试用例
        test_cases = [
            "写一份人工智能市场分析报告",
            "搜索最新的AI新闻",
            "分析OpenAI的发展趋势",
            "总结量子计算的研究进展",
            "帮我查找机器学习相关论文",
            "生成一个关于区块链的洞察报告"
        ]
        
        print("\n🔍 测试任务类型检测:")
        for i, test_case in enumerate(test_cases, 1):
            try:
                task_type = detector.detect_task_type(test_case)
                print(f"  {i}. '{test_case}' -> {task_type}")
            except Exception as e:
                print(f"  {i}. '{test_case}' -> ❌ 错误: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ TaskTypeDetector初始化失败: {e}")
        return False

def test_mcp_tools_integration():
    """测试mcp_tools中的意图识别集成"""
    print("\n🔧 测试mcp_tools集成")
    print("=" * 50)
    
    try:
        from mcp_tools import task_detector
        print("✅ 从mcp_tools导入task_detector成功")
        
        # 测试检测功能
        test_query = "分析人工智能在医疗领域的应用趋势"
        task_type = task_detector.detect_task_type(test_query)
        print(f"✅ 意图检测成功: '{test_query}' -> {task_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ mcp_tools集成测试失败: {e}")
        return False

def test_streaming_integration():
    """测试streaming模块中的意图识别"""
    print("\n📡 测试streaming模块集成")
    print("=" * 50)
    
    try:
        from streaming import task_detector
        print("✅ 从streaming导入task_detector成功")
        
        # 测试检测功能
        test_query = "写一份关于新能源汽车的市场研究报告"
        task_type = task_detector.detect_task_type(test_query)
        print(f"✅ 意图检测成功: '{test_query}' -> {task_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ streaming集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始意图识别测试")
    
    results = {
        "基本功能测试": test_task_type_detection(),
        "mcp_tools集成测试": test_mcp_tools_integration(),
        "streaming集成测试": test_streaming_integration()
    }
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {status} {test_name}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 所有意图识别测试通过！")
    else:
        print("\n⚠️ 部分测试失败，需要修复")
    
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    main()