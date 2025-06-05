#!/usr/bin/env python3
"""
测试实用市场收集器
"""

from practical_market_collector import PracticalMarketCollector

def main():
    print("=== 测试实用市场收集器 ===\n")
    
    collector = PracticalMarketCollector()
    
    # 测试AI市场数据
    print("📊 测试人工智能市场数据收集...")
    try:
        ai_data = collector.get_practical_market_data('artificial intelligence')
        
        print("✅ 数据收集成功!")
        print(f"行业: {ai_data['industry_baseline']['industry']}")
        print(f"市场规模 (2024): {ai_data['industry_baseline']['market_size_2024']}")
        print(f"市场规模 (2030): {ai_data['industry_baseline']['market_size_2030']}")
        print(f"复合年增长率: {ai_data['industry_baseline']['cagr']}")
        print(f"可信度等级: {ai_data['data_confidence']['level']} ({ai_data['data_confidence']['score']}/100)")
        
        # 显示财务数据摘要
        financial = ai_data['financial_indicators']
        if financial.get('companies_analyzed', 0) > 0:
            print(f"分析公司数量: {financial['companies_analyzed']}")
            if financial.get('total_market_cap_formatted'):
                print(f"总市值: {financial['total_market_cap_formatted']}")
        
        print("\n" + "="*50)
        
    except Exception as e:
        print(f"❌ AI数据收集失败: {str(e)}")
    
    # 测试报告生成
    print("\n📝 测试报告生成...")
    try:
        report_data = collector.generate_practical_report('artificial intelligence')
        
        # 保存报告
        filename = "ai_practical_test_report.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_data['report_content'])
        
        print(f"✅ 报告生成成功: {filename}")
        print(f"报告长度: {len(report_data['report_content'])} 字符")
        print(f"数据可信度: {report_data['generation_info']['confidence_score']}/100")
        
        # 显示报告摘要
        lines = report_data['report_content'].split('\n')
        print("\n报告摘要:")
        for line in lines[:10]:  # 显示前10行
            if line.strip():
                print(f"  {line}")
        
    except Exception as e:
        print(f"❌ 报告生成失败: {str(e)}")

if __name__ == "__main__":
    main() 