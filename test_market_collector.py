#!/usr/bin/env python3
"""
测试市场研究数据收集器
演示如何使用新的MarketResearchCollector获取市场数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.market_research_collector import MarketResearchCollector
import json

def test_market_collector():
    """测试市场研究收集器"""
    
    print("=== 测试市场研究数据收集器 ===\n")
    
    # 初始化收集器
    collector = MarketResearchCollector()
    
    # 测试主题
    test_topics = [
        "artificial intelligence",
        "electric vehicle", 
        "cloud computing",
        "fintech"
    ]
    
    for topic in test_topics:
        print(f"\n--- 测试主题: {topic} ---")
        
        try:
            # 获取市场数据
            market_data = collector.get_market_data(
                topic=topic,
                data_types=['market_size', 'growth_rate', 'forecast'],
                regions=['global', 'north_america']
            )
            
            # 显示结果摘要
            print(f"✅ 成功收集 {topic} 市场数据")
            print(f"📊 数据源数量: {len(market_data.get('detailed_reports', []))}")
            
            # 显示数据摘要
            data_summary = market_data.get('data_summary', {})
            if data_summary.get('market_size_estimates'):
                print(f"💰 市场规模估计: {len(data_summary['market_size_estimates'])} 个")
                for est in data_summary['market_size_estimates'][:2]:
                    print(f"   - {est['value']} (来源: {est['source']})")
            
            if data_summary.get('growth_rate_estimates'):
                print(f"📈 增长率估计: {len(data_summary['growth_rate_estimates'])} 个")
                for est in data_summary['growth_rate_estimates'][:2]:
                    print(f"   - {est['rate']} (来源: {est['source']})")
            
            # 显示数据质量注释
            if data_summary.get('data_quality_notes'):
                print(f"⚠️ 数据质量注释: {len(data_summary['data_quality_notes'])} 条")
            
            # 显示数据冲突
            if data_summary.get('data_conflicts'):
                print(f"🔍 数据冲突: {len(data_summary['data_conflicts'])} 条")
                for conflict in data_summary['data_conflicts']:
                    print(f"   - {conflict}")
            
        except Exception as e:
            print(f"❌ 收集 {topic} 数据时出错: {str(e)}")
        
        print("-" * 50)

def test_specific_sources():
    """测试特定数据源"""
    
    print("\n=== 测试特定数据源 ===\n")
    
    collector = MarketResearchCollector()
    topic = "artificial intelligence"
    
    # 测试各个数据源
    sources_to_test = [
        ('statista', collector._scrape_statista_summary),
        ('grandview', collector._scrape_grandview_summary),
        ('precedence', collector._scrape_precedence_summary),
        ('marketsandmarkets', collector._scrape_marketsandmarkets_summary),
        ('fortune', collector._scrape_fortune_summary)
    ]
    
    for source_name, source_func in sources_to_test:
        print(f"--- 测试 {source_name} ---")
        try:
            data = source_func(topic, ['market_size', 'growth_rate'])
            if data:
                print(f"✅ {source_name} 数据获取成功")
                print(f"   标题: {data.get('title', 'N/A')}")
                print(f"   访问级别: {data.get('access_level', 'N/A')}")
                if 'statistics' in data:
                    print(f"   统计数据: {len(data['statistics'])} 条")
                if 'market_size' in data:
                    print(f"   市场规模: {data['market_size']}")
                if 'growth_rate' in data:
                    print(f"   增长率: {data['growth_rate']}")
            else:
                print(f"⚠️ {source_name} 未返回数据")
        except Exception as e:
            print(f"❌ {source_name} 测试失败: {str(e)}")
        print()

def test_company_data():
    """测试公司财务数据获取"""
    
    print("\n=== 测试公司财务数据获取 ===\n")
    
    collector = MarketResearchCollector()
    
    # 测试AI相关公司
    companies = ['NVDA', 'GOOGL', 'MSFT']
    topic = "artificial intelligence"
    
    for company in companies:
        print(f"--- 测试公司: {company} ---")
        try:
            data = collector._get_company_financial_highlights(company, topic)
            if data:
                print(f"✅ {company} 财务数据获取成功")
                print(f"   市值: {data.get('market_cap', 'N/A')}")
                print(f"   营收: {data.get('revenue', 'N/A')}")
                print(f"   来源: {data.get('source', 'N/A')}")
            else:
                print(f"⚠️ {company} 未返回财务数据")
        except Exception as e:
            print(f"❌ {company} 财务数据获取失败: {str(e)}")
        print()

def test_comprehensive_report():
    """测试综合报告生成"""
    
    print("\n=== 测试综合报告生成 ===\n")
    
    collector = MarketResearchCollector()
    topic = "artificial intelligence"
    
    try:
        print(f"正在生成 {topic} 综合市场报告...")
        report = collector.get_comprehensive_market_report(topic, include_forecasts=True)
        
        print("✅ 综合报告生成成功")
        print(f"📅 生成日期: {report['generation_date']}")
        print(f"📝 执行摘要长度: {len(report['executive_summary'])} 字符")
        print(f"📊 市场概览长度: {len(report['market_overview'])} 字符")
        print(f"🏢 竞争格局长度: {len(report['competitive_landscape'])} 字符")
        print(f"📈 数据源数量: {len(report['data_sources'])}")
        
        # 显示数据源
        print("\n数据源列表:")
        for i, source in enumerate(report['data_sources'][:5], 1):
            print(f"  {i}. {source['name']} ({source['access_level']})")
        
        # 显示方法论注释
        print("\n方法论注释:")
        for note in report['methodology_notes']:
            print(f"  - {note}")
        
    except Exception as e:
        print(f"❌ 综合报告生成失败: {str(e)}")

def main():
    """主函数"""
    
    print("开始测试市场研究数据收集器...\n")
    
    # 运行各项测试
    test_market_collector()
    test_specific_sources()
    test_company_data()
    test_comprehensive_report()
    
    print("\n=== 测试完成 ===")
    print("注意：由于网络限制和反爬虫机制，部分数据源可能无法正常访问。")
    print("这是正常现象，实际使用时建议配置代理或使用API密钥。")

if __name__ == "__main__":
    main() 