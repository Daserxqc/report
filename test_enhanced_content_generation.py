#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强后的内容生成功能
验证是否能达到预期的字数要求（3万字符）
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_tools import comprehensive_search, outline_writer_mcp
from generators.detailed_report_generator import DetailedReportGenerator
from streaming import StreamingProgressReporter
from search_manager import SearchEngineManager
from mcp_tools import MCPToolRegistry


def test_enhanced_content_generation():
    """测试增强后的内容生成功能"""
    print("\n" + "="*60)
    print("🧪 测试增强后的内容生成功能")
    print("="*60)
    
    # 初始化搜索引擎管理器
    print("\n🔧 初始化搜索引擎管理器...")
    try:
        search_manager = SearchEngineManager()
        registry = MCPToolRegistry(search_manager=search_manager)
        registry.initialize_components()
        print("   ✅ 搜索引擎管理器初始化完成")
    except Exception as e:
        print(f"   ❌ 搜索引擎管理器初始化失败: {e}")
        return {'success': False, 'error': f"搜索引擎管理器初始化失败: {e}"}
    
    topic = "人工智能在医疗诊断中的应用与发展趋势"
    session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        print(f"\n📝 测试主题: {topic}")
        print(f"🔍 会话ID: {session_id}")
        
        # 步骤1: 搜索相关信息
        print("\n🔍 步骤1: 搜索相关信息...")
        search_data = comprehensive_search(topic, max_results=15, session_id=session_id)

        # 从嵌套字典中提取并合并所有文章列表
        search_results_dict = search_data.get('search_results', {})
        all_articles = []
        if isinstance(search_results_dict, dict):
            for category, articles in search_results_dict.items():
                if isinstance(articles, list):
                    all_articles.extend(articles)
        
        if not all_articles:
            print(f"   ❌ 错误: 未能从搜索结果中提取任何文章.")
            return {'success': False, 'error': 'No articles found in search results.'}

        search_results = all_articles
        print(f"   ✅ 获得 {len(search_results)} 条搜索结果")
        
        # 记录搜索结果以供分析
        search_log_path = os.path.join(os.getcwd(), f"search_results_{session_id}.json")
        with open(search_log_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(search_results, f, ensure_ascii=False, indent=4)
        print(f"   📝 搜索结果已记录到: {search_log_path}")

        
        # 步骤2: 生成大纲
        print("\n📋 步骤2: 生成报告大纲...")
        outline_result = outline_writer_mcp(topic, search_results, session_id)
        outline = outline_result.get('outline', {})
        print(f"   ✅ 大纲生成完成")
        
        # 步骤3: 使用增强模式生成内容
        print("\n✍️ 步骤3: 生成详细内容 (使用 DetailedReportGenerator)...")
        report_generator = DetailedReportGenerator()
        content_result = report_generator.generate_detailed_report(
            topic=topic,
            articles=search_results,
            outline=outline
        )
        
        if content_result:
            content = content_result
            content_length = len(content.replace(' ', '').replace('\n', ''))
            
            print(f"\n📊 内容生成结果:")
            print(f"   📝 内容长度: {content_length:,} 字符")
            print(f"   📝 目标长度: 30,000 字符")
            print(f"   📝 达成率: {(content_length/30000)*100:.1f}%")
            
            # 保存生成的报告
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"增强内容测试报告_{timestamp}.md"
            filepath = os.path.join(os.getcwd(), filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"   💾 报告已保存: {filepath}")
            
            # 质量评估
            if content_length >= 30000:
                quality = "优秀 ✅"
            elif content_length >= 20000:
                quality = "良好 ⚠️"
            elif content_length >= 10000:
                quality = "一般 ⚠️"
            else:
                quality = "需改进 ❌"
            
            print(f"   🎯 内容质量: {quality}")
            
            return {
                'success': True,
                'content_length': content_length,
                'target_length': 30000,
                'achievement_rate': (content_length/30000)*100,
                'quality': quality,
                'filepath': filepath
            }
        else:
            print(f"   ❌ 内容生成失败: {content_result.get('error', '未知错误')}")
            return {'success': False, 'error': content_result.get('error', '未知错误')}
            
    except Exception as e:
        print(f"   ❌ 测试异常: {str(e)}")
        return {'success': False, 'error': str(e)}



if __name__ == "__main__":
    print("\n🚀 开始增强内容生成测试")
    
    # 测试1: 完整流程测试
    result1 = test_enhanced_content_generation()
    
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    
    if result1.get('success'):
        print(f"✅ 完整流程测试: 成功")
        print(f"   📝 内容长度: {result1.get('content_length', 0):,} 字符")
        print(f"   🎯 达成率: {result1.get('achievement_rate', 0):.1f}%")
    else:
        print(f"❌ 完整流程测试: 失败 - {result1.get('error', '未知错误')}")
    
    print("\n🎉 测试完成!")