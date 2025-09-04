#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索MCP功能综合测试脚本

测试搜索MCP的各项核心功能：
1. 并行搜索功能
2. 分类搜索功能
3. 回退机制
4. 配置管理
5. 数据收集器状态
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 添加search_mcp路径
search_mcp_path = project_root / "search_mcp" / "src"
if str(search_mcp_path) not in sys.path:
    sys.path.insert(0, str(search_mcp_path))

print("=" * 80)
print("🔍 搜索MCP功能综合测试")
print("=" * 80)

def test_search_config():
    """测试搜索配置功能"""
    print("\n📋 测试1: 搜索配置管理")
    print("-" * 50)
    
    try:
        from search_mcp.config import SearchConfig
        
        # 创建配置实例
        config = SearchConfig()
        print(f"✅ 配置创建成功")
        
        # 检查API密钥状态
        api_keys = config.get_api_keys()
        print(f"📊 API密钥状态:")
        for source, key in api_keys.items():
            status = "✅ 已配置" if key else "❌ 未配置"
            print(f"   {source}: {status}")
        
        # 检查启用的数据源
        enabled_sources = config.get_enabled_sources()
        print(f"🔧 启用的数据源: {enabled_sources}")
        
        # 检查配置参数
        print(f"⚙️ 配置参数:")
        print(f"   最大结果数: {config.max_results_per_query}")
        print(f"   最大工作线程: {config.max_workers}")
        print(f"   请求超时: {config.request_timeout}s")
        print(f"   缓存启用: {config.enable_cache}")
        
        return config
        
    except Exception as e:
        print(f"❌ 配置测试失败: {str(e)}")
        return None

def test_search_orchestrator(config):
    """测试搜索编排器"""
    print("\n🎭 测试2: 搜索编排器初始化")
    print("-" * 50)
    
    try:
        from search_mcp.generators import SearchOrchestrator
        
        # 创建编排器实例
        orchestrator = SearchOrchestrator(config)
        print(f"✅ 搜索编排器创建成功")
        
        # 获取可用数据源
        available_sources = orchestrator.get_available_sources()
        print(f"📊 可用数据源分类:")
        for category, sources in available_sources.items():
            print(f"   {category}: {sources}")
        
        # 获取收集器信息
        collector_info = orchestrator.get_collector_info()
        print(f"🔧 收集器状态:")
        for info in collector_info:
            status = "✅ 可用" if info.is_available else "❌ 不可用"
            print(f"   {info.name} ({info.source_type}): {status}")
            print(f"      API密钥需要: {info.api_key_required}")
            print(f"      API密钥状态: {'✅ 已配置' if info.has_api_key else '❌ 未配置'}")
            if info.description:
                print(f"      描述: {info.description}")
        
        return orchestrator
        
    except Exception as e:
        print(f"❌ 编排器测试失败: {str(e)}")
        return None

def test_parallel_search(orchestrator):
    """测试并行搜索功能"""
    print("\n🚀 测试3: 并行搜索功能")
    print("-" * 50)
    
    try:
        # 定义测试查询
        test_queries = [
            "人工智能最新发展",
            "机器学习技术趋势"
        ]
        
        print(f"🔍 执行并行搜索...")
        print(f"   查询: {test_queries}")
        
        start_time = datetime.now()
        
        # 执行并行搜索
        results = orchestrator.parallel_search(
            queries=test_queries,
            max_results_per_query=3,
            days_back=7,
            max_workers=4
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print(f"✅ 并行搜索完成")
        print(f"📊 搜索结果统计:")
        print(f"   总结果数: {len(results)}")
        print(f"   执行时间: {execution_time:.2f}秒")
        
        # 按数据源分类统计
        source_stats = {}
        for result in results:
            source = result.source
            if source not in source_stats:
                source_stats[source] = 0
            source_stats[source] += 1
        
        print(f"   数据源分布:")
        for source, count in source_stats.items():
            print(f"     {source}: {count}条")
        
        # 显示前几条结果
        print(f"\n📄 前3条搜索结果:")
        for i, result in enumerate(results[:3]):
            print(f"   {i+1}. [{result.source}] {result.title}")
            print(f"      URL: {result.url}")
            print(f"      摘要: {result.content[:100]}...")
            print()
        
        return results
        
    except Exception as e:
        print(f"❌ 并行搜索测试失败: {str(e)}")
        return []

def test_category_search(orchestrator):
    """测试分类搜索功能"""
    print("\n📚 测试4: 分类搜索功能")
    print("-" * 50)
    
    try:
        test_queries = ["深度学习研究进展"]
        categories = ['web', 'academic', 'news']
        
        for category in categories:
            print(f"\n🔍 测试{category}类别搜索...")
            
            try:
                results = orchestrator.search_by_category(
                    queries=test_queries,
                    category=category,
                    max_results_per_query=2,
                    days_back=30
                )
                
                print(f"✅ {category}搜索完成，获得{len(results)}条结果")
                
                if results:
                    print(f"   示例结果: [{results[0].source}] {results[0].title}")
                
            except Exception as e:
                print(f"⚠️ {category}搜索失败: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 分类搜索测试失败: {str(e)}")
        return False

def test_fallback_mechanism(orchestrator):
    """测试回退机制"""
    print("\n🔄 测试5: 搜索回退机制")
    print("-" * 50)
    
    try:
        test_queries = ["量子计算发展"]
        
        # 测试首选和回退数据源
        preferred_sources = ['nonexistent_source']  # 不存在的数据源
        fallback_sources = ['tavily', 'brave']  # 回退数据源
        
        print(f"🔍 测试回退搜索...")
        print(f"   首选数据源: {preferred_sources}")
        print(f"   回退数据源: {fallback_sources}")
        
        results = orchestrator.search_with_fallback(
            queries=test_queries,
            preferred_sources=preferred_sources,
            fallback_sources=fallback_sources,
            max_results_per_query=2
        )
        
        print(f"✅ 回退搜索完成，获得{len(results)}条结果")
        
        if results:
            print(f"📊 实际使用的数据源:")
            used_sources = set(result.source for result in results)
            for source in used_sources:
                print(f"   - {source}")
        
        return True
        
    except Exception as e:
        print(f"❌ 回退机制测试失败: {str(e)}")
        return False

def test_main_mcp_integration():
    """测试main.py中的MCP集成"""
    print("\n🔗 测试6: main.py MCP集成")
    print("-" * 50)
    
    try:
        # 测试comprehensive_search函数
        from main import comprehensive_search, parallel_search
        
        print("🔍 测试comprehensive_search函数...")
        result1 = comprehensive_search(
            topic="人工智能发展趋势",
            days=7,
            max_results=3
        )
        
        print(f"✅ comprehensive_search执行成功")
        print(f"   结果长度: {len(result1)}字符")
        
        print("\n🔍 测试parallel_search函数...")
        result2 = parallel_search(
            queries=["机器学习", "深度学习"],
            max_results=2,
            topic="AI技术"
        )
        
        print(f"✅ parallel_search执行成功")
        print(f"   结果长度: {len(result2)}字符")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP集成测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print(f"🕒 测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试结果统计
    test_results = {
        'config': False,
        'orchestrator': False,
        'parallel_search': False,
        'category_search': False,
        'fallback': False,
        'mcp_integration': False
    }
    
    # 1. 测试配置
    config = test_search_config()
    test_results['config'] = config is not None
    
    if config:
        # 2. 测试编排器
        orchestrator = test_search_orchestrator(config)
        test_results['orchestrator'] = orchestrator is not None
        
        if orchestrator:
            # 3. 测试并行搜索
            results = test_parallel_search(orchestrator)
            test_results['parallel_search'] = len(results) > 0
            
            # 4. 测试分类搜索
            test_results['category_search'] = test_category_search(orchestrator)
            
            # 5. 测试回退机制
            test_results['fallback'] = test_fallback_mechanism(orchestrator)
    
    # 6. 测试MCP集成
    test_results['mcp_integration'] = test_main_mcp_integration()
    
    # 输出测试总结
    print("\n" + "=" * 80)
    print("📊 测试结果总结")
    print("=" * 80)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed_tests}/{total_tests} 项测试通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！搜索MCP功能正常")
    else:
        print("⚠️ 部分测试失败，请检查相关配置和依赖")
    
    print(f"🕒 测试结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()