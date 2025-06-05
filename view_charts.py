#!/usr/bin/env python3
"""
图表查看器
帮助用户在浏览器中查看生成的HTML图表
"""

import os
import webbrowser
from pathlib import Path

def list_available_charts():
    """列出所有可用的图表"""
    charts_dir = "market_charts"
    
    if not os.path.exists(charts_dir):
        print("❌ 图表目录不存在，请先运行 enhanced_market_collector.py")
        return []
    
    chart_files = []
    for file in os.listdir(charts_dir):
        if file.endswith('.html'):
            chart_files.append(file)
    
    return chart_files

def open_chart_in_browser(chart_name):
    """在浏览器中打开图表"""
    charts_dir = "market_charts"
    chart_path = os.path.join(charts_dir, chart_name)
    
    if os.path.exists(chart_path):
        # 获取绝对路径
        abs_path = os.path.abspath(chart_path)
        file_url = f"file:///{abs_path}"
        
        print(f"🌐 正在浏览器中打开: {chart_name}")
        webbrowser.open(file_url)
        return True
    else:
        print(f"❌ 图表文件不存在: {chart_name}")
        return False

def show_chart_info(chart_name):
    """显示图表信息"""
    chart_info = {
        "market_size": {
            "类型": "市场规模趋势图",
            "描述": "显示历史数据和预测趋势",
            "特点": ["历史数据用实线", "预测数据用虚线", "每个数据点标注来源"]
        },
        "segments": {
            "类型": "市场细分饼图", 
            "描述": "展示不同细分市场的占比",
            "特点": ["环形饼图设计", "悬停显示详细信息", "每个部分标注数据来源"]
        },
        "companies": {
            "类型": "公司对比柱状图",
            "描述": "对比相关上市公司的市值",
            "特点": ["横向柱状图", "按市值排序", "实时财务数据"]
        }
    }
    
    # 确定图表类型
    chart_type = "unknown"
    if "market_size" in chart_name:
        chart_type = "market_size"
    elif "segments" in chart_name:
        chart_type = "segments"
    elif "companies" in chart_name:
        chart_type = "companies"
    
    if chart_type in chart_info:
        info = chart_info[chart_type]
        print(f"\n📊 图表信息:")
        print(f"   类型: {info['类型']}")
        print(f"   描述: {info['描述']}")
        print(f"   特点:")
        for feature in info['特点']:
            print(f"     • {feature}")

def main():
    """主函数"""
    print("📊 市场图表查看器")
    print("="*50)
    
    # 列出所有图表
    charts = list_available_charts()
    
    if not charts:
        print("📭 没有找到图表文件")
        print("💡 请先运行以下命令生成图表:")
        print("   python enhanced_market_collector.py")
        print("   或者")
        print("   python demo_enhanced_collector.py")
        return
    
    print(f"📈 找到 {len(charts)} 个图表文件:")
    print("-" * 30)
    
    # 按行业分组显示
    industries = {}
    for chart in charts:
        # 提取行业名称
        industry = chart.split('_')[0] + '_' + chart.split('_')[1]
        if industry not in industries:
            industries[industry] = []
        industries[industry].append(chart)
    
    chart_index = 1
    chart_map = {}
    
    for industry, industry_charts in industries.items():
        industry_name = industry.replace('_', ' ').title()
        print(f"\n🏭 {industry_name}:")
        
        for chart in industry_charts:
            chart_type = "未知类型"
            if "market_size" in chart:
                chart_type = "市场规模趋势图"
            elif "segments" in chart:
                chart_type = "市场细分饼图"
            elif "companies" in chart:
                chart_type = "公司对比图"
            
            print(f"   {chart_index}. {chart} ({chart_type})")
            chart_map[chart_index] = chart
            chart_index += 1
    
    print("\n" + "="*50)
    print("🎯 选择操作:")
    print("1. 输入数字打开对应图表")
    print("2. 输入 'all' 打开所有图表")
    print("3. 输入 'exit' 退出")
    
    while True:
        try:
            choice = input("\n请选择 (数字/all/exit): ").strip().lower()
            
            if choice == 'exit':
                print("👋 再见！")
                break
            elif choice == 'all':
                print("🚀 正在打开所有图表...")
                for chart in charts:
                    open_chart_in_browser(chart)
                print("✅ 所有图表已在浏览器中打开")
                break
            else:
                try:
                    chart_num = int(choice)
                    if chart_num in chart_map:
                        chart_name = chart_map[chart_num]
                        show_chart_info(chart_name)
                        open_chart_in_browser(chart_name)
                    else:
                        print("❌ 无效的选择，请输入正确的数字")
                except ValueError:
                    print("❌ 请输入有效的数字")
                    
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break

if __name__ == "__main__":
    main() 