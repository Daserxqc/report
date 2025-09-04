#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Tavily搜索功能的运行时错误
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('e:/report_generation')
sys.path.append('e:/report_generation/search_mcp/src')

from collectors.tavily_collector import TavilyCollector
from search_mcp import SearchGenerator, SearchConfig
from search_mcp.models import Document

def test_tavily_search():
    """测试Tavily搜索功能"""
    print("🔍 开始测试Tavily搜索功能...")
    
    try:
        # 初始化Tavily收集器
        tavily = TavilyCollector()
        print("✅ TavilyCollector初始化成功")
        
        # 测试搜索
        query = "人工智能在医疗领域的应用"
        print(f"🔍 搜索查询: {query}")
        
        results = tavily.search(query, max_results=3)
        print(f"📊 搜索结果数量: {len(results)}")
        
        # 检查结果类型
        if results:
            first_result = results[0]
            print(f"📋 第一个结果类型: {type(first_result)}")
            
            if isinstance(first_result, Document):
                print(f"✅ 结果是Document类型")
                print(f"📄 标题: {first_result.title[:50]}...")
                print(f"📝 内容长度: {len(first_result.content)}")
                print(f"🔗 URL: {first_result.url}")
            else:
                print(f"❌ 结果不是Document类型: {type(first_result)}")
                print(f"📋 结果内容: {first_result}")
        
        print("✅ Tavily搜索测试通过")
        return True
        
    except Exception as e:
        print(f"❌ Tavily搜索测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_tavily_parallel_search():
    """测试Tavily并行搜索功能"""
    print("\n🔍 开始测试Tavily并行搜索功能...")
    
    try:
        # 初始化搜索配置和生成器
        config = SearchConfig()
        search_generator = SearchGenerator(config)
        print("✅ SearchGenerator初始化成功")
        
        # 测试并行搜索
        queries = [
            "人工智能医疗应用",
            "AI医疗诊断技术",
            "智能医疗设备发展"
        ]
        print(f"🔍 并行搜索查询: {queries}")
        
        results = search_generator.parallel_search(
            queries=queries,
            sources=["tavily"],
            max_results_per_query=2
        )
        
        print(f"📊 并行搜索结果数量: {len(results)}")
        
        # 检查结果
        if results:
            for i, result in enumerate(results[:3]):
                print(f"📋 结果{i+1}类型: {type(result)}")
                if isinstance(result, Document):
                    print(f"   标题: {result.title[:30]}...")
                    print(f"   来源: {result.source_type}")
        
        print("✅ Tavily并行搜索测试通过")
        return True
        
    except Exception as e:
        print(f"❌ Tavily并行搜索测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Tavily搜索功能测试")
    print("=" * 60)
    
    # 测试基本搜索
    test1_passed = test_tavily_search()
    
    # 测试并行搜索
    test2_passed = test_tavily_parallel_search()
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"   ✅ Tavily基本搜索: {'通过' if test1_passed else '失败'}")
    print(f"   ✅ Tavily并行搜索: {'通过' if test2_passed else '失败'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 所有Tavily搜索测试通过！")
    else:
        print("\n❌ 部分Tavily搜索测试失败！")
    print("=" * 60)