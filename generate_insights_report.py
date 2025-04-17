import os
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

from collectors.tavily_collector import TavilyCollector
from collectors.news_collector import NewsCollector
from generators.report_generator import ReportGenerator
import config

def generate_industry_insights_without_api(topic, subtopics=None):
    """
    在没有API密钥的情况下生成行业洞察
    参考元宇宙发展洞察报告的结构
    """
    # 基于行业洞察报告的典型章节结构
    insights_sections = {
        f"{topic}产业概况与历史发展": f"本节将介绍{topic}产业的定义、发展历程以及当前市场状况。",
        "政策与法规支持": f"分析{topic}相关的政策环境、法规框架及政府支持措施。",
        "市场规模与增长趋势": f"探讨{topic}市场的当前规模、增长率以及未来预测。",
        "技术趋势与创新": f"研究{topic}领域的关键技术发展方向、创新点以及技术突破。",
        "行业案例与实践": f"分析{topic}在各个领域的成功应用案例和最佳实践。",
        "PEST分析": f"从政治(Political)、经济(Economic)、社会(Social)、技术(Technological)四个维度分析{topic}产业。",
        "未来展望与建议": f"对{topic}的发展前景进行预测，并提出发展建议。"
    }
    
    # 转换为文章格式
    current_date = datetime.now().strftime('%Y-%m-%d')
    articles = []
    
    for section, content in insights_sections.items():
        article = {
            'title': section,
            'authors': ['行业分析'],
            'summary': content,
            'published': current_date,
            'url': '#',
            'source': '系统分析',
            'content': content
        }
        articles.append(article)
    
    return articles

def get_industry_insights(topic, subtopics=None):
    """
    获取行业洞察数据
    
    Args:
        topic (str): 主题
        subtopics (list): 子主题列表
        
    Returns:
        dict: 包含行业洞察内容和来源的字典
    """
    print(f"\n=== 收集{topic}行业洞察 ===")
    print(f"子主题: {subtopics if subtopics else '无'}")
    
    tavily_collector = TavilyCollector()
    
    try:
        # 尝试从Tavily获取数据
        industry_insights_data = tavily_collector.get_industry_insights(topic, subtopics)
        
        # 检查返回的是新格式(字典)还是旧格式(列表)
        if isinstance(industry_insights_data, dict):
            print(f"已获取结构化行业洞察报告，包含{len(industry_insights_data.get('sections', []))}个章节")
            return industry_insights_data
        else:
            # 旧格式，进行适当处理
            print("获取到旧格式的行业洞察数据，进行适当处理...")
            content = "# " + topic + "行业洞察\n\n"
            sections = []
            sources = []
            
            for i, article in enumerate(industry_insights_data):
                section = {
                    "title": article.get('title', f"第{i+1}部分"),
                    "content": article.get('content', "无内容")
                }
                sections.append(section)
                
                # 收集来源
                if article.get('url', '#') != '#':
                    sources.append({
                        "title": article.get('title', "未知标题"),
                        "url": article.get('url', '#'),
                        "source": article.get('source', "未知来源")
                    })
            
            return {
                "title": f"{topic}行业洞察",
                "sections": sections,
                "sources": sources,
                "date": datetime.now().strftime('%Y-%m-%d')
            }
            
    except Exception as e:
        print(f"API搜索出错: {str(e)}，使用系统生成的内容...")
        
        # 使用备选方法生成内容
        fallback_insights = generate_industry_insights_without_api(topic, subtopics)
        
        # 转换为标准格式
        content = "# " + topic + "行业洞察 (系统生成)\n\n"
        sections = []
        sources = []
        
        for article in fallback_insights:
            section = {
                "title": article.get('title', "未知部分"),
                "content": article.get('content', "无内容")
            }
            sections.append(section)
        
        return {
            "title": f"{topic}行业洞察 (系统生成)",
            "sections": sections,
            "sources": sources,
            "date": datetime.now().strftime('%Y-%m-%d')
        }

def generate_insights_report(topic, subtopics=None, output_file=None):
    """
    生成行业洞察报告
    
    Args:
        topic (str): 主题
        subtopics (list): 子主题列表
        output_file (str): 输出文件名或路径
        
    Returns:
        tuple: (报告文件路径, 报告数据)
    """
    # 确保输出目录存在
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    # 获取行业洞察数据
    insights_data = get_industry_insights(topic, subtopics)
    
    # 提取内容并格式化
    title = insights_data.get("title", f"{topic}行业洞察")
    date = insights_data.get("date", datetime.now().strftime('%Y-%m-%d'))
    
    content = f"# {title}\n\n"
    
    # 添加章节内容
    for section in insights_data.get("sections", []):
        section_title = section.get("title", "未知部分")
        section_content = section.get("content", "无内容")
        content += f"## {section_title}\n\n{section_content}\n\n"
    
    # 添加参考资料
    sources = insights_data.get("sources", [])
    if sources:
        content += "## 参考资料\n\n"
        for source in sources:
            content += f"- [{source.get('title', '未知标题')}]({source.get('url', '#')}) - {source.get('source', '未知来源')}\n"
    
    # 确定输出文件路径
    if not output_file:
        # 如果没有提供输出文件，使用默认命名
        date_str = datetime.now().strftime('%Y%m%d')
        output_file = os.path.join(config.OUTPUT_DIR, f"{topic.replace(' ', '_').lower()}_insights_report_{date_str}.md")
    elif not os.path.isabs(output_file):
        # 如果提供的是相对路径，确保正确拼接
        # 检查输出文件所在目录是否存在
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
    
    # 写入报告
    with open(output_file, 'w', encoding='utf-8-sig') as f:
        f.write(content)
    
    print(f"\n=== 行业洞察报告生成完成 ===")
    print(f"报告已保存至: {output_file}")
    
    return output_file, insights_data

if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='生成行业洞察报告')
    parser.add_argument('--topic', type=str, required=True, help='报告的主题')
    parser.add_argument('--subtopics', type=str, nargs='*', help='与主题相关的子主题')
    parser.add_argument('--output', type=str, help='输出文件名')
    
    args = parser.parse_args()
    
    # 生成报告
    generate_insights_report(args.topic, args.subtopics, args.output) 