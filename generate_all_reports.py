import os
import argparse
import time
from datetime import datetime
from dotenv import load_dotenv
import json
import sys
from fix_md_headings import fix_markdown_headings

import config
from generate_news_report import generate_news_report
from generate_research_report import generate_research_report
from generate_insights_report import generate_insights_report

def create_report_directory(topic, timestamp=None):
    """
    创建一个按主题和时间组织的报告目录
    
    Args:
        topic (str): 报告主题
        timestamp (str, optional): 时间戳，默认为当前时间
        
    Returns:
        str: 报告目录的路径
    """
    # 规范化主题名称，去除特殊字符
    safe_topic = topic.replace(' ', '_').replace('/', '_').replace('\\', '_').lower()
    
    # 使用提供的时间戳或当前时间
    timestamp = timestamp or datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 创建目录路径
    report_dir = os.path.join(config.OUTPUT_DIR, f"{safe_topic}_{timestamp}")
    
    # 确保目录存在
    os.makedirs(report_dir, exist_ok=True)
    
    return report_dir

def generate_combined_report(topic, subtopics=None, companies=None, days=7):
    """
    生成完整的三部分报告，并将它们合并成一个
    
    Args:
        topic (str): 主题
        subtopics (list): 子主题列表
        companies (list): 公司列表
        days (int): 天数范围
        
    Returns:
        str: 合并报告的文件路径
    """
    print(f"\n===== 开始为 {topic} 生成完整报告 =====")
    print(f"子主题: {subtopics if subtopics else '无'}")
    print(f"追踪公司: {companies if companies else '无'}")
    print(f"时间范围: {days}天")
    
    # 创建唯一的报告目录
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = create_report_directory(topic, timestamp)
    
    # 生成三个独立报告
    news_filepath, news_data = generate_news_report(
        topic, 
        companies, 
        days, 
        os.path.join(report_dir, "news_report.md")
    )
    
    research_filepath, research_data = generate_research_report(
        topic, 
        subtopics, 
        days, 
        os.path.join(report_dir, "research_report.md")
    )
    
    insights_filepath, insights_data = generate_insights_report(
        topic, 
        subtopics, 
        os.path.join(report_dir, "insights_report.md")
    )
    
    # 创建完整报告
    # 生成报告文件名
    combined_filename = "complete_report.md"
    
    # 文件完整路径
    combined_filepath = os.path.join(report_dir, combined_filename)
    
    # 准备报告内容
    intro_content = f"""# {topic}行业趋势完整报告（{datetime.now().strftime('%Y年%m月%d日')}）

本报告包含三个主要部分：行业最新动态、研究方向和行业洞察。通过多种渠道收集和分析数据，为您提供全面的行业视角。

## 目录

1. [行业最新动态](#行业最新动态) - 主要公司和组织的最新动向
2. [研究方向](#研究方向) - 学术界和研究机构的前沿探索
3. [行业洞察](#行业洞察) - 市场趋势、政策环境和未来展望

---

"""
    
    # 读取并组合三个报告
    with open(news_filepath, 'r', encoding='utf-8-sig') as f:
        news_content = f.read()
        
    with open(research_filepath, 'r', encoding='utf-8-sig') as f:
        research_content = f.read()
        
    with open(insights_filepath, 'r', encoding='utf-8-sig') as f:
        insights_content = f.read()
    
    # 合并报告内容
    combined_content = intro_content + news_content + "\n\n" + research_content + "\n\n" + insights_content
    
    # 写入合并报告
    with open(combined_filepath, 'w', encoding='utf-8-sig') as f:
        f.write(combined_content)
    
    # 创建索引文件，记录各个报告的位置和详情
    index_data = {
        "topic": topic,
        "timestamp": timestamp,
        "generation_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "report_directory": report_dir,
        "reports": {
            "complete": {"filepath": combined_filepath, "type": "complete"},
            "news": {"filepath": news_filepath, "type": "news"},
            "research": {"filepath": research_filepath, "type": "research"},
            "insights": {"filepath": insights_filepath, "type": "insights"}
        },
        "parameters": {
            "subtopics": subtopics,
            "companies": companies,
            "days": days
        }
    }
    
    # 将索引数据写入JSON文件
    index_filepath = os.path.join(report_dir, "report_index.json")
    with open(index_filepath, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n===== 完整报告生成完成 =====")
    print(f"报告目录: {report_dir}")
    print(f"完整报告: {combined_filepath}")
    print(f"各部分报告:")
    print(f"- 行业最新动态: {news_filepath}")
    print(f"- 研究方向: {research_filepath}")
    print(f"- 行业洞察: {insights_filepath}")
    print(f"索引文件: {index_filepath}")
    
    # 修复报告中的标题问题
    print("正在优化报告标题格式...")
    fix_markdown_headings(combined_filepath)
    
    return combined_filepath

def main():
    """主程序入口"""
    # 加载环境变量
    load_dotenv()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='生成行业趋势报告')
    parser.add_argument('--topic', type=str, required=True, help='报告的主题')
    parser.add_argument('--subtopics', type=str, nargs='*', help='与主题相关的子主题')
    parser.add_argument('--companies', type=str, nargs='*', 
                      default=["OpenAI", "Anthropic", "Google", "Microsoft", "Meta"], 
                      help='要追踪的公司')
    parser.add_argument('--days', type=int, default=7, help='搜索内容的天数范围')
    parser.add_argument('--type', type=str, default='all', 
                      choices=['all', 'news', 'research', 'insights'], 
                      help='报告类型: all=全部, news=行业最新动态, research=研究方向, insights=行业洞察')
    parser.add_argument('--interactive', '-i', action='store_true', 
                        help='使用交互式模式')
    
    args = parser.parse_args()
    
    # 如果指定了交互式模式，使用交互式模式
    if args.interactive:
        interactive_mode()
        return
    
    # 创建报告目录
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = create_report_directory(args.topic, timestamp)
    
    # 根据指定的报告类型生成报告
    if args.type == 'news' or args.type == 'all':
        news_filepath, _ = generate_news_report(
            args.topic, 
            args.companies, 
            args.days,
            os.path.join(report_dir, "news_report.md")
        )
        
    if args.type == 'research' or args.type == 'all':
        research_filepath, _ = generate_research_report(
            args.topic, 
            args.subtopics, 
            args.days,
            os.path.join(report_dir, "research_report.md")
        )
        
    if args.type == 'insights' or args.type == 'all':
        insights_filepath, _ = generate_insights_report(
            args.topic, 
            args.subtopics,
            os.path.join(report_dir, "insights_report.md")
        )
        
    # 如果是全部类型，还需要生成合并报告
    if args.type == 'all':
        generate_combined_report(args.topic, args.subtopics, args.companies, args.days)
    else:
        print(f"\n===== 报告生成完成 =====")
        print(f"报告目录: {report_dir}")
        if args.type == 'news':
            print(f"行业最新动态报告: {news_filepath}")
        elif args.type == 'research':
            print(f"研究方向报告: {research_filepath}")
        elif args.type == 'insights':
            print(f"行业洞察报告: {insights_filepath}")

def interactive_mode():
    """交互式模式，让用户输入参数"""
    print("\n===== 行业趋势报告生成器 =====\n")
    
    # 获取用户输入的行业名称
    topic = input("请输入您想要生成报告的行业名称（例如：人工智能、区块链、元宇宙等）: ").strip()
    if not topic:
        print("错误：行业名称不能为空。")
        return
    
    # 询问用户是否要添加子主题
    add_subtopics = input("\n是否要添加子主题？(y/n，默认为n): ").strip().lower()
    subtopics = None
    if add_subtopics == 'y':
        subtopics_input = input("请输入子主题，用空格分隔（例如：机器学习 深度学习 自然语言处理）: ").strip()
        if subtopics_input:
            subtopics = subtopics_input.split()
    
    # 询问公司信息
    custom_companies = input("\n是否要自定义追踪的公司？(y/n，默认为n): ").strip().lower()
    companies = ["OpenAI", "Anthropic", "Google", "Microsoft", "Meta"]
    if custom_companies == 'y':
        companies_input = input("请输入公司名称，用空格分隔（例如：阿里巴巴 腾讯 百度 华为）: ").strip()
        if companies_input:
            companies = companies_input.split()
    
    # 设置天数范围
    days = 7
    days_input = input("\n请输入需要搜索的天数范围(默认为7天): ").strip()
    if days_input and days_input.isdigit():
        days = int(days_input)
    
    # 让用户选择报告类型
    print("\n请选择要生成的报告类型：")
    print("1. 全面报告（包含行业动态、研究方向和行业洞察）")
    print("2. 仅行业动态（主要公司和组织的最新动态）")
    print("3. 仅研究方向（学术界最新研究）")
    print("4. 仅行业洞察（全面的产业分析，包括产业概况、政策、市场、技术趋势、案例等）")
    
    report_type = input("\n请输入选项(1-4，默认为1): ").strip()
    
    # 创建报告目录
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = create_report_directory(topic, timestamp)
    
    if not report_type or report_type == "1":
        generate_combined_report(topic, subtopics, companies, days)
    elif report_type == "2":
        news_filepath, _ = generate_news_report(
            topic, 
            companies, 
            days,
            os.path.join(report_dir, "news_report.md")
        )
        print(f"\n===== 行业最新动态报告生成完成 =====")
        print(f"报告已保存至: {news_filepath}")
    elif report_type == "3":
        research_filepath, _ = generate_research_report(
            topic, 
            subtopics, 
            days,
            os.path.join(report_dir, "research_report.md")
        )
        print(f"\n===== 研究方向报告生成完成 =====")
        print(f"报告已保存至: {research_filepath}")
    elif report_type == "4":
        insights_filepath, _ = generate_insights_report(
            topic, 
            subtopics,
            os.path.join(report_dir, "insights_report.md")
        )
        print(f"\n===== 行业洞察报告生成完成 =====")
        print(f"报告已保存至: {insights_filepath}")
    else:
        print("无效的选项，使用默认选项1（全面报告）")
        generate_combined_report(topic, subtopics, companies, days)

if __name__ == "__main__":
    main() 