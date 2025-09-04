#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强后的MCP工具报告生成质量
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from mcp_tools import content_writer_mcp
from collectors.detailed_content_writer_mcp import ContentWritingConfig

def test_enhanced_content_generation():
    """测试增强的内容生成功能"""
    print("=" * 60)
    print("测试增强后的MCP工具报告生成质量")
    print("=" * 60)
    
    # 测试主题
    test_topic = "水下特种机器人行业市场动态分析"
    
    # 模拟搜索结果数据
    mock_search_results = [
        {
            "title": "全球水下机器人市场规模预测",
            "content": "根据最新市场研究报告，全球水下机器人市场预计将从2023年的45亿美元增长到2030年的89亿美元，年复合增长率达到10.2%。海洋石油开采、海底电缆维护和科学研究是主要驱动因素。",
            "source": "MarketResearch.com",
            "url": "https://example.com/underwater-robot-market"
        },
        {
            "title": "水下机器人技术创新趋势",
            "content": "人工智能和机器学习技术的集成正在革命性地改变水下机器人的能力。新一代水下机器人配备了先进的计算机视觉系统，能够实现自主导航和目标识别，大大提高了作业效率和安全性。",
            "source": "TechInnovation Weekly",
            "url": "https://example.com/underwater-tech-trends"
        },
        {
            "title": "深海探索应用案例",
            "content": "挪威海洋研究所最近使用自主水下航行器(AUV)成功完成了北极海底地质勘探任务，收集了超过500GB的海底地形和生物多样性数据，为气候变化研究提供了重要支撑。",
            "source": "Ocean Research Journal",
            "url": "https://example.com/deep-sea-exploration"
        }
    ]
    
    print(f"\n🎯 测试主题: {test_topic}")
    print(f"📊 模拟数据源: {len(mock_search_results)}个")
    
    # 测试增强模式
    print("\n" + "="*50)
    print("🚀 测试增强模式 (Enhanced Mode)")
    print("="*50)
    
    enhanced_result = content_writer_mcp(
        topic=test_topic,
        search_results=mock_search_results,
        content_style="enhanced",
        min_word_count=2500
    )
    
    if "error" in enhanced_result:
        print(f"❌ 增强模式测试失败: {enhanced_result['error']}")
    else:
        print(f"✅ 增强模式测试成功")
        print(f"📝 内容长度: {enhanced_result.get('content_length', 0)} 字符")
        print(f"⭐ 质量评分: {enhanced_result.get('quality_score', 'N/A')}")
        print(f"📚 数据源数量: {enhanced_result.get('data_sources_count', 0)}")
        
        # 显示内容预览
        content = enhanced_result.get('content', '')
        preview = content[:500] + "..." if len(content) > 500 else content
        print(f"\n📖 内容预览:\n{preview}")
    
    # 测试原始模式对比
    print("\n" + "="*50)
    print("🔄 测试原始模式 (Original Mode)")
    print("="*50)
    
    original_result = content_writer_mcp(
        topic=test_topic,
        search_results=mock_search_results,
        content_style="original",
        min_word_count=1000
    )
    
    if "error" in original_result:
        print(f"❌ 原始模式测试失败: {original_result['error']}")
    else:
        print(f"✅ 原始模式测试成功")
        print(f"📝 内容长度: {original_result.get('content_length', 0)} 字符")
        print(f"⭐ 质量评分: {original_result.get('quality_score', 'N/A')}")
        print(f"📚 数据源数量: {original_result.get('data_sources_count', 0)}")
    
    # 对比分析
    print("\n" + "="*50)
    print("📊 模式对比分析")
    print("="*50)
    
    if "error" not in enhanced_result and "error" not in original_result:
        enhanced_length = enhanced_result.get('content_length', 0)
        original_length = original_result.get('content_length', 0)
        
        print(f"📏 长度对比:")
        print(f"   增强模式: {enhanced_length} 字符")
        print(f"   原始模式: {original_length} 字符")
        print(f"   增长比例: {((enhanced_length - original_length) / original_length * 100):.1f}%" if original_length > 0 else "N/A")
        
        print(f"\n🎯 质量对比:")
        print(f"   增强模式: {enhanced_result.get('quality_score', 'N/A')}")
        print(f"   原始模式: {original_result.get('quality_score', 'N/A')}")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)

if __name__ == "__main__":
    test_enhanced_content_generation()