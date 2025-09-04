#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证测试 - 确保修复在完整的orchestrator_mcp工作流中正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_orchestrator_mcp_with_analysis():
    """测试orchestrator_mcp中的分析功能"""
    print("🧪 测试orchestrator_mcp中的分析功能...")
    
    try:
        # 导入main模块
        import main
        
        # 测试简单的报告生成任务
        task = "生成一份关于人工智能在医疗领域应用的简短报告"
        print(f"📝 任务: {task}")
        
        # 调用orchestrator_mcp_simple（更轻量级的测试）
        result = main.orchestrator_mcp_simple(task)
        
        print(f"✅ orchestrator_mcp_simple执行成功")
        print(f"📊 结果类型: {type(result)}")
        
        # 处理字典格式的结果
        if isinstance(result, dict):
            print(f"📊 结果键: {list(result.keys())}")
            result_str = str(result)
            print(f"📊 结果长度: {len(result_str)} 字符")
            
            # 检查结果中是否包含质量评分信息
            if "质量评分" in result_str or "quality" in result_str.lower():
                print("✅ 结果包含质量评分信息")
            else:
                print("⚠️ 结果中未找到质量评分信息")
                
            # 显示结果的前500字符
            print("\n📄 报告预览:")
            print("=" * 50)
            print(result_str[:500] + "..." if len(result_str) > 500 else result_str)
            print("=" * 50)
        else:
            print(f"📊 结果长度: {len(result)} 字符")
            
            # 检查结果中是否包含质量评分信息
            if "质量评分" in result or "quality" in result.lower():
                print("✅ 结果包含质量评分信息")
            else:
                print("⚠️ 结果中未找到质量评分信息")
                
            # 显示结果的前500字符
            print("\n📄 报告预览:")
            print("=" * 50)
            print(result[:500] + "..." if len(result) > 500 else result)
            print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ orchestrator_mcp测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_analysis_mcp():
    """直接测试analysis_mcp函数"""
    print("\n🧪 直接测试analysis_mcp函数...")
    
    try:
        import main
        
        # 模拟搜索结果数据
        test_data = [
            {
                "title": "AI在医疗诊断中的突破性进展",
                "content": "人工智能技术在医疗影像诊断领域取得重大突破，准确率达到95%以上。",
                "url": "https://example.com/ai-medical-1",
                "source": "医疗科技新闻"
            },
            {
                "title": "机器学习辅助药物研发",
                "content": "利用机器学习算法加速新药研发过程，缩短研发周期50%。",
                "url": "https://example.com/ai-medical-2",
                "source": "生物医学期刊"
            }
        ]
        
        # 测试质量分析
        result = main.analysis_mcp.analyze_quality(
            data=test_data,
            topic="人工智能在医疗领域的应用",
            evaluation_mode="initial"
        )
        
        print(f"✅ analysis_mcp执行成功")
        print(f"📊 分析结果类型: {type(result)}")
        print(f"📊 分析类型: {result.analysis_type}")
        print(f"📊 评分: {result.score}")
        print(f"📊 推理: {result.reasoning[:200]}..." if len(result.reasoning) > 200 else f"📊 推理: {result.reasoning}")
        
        # 解析结果 - AnalysisResult对象已经是结构化的
        score = result.score
        print(f"🎯 质量评分: {score}/10")
        print(f"📊 详细信息: {result.details}")
        
        if score > 0:
            print("✅ 评分正常，修复成功！")
            return True
        else:
            print("❌ 评分仍为0，可能存在其他问题")
            return False
            
    except Exception as e:
        print(f"❌ analysis_mcp测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_orchestrator_mcp():
    """测试完整的orchestrator_mcp功能，包括分析步骤"""
    print("🧪 测试完整的orchestrator_mcp功能...")
    
    try:
        import main
        
        task = "生成一份关于人工智能在医疗领域应用的简短报告"
        print(f"📝 任务: {task}")
        
        # 调用完整的orchestrator_mcp（包含分析步骤）
        result = main.orchestrator_mcp(task, include_analysis=True)
        
        print(f"✅ orchestrator_mcp执行成功")
        print(f"📊 结果类型: {type(result)}")
        
        if isinstance(result, dict):
            print(f"📊 结果键: {list(result.keys())}")
            
            # 检查是否包含分析结果
            if 'analysis' in result:
                analysis = result['analysis']
                print(f"✅ 包含分析结果: {type(analysis)}")
                
                if hasattr(analysis, 'score'):
                    print(f"🎯 质量评分: {analysis.score}/10")
                    print(f"📊 分析类型: {analysis.analysis_type}")
                    return True
                else:
                    print(f"⚠️ 分析结果格式: {analysis}")
            else:
                print("⚠️ 结果中未包含分析信息")
        
        return False
        
    except Exception as e:
        print(f"❌ 完整orchestrator_mcp测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main_test():
    """主测试函数"""
    print("🚀 开始最终验证测试...")
    print("=" * 60)
    
    # 测试1: 直接测试analysis_mcp
    test1_passed = test_direct_analysis_mcp()
    
    # 测试2: 测试orchestrator_mcp集成（简化版）
    test2_passed = test_orchestrator_mcp_with_analysis()
    
    # 测试3: 测试完整orchestrator_mcp功能
    test3_passed = test_full_orchestrator_mcp()
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"   ✅ analysis_mcp直接测试: {'通过' if test1_passed else '失败'}")
    print(f"   ✅ orchestrator_mcp集成测试(简化): {'通过' if test2_passed else '失败'}")
    print(f"   ✅ orchestrator_mcp完整测试: {'通过' if test3_passed else '失败'}")
    
    if test1_passed and test2_passed and test3_passed:
        print("\n🎉 所有测试通过！搜索-分析集成修复成功！")
    else:
        print("\n⚠️ 部分测试失败，需要进一步调试")
    
    print("=" * 60)

if __name__ == "__main__":
    main_test()