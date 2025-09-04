#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试大纲创建功能
验证OutlineWriterMcp模块是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.outline_writer_mcp import OutlineWriterMcp, OutlineNode

def test_outline_writer_initialization():
    """测试OutlineWriterMcp初始化"""
    print("\n🏗️ 测试OutlineWriterMcp初始化")
    print("=" * 50)
    
    try:
        outline_writer = OutlineWriterMcp()
        print("✅ OutlineWriterMcp初始化成功")
        return True, outline_writer
        
    except Exception as e:
        print(f"❌ OutlineWriterMcp初始化失败: {e}")
        return False, None

def test_outline_creation(outline_writer):
    """测试大纲创建功能"""
    print("\n📋 测试大纲创建功能")
    print("=" * 50)
    
    if not outline_writer:
        print("❌ OutlineWriterMcp未初始化，跳过测试")
        return False
    
    try:
        # 测试用例
        test_cases = [
            {
                "topic": "人工智能在医疗领域的应用",
                "report_type": "technical_report",
                "user_requirements": "重点关注AI诊断技术"
            },
            {
                "topic": "新能源汽车市场分析",
                "report_type": "business_report",
                "user_requirements": "包含竞争格局分析"
            },
            {
                "topic": "区块链技术发展趋势",
                "report_type": "comprehensive",
                "user_requirements": "涵盖技术和商业应用"
            }
        ]
        
        print("\n🔍 测试大纲创建:")
        for i, test_case in enumerate(test_cases, 1):
            try:
                print(f"\n  测试 {i}: {test_case['topic']}")
                print(f"    报告类型: {test_case['report_type']}")
                
                outline = outline_writer.create_outline(
                    topic=test_case['topic'],
                    report_type=test_case['report_type'],
                    user_requirements=test_case['user_requirements']
                )
                
                if isinstance(outline, OutlineNode):
                    print(f"    ✅ 大纲创建成功")
                    print(f"    📊 主章节数量: {len(outline.subsections)}")
                    print(f"    📝 大纲标题: {outline.title}")
                    
                    # 显示前几个章节
                    for j, section in enumerate(outline.subsections[:3]):
                        print(f"      {j+1}. {section.title}")
                    
                    if len(outline.subsections) > 3:
                        print(f"      ... 还有 {len(outline.subsections) - 3} 个章节")
                else:
                    print(f"    ❌ 返回类型错误: {type(outline)}")
                    return False
                    
            except Exception as e:
                print(f"    ❌ 大纲创建失败: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 大纲创建测试失败: {e}")
        return False

def test_fallback_outline_creation(outline_writer):
    """测试备用大纲创建功能"""
    print("\n🔄 测试备用大纲创建功能")
    print("=" * 50)
    
    if not outline_writer:
        print("❌ OutlineWriterMcp未初始化，跳过测试")
        return False
    
    try:
        # 临时禁用LLM以测试备用功能
        original_has_llm = outline_writer.has_llm
        outline_writer.has_llm = False
        
        print("🔍 测试备用大纲创建（无LLM模式）:")
        outline = outline_writer.create_outline(
            topic="测试主题",
            report_type="comprehensive",
            user_requirements="测试要求"
        )
        
        if isinstance(outline, OutlineNode):
            print("✅ 备用大纲创建成功")
            print(f"📊 主章节数量: {len(outline.subsections)}")
            print(f"📝 大纲标题: {outline.title}")
            
            # 恢复原始设置
            outline_writer.has_llm = original_has_llm
            return True
        else:
            print(f"❌ 备用大纲创建失败: {type(outline)}")
            outline_writer.has_llm = original_has_llm
            return False
            
    except Exception as e:
        print(f"❌ 备用大纲创建测试失败: {e}")
        # 恢复原始设置
        if 'original_has_llm' in locals():
            outline_writer.has_llm = original_has_llm
        return False

def test_mcp_tools_integration():
    """测试mcp_tools中的大纲创建集成"""
    print("\n🔧 测试mcp_tools集成")
    print("=" * 50)
    
    try:
        # 先初始化搜索管理器
        from search_manager import SearchEngineManager
        from mcp_tools import get_tool_registry
        
        search_manager = SearchEngineManager()
        tool_registry = get_tool_registry(search_manager)
        
        from mcp_tools import outline_writer_mcp
        print("✅ 从mcp_tools导入outline_writer_mcp成功")
        
        # 测试大纲创建功能
        print("🔍 测试大纲创建集成:")
        result = outline_writer_mcp(
            topic="人工智能技术发展趋势",
            search_results=[]  # 提供空的搜索结果以避免额外搜索
        )
        
        if 'outline' in result and not result.get('error'):
            print("✅ mcp_tools大纲创建集成测试成功")
            print(f"📊 返回结果包含: {list(result.keys())}")
            return True
        else:
            print(f"❌ mcp_tools大纲创建集成测试失败: {result.get('error', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ mcp_tools集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始大纲创建测试")
    
    # 初始化测试
    init_success, outline_writer = test_outline_writer_initialization()
    
    results = {
        "初始化测试": init_success,
        "大纲创建测试": test_outline_creation(outline_writer) if init_success else False,
        "备用功能测试": test_fallback_outline_creation(outline_writer) if init_success else False,
        "mcp_tools集成测试": test_mcp_tools_integration()
    }
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {status} {test_name}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 所有大纲创建测试通过！")
    else:
        print("\n⚠️ 部分测试失败，需要修复")
    
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    main()