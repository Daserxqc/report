#!/usr/bin/env python3
"""
演示增强版市场收集器的功能
展示精确数据来源标注和智能图表生成
"""

from enhanced_market_collector import EnhancedMarketCollector
import os

def demo_enhanced_features():
    """演示增强版功能"""
    print("🚀 增强版市场收集器功能演示")
    print("="*60)
    
    collector = EnhancedMarketCollector()
    
    # 测试主题列表
    test_topics = [
        'artificial intelligence',
        'electric vehicle', 
        'cloud computing'
    ]
    
    for topic in test_topics:
        print(f"\n📊 正在处理: {topic.title()}")
        print("-" * 40)
        
        try:
            # 生成增强版报告
            report_data = collector.generate_enhanced_report(topic)
            
            # 保存报告
            filename = f"{topic.replace(' ', '_')}_enhanced_demo.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_data['report_content'])
            
            # 显示结果摘要
            confidence_info = report_data['raw_data']['data_confidence']
            print(f"✅ 报告生成成功: {filename}")
            print(f"📈 生成图表: {len(report_data['chart_paths'])} 个")
            print(f"🔍 数据可信度: {confidence_info['level']} ({confidence_info['score']}/100)")
            
            # 显示数据来源详情
            industry_data = report_data['raw_data']['industry_data']
            print(f"📋 市场规模来源: {industry_data['current_market_size']['source']}")
            print(f"📈 增长率来源: {industry_data['growth_rate']['source']}")
            
            # 列出生成的图表
            if report_data['chart_paths']:
                print("📊 生成的图表:")
                for chart_path in report_data['chart_paths']:
                    chart_name = os.path.basename(chart_path)
                    chart_type = "未知类型"
                    if "market_size" in chart_name:
                        chart_type = "市场规模趋势图"
                    elif "segments" in chart_name:
                        chart_type = "市场细分饼图"
                    elif "companies" in chart_name:
                        chart_type = "公司对比柱状图"
                    print(f"   • {chart_name} ({chart_type})")
            
        except Exception as e:
            print(f"❌ 处理 {topic} 时出错: {str(e)}")
    
    print(f"\n🎯 演示完成！")
    print(f"📁 所有图表已保存至: {collector.charts_dir}")
    print(f"📄 报告文件已生成")

def show_data_source_examples():
    """展示数据来源标注的详细示例"""
    print("\n" + "="*60)
    print("📋 数据来源标注示例")
    print("="*60)
    
    collector = EnhancedMarketCollector()
    
    # 获取AI数据作为示例
    market_data = collector.get_enhanced_market_data('artificial intelligence')
    industry_data = market_data['industry_data']
    
    print("\n🔍 详细数据来源标注示例:")
    print("-" * 30)
    
    # 当前市场规模
    current_size = industry_data['current_market_size']
    print(f"📊 当前市场规模 (2024)")
    print(f"   数值: {current_size['formatted']}")
    print(f"   来源: {current_size['source']}")
    print(f"   日期: {current_size['date']}")
    print(f"   可信度: {current_size['confidence']}")
    
    # 预测市场规模
    projected_size = industry_data['projected_market_size']
    print(f"\n📈 预测市场规模 (2030)")
    print(f"   数值: {projected_size['formatted']}")
    print(f"   来源: {projected_size['source']}")
    print(f"   日期: {projected_size['date']}")
    print(f"   可信度: {projected_size['confidence']}")
    
    # 增长率
    growth_rate = industry_data['growth_rate']
    print(f"\n📊 复合年增长率 (CAGR)")
    print(f"   数值: {growth_rate['formatted']}")
    print(f"   来源: {growth_rate['source']}")
    print(f"   日期: {growth_rate['date']}")
    print(f"   可信度: {growth_rate['confidence']}")
    
    # 历史数据
    print(f"\n📅 历史数据 (每个数据点都有来源):")
    for item in industry_data['historical_data']:
        print(f"   {item['year']}: ${item['size']}B (来源: {item['source']})")
    
    # 市场细分
    print(f"\n🥧 市场细分 (每个细分都有来源):")
    for segment, data in industry_data['market_segments'].items():
        print(f"   {segment}: {data['share']}% (来源: {data['source']})")

def show_chart_types():
    """展示不同类型的图表"""
    print("\n" + "="*60)
    print("📊 智能图表生成示例")
    print("="*60)
    
    print("\n🎨 根据数据类型自动选择图表类型:")
    print("-" * 40)
    
    chart_types = {
        "市场规模历史和预测": {
            "数据类型": "时间序列数据",
            "图表类型": "线图 + 散点图",
            "特点": ["历史数据用实线", "预测数据用虚线", "悬停显示来源"]
        },
        "市场细分分析": {
            "数据类型": "分类占比数据",
            "图表类型": "环形饼图",
            "特点": ["显示百分比", "悬停显示来源", "每个部分标注数据源"]
        },
        "公司对比分析": {
            "数据类型": "公司财务数据",
            "图表类型": "横向柱状图",
            "特点": ["按市值排序", "实时Yahoo Finance数据", "标注数据获取时间"]
        }
    }
    
    for chart_name, details in chart_types.items():
        print(f"\n📈 {chart_name}")
        print(f"   数据类型: {details['数据类型']}")
        print(f"   图表类型: {details['图表类型']}")
        print(f"   特点:")
        for feature in details['特点']:
            print(f"     • {feature}")

def main():
    """主演示函数"""
    print("🎯 增强版市场数据收集器演示")
    print("特点: 精确数据来源标注 + 智能图表生成")
    print("="*60)
    
    # 1. 演示增强版功能
    demo_enhanced_features()
    
    # 2. 展示数据来源标注详情
    show_data_source_examples()
    
    # 3. 展示图表类型说明
    show_chart_types()
    
    print("\n" + "="*60)
    print("🎉 演示完成！")
    print("\n📝 主要改进:")
    print("1. ✅ 每个数据点都标注具体来源、日期和可信度")
    print("2. ✅ 根据数据类型智能生成相应图表")
    print("3. ✅ 图表中嵌入数据来源信息")
    print("4. ✅ 支持历史数据、预测数据、市场细分、公司对比等多种图表")
    print("\n🔗 查看生成的HTML图表文件以获得完整的交互式体验！")

if __name__ == "__main__":
    main() 