import os
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
import sys
from fix_md_headings import fix_markdown_headings

from collectors.tavily_collector import TavilyCollector
from generators.report_generator import ReportGenerator
import config

def get_industry_news_comprehensive(topic, days=7, companies=None):
    """
    获取全面的行业动态信息
    
    Args:
        topic (str): 行业主题
        days (int): 天数范围
        companies (list): 公司列表，可选
        
    Returns:
        dict: 包含行业动态数据和报告内容的字典
    """
    print(f"\n=== 开始收集{topic}行业全面动态 ===")
    
    # 初始化数据收集器和LLM处理器
    tavily_collector = TavilyCollector()
    llm_processor = tavily_collector._get_llm_processor()
    
    # 首先使用直接搜索获取行业新闻数据，不依赖于特定公司
    # 这将提供更全面的行业视角，而不是仅关注大公司
    all_news_data = tavily_collector.get_industry_news_direct(topic, days)
    
    # 如果提供了公司列表，收集这些公司的特定新闻作为补充
    company_specifics = []
    if companies and isinstance(companies, list):
        print(f"\n=== 收集{len(companies)}家公司特定新闻作为补充 ===")
        # 调整每家公司的新闻数量，确保不会过于偏重大公司
        max_news_per_company = max(2, 10 // len(companies))
        
        for company in companies:
            company_news = tavily_collector.get_company_news(
                company, topic, days, max_results=max_news_per_company
            )
            if company_news:
                # 将公司新闻添加到公司特定部分
                company_specifics.append({
                    "company": company,
                    "news": company_news
                })
                print(f"找到 {len(company_news)} 条 {company} 相关新闻")
            else:
                print(f"未找到 {company} 相关新闻")
        
        # 将公司特定新闻添加到总数据中
        all_news_data["company_news"] = [item for company_data in company_specifics for item in company_data["news"]]
    
    print(f"\n=== 收集完成，开始处理报告内容 ===")
    
    # 初始化报告内容
    content = f"# {topic}行业最新动态报告\n\n"
    date_str = datetime.now().strftime('%Y-%m-%d')
    content += f"报告日期: {date_str}\n\n"
    
    # 1. 首先处理重大新闻部分
    breaking_news = all_news_data.get("breaking_news", [])
    breaking_news_content = process_breaking_news(llm_processor, topic, breaking_news)
    content += breaking_news_content
    
    # 2. 处理创新新闻部分
    innovation_news = all_news_data.get("innovation_news", [])
    innovation_news_content = process_innovation_news(llm_processor, topic, innovation_news)
    content += innovation_news_content
    
    # 3. 处理投资新闻部分
    investment_news = all_news_data.get("investment_news", [])
    investment_news_content = process_investment_news(llm_processor, topic, investment_news)
    content += investment_news_content
    
    # 4. 处理政策监管动态
    policy_news = all_news_data.get("policy_news", [])
    policy_content = process_policy_news(llm_processor, topic, policy_news)
    content += policy_content
    
    # 5. 处理行业趋势新闻
    trend_news = all_news_data.get("trend_news", [])
    trend_content = process_industry_trends(llm_processor, topic, trend_news)
    content += trend_content
    
    # 6. 如果有公司特定新闻，生成公司动态部分
    company_news = all_news_data.get("company_news", [])
    if company_news and company_specifics:
        content += "## 重点公司动态\n\n"
        
        # 为每个有新闻的公司生成小节
        for company_data in company_specifics:
            company = company_data["company"]
            news_items = company_data["news"]
            
            if news_items:
                company_summary = process_company_news(llm_processor, topic, company, news_items)
                content += company_summary + "\n\n"
    
    # 7. 最后生成趋势总结章节（对整个行业的分析）
    trend_summary = generate_comprehensive_trend_summary(llm_processor, topic, all_news_data)
    content += trend_summary
    
    # 8. 收集所有参考资料
    references = []
    
    for news_type in ["breaking_news", "innovation_news", "trend_news", "policy_news", "investment_news", "company_news"]:
        for item in all_news_data.get(news_type, []):
            title = item.get('title', '未知标题')
            url = item.get('url', '#')
            source = item.get('source', '未知来源')
            if url != '#':
                references.append(f"- [{title}]({url}) - {source}")
    
    # 去重参考资料
    unique_references = list(set(references))
    
    # 添加参考资料章节
    content += "\n\n## 参考资料\n\n"
    content += "\n".join(unique_references)
    
    # 返回结果
    return {
        "content": content,
        "data": all_news_data,
        "date": date_str
    }

def process_breaking_news(llm_processor, topic, breaking_news):
    """处理行业重大新闻"""
    if not breaking_news:
        return f"## 行业重大事件\n\n目前暂无{topic}行业的重大新闻。\n\n"
    
    # 提取所有重大新闻的关键信息
    all_news_text = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
        for item in breaking_news
    ])
    
    prompt = f"""
    请基于以下{topic}行业的最新重大新闻，提供简洁但全面的摘要，突出最重要的事件和发展。
    
    {all_news_text}
    
    请提供:
    1. 每条重大新闻的简要摘要，包括事件的关键细节
    2. 对这些事件可能对{topic}行业产生的影响的简要分析
    3. 相关企业、技术或市场的必要背景信息
    
    要求:
    - 保持客观，专注于事实
    - 按重要性排序
    - 特别关注可能改变行业格局的突发事件
    - 长度控制在800-1000字
    """
    
    system = f"你是一位权威的{topic}行业分析师，擅长从复杂信息中提取和总结最重要的行业事件与发展。"
    
    try:
        breaking_news_summary = llm_processor.call_llm_api(prompt, system)
        
        # 收集这部分使用的新闻来源
        news_sources = []
        for item in breaking_news:
            title = item.get('title', '未知标题')
            url = item.get('url', '#')
            source = item.get('source', '未知来源')
            if url != '#':
                news_sources.append(f"- [{title}]({url}) - {source}")
        
        # 添加来源到摘要末尾
        if news_sources:
            breaking_news_summary += "\n\n**来源:**\n" + "\n".join(news_sources)
            
        return f"## 行业重大事件\n\n{breaking_news_summary}\n\n"
    except Exception as e:
        print(f"生成行业重大事件摘要时出错: {str(e)}")
        return f"## 行业重大事件\n\n暂无{topic}行业重大事件摘要。\n\n"

def process_innovation_news(llm_processor, topic, innovation_news):
    """处理技术创新新闻"""
    if not innovation_news:
        return f"## 技术创新与新产品\n\n目前暂无{topic}行业的技术创新新闻。\n\n"
    
    # 提取所有创新新闻的关键信息
    all_news_text = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
        for item in innovation_news
    ])
    
    prompt = f"""
    请基于以下{topic}行业的最新技术创新和产品发布信息，提供综合分析。
    
    {all_news_text}
    
    请提供:
    1. 主要技术突破和创新点的摘要
    2. 新产品或服务的关键特性和潜在影响
    3. 这些创新如何影响{topic}行业的发展方向
    4. 可能的市场反应和消费者采纳情况
    
    要求:
    - 专注于技术细节和创新点
    - 解释复杂概念时使用通俗易懂的语言
    - 分析创新的实际应用价值
    - 长度控制在600-800字
    """
    
    system = f"你是一位专精于{topic}领域技术的分析师，擅长评估技术创新的潜力和影响。"
    
    try:
        innovation_summary = llm_processor.call_llm_api(prompt, system)
        
        # 收集这部分使用的新闻来源
        news_sources = []
        for item in innovation_news:
            title = item.get('title', '未知标题')
            url = item.get('url', '#')
            source = item.get('source', '未知来源')
            if url != '#':
                news_sources.append(f"- [{title}]({url}) - {source}")
        
        # 添加来源到摘要末尾
        if news_sources:
            innovation_summary += "\n\n**来源:**\n" + "\n".join(news_sources)
            
        return f"## 技术创新与新产品\n\n{innovation_summary}\n\n"
    except Exception as e:
        print(f"生成技术创新摘要时出错: {str(e)}")
        return f"## 技术创新与新产品\n\n暂无{topic}行业技术创新摘要。\n\n"

def process_investment_news(llm_processor, topic, investment_news):
    """处理投资新闻"""
    if not investment_news:
        return f"## 投资与市场动向\n\n目前暂无{topic}行业的投资相关新闻。\n\n"
    
    # 提取所有投资新闻的关键信息
    all_news_text = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
        for item in investment_news
    ])
    
    prompt = f"""
    请基于以下{topic}行业的最新投资、融资和市场变动信息，提供财务和市场分析。
    
    {all_news_text}
    
    请提供:
    1. 主要投资、并购或融资事件的摘要，包括金额和参与方
    2. 资金流向分析 - 哪些细分领域获得了最多关注
    3. 这些投资如何反映行业的发展趋势和市场信心
    4. 值得关注的新兴公司或领域
    
    要求:
    - 包含关键的财务数据和估值信息
    - 分析投资背后的战略考量
    - 评估这些投资对行业格局的潜在影响
    - 长度控制在600-800字
    """
    
    system = f"你是一位专注于{topic}行业的投资分析师，擅长解读融资事件和市场动向。"
    
    try:
        investment_summary = llm_processor.call_llm_api(prompt, system)
        
        # 收集这部分使用的新闻来源
        news_sources = []
        for item in investment_news:
            title = item.get('title', '未知标题')
            url = item.get('url', '#')
            source = item.get('source', '未知来源')
            if url != '#':
                news_sources.append(f"- [{title}]({url}) - {source}")
        
        # 添加来源到摘要末尾
        if news_sources:
            investment_summary += "\n\n**来源:**\n" + "\n".join(news_sources)
            
        return f"## 投资与市场动向\n\n{investment_summary}\n\n"
    except Exception as e:
        print(f"生成投资动向摘要时出错: {str(e)}")
        return f"## 投资与市场动向\n\n暂无{topic}行业投资动向摘要。\n\n"

def process_industry_trends(llm_processor, topic, trend_news):
    """处理行业趋势新闻，生成详细的趋势分析"""
    if not trend_news:
        return f"## 行业趋势概览\n\n目前暂无{topic}行业的趋势分析。\n\n"
    
    # 提取所有趋势新闻的关键信息
    all_news_text = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
        for item in trend_news
    ])
    
    trend_prompt = f"""
    请基于以下{topic}行业的最新趋势相关新闻，分析并总结行业整体趋势和发展方向。
    
    {all_news_text}
    
    请提供详细的行业趋势分析，内容需要包括：
    1. {topic}行业的整体发展趋势和主要特征
    2. 市场规模、增长率和主要驱动因素
    3. 技术发展路线和创新焦点
    4. 值得关注的新技术、新产品或新模式
    5. 行业面临的挑战、机遇和潜在风险
    6. 区域发展差异和国际竞争格局
    7. 产业链上下游发展情况
    8. 对未来3-5年的预测和展望
    
    要求:
    - 使用专业、客观的语言
    - 提供具体数据和事实支持你的观点
    - 分析要深入且有洞察力，不要停留在表面现象
    - 适当引用新闻中的关键信息作为支撑
    - 对各个趋势进行详细展开解释，而不仅是罗列要点
    - 使用小标题组织内容，使分析更有结构
    - 长度要充分，约1000-1200字
    """
    
    trend_system = f"""你是一位权威的{topic}行业趋势分析专家，拥有丰富的行业经验和深刻的洞察力。
    你擅长从零散信息中提炼出行业发展的关键趋势，并能够预测未来发展方向。
    你的分析需要专业、深入且全面，覆盖行业的各个重要方面，同时保持客观公正。
    每个趋势点都需要充分展开解释，提供足够的事实、数据和案例支持。
    你的回答应该是一篇可以直接发表的高质量行业分析报告。"""
    
    try:
        industry_trend = llm_processor.call_llm_api(trend_prompt, trend_system)
        
        # 收集这部分使用的新闻来源
        news_sources = []
        for item in trend_news:
            title = item.get('title', '未知标题')
            url = item.get('url', '#')
            source = item.get('source', '未知来源')
            if url != '#':
                news_sources.append(f"- [{title}]({url}) - {source}")
        
        # 添加来源到摘要末尾
        if news_sources:
            industry_trend += "\n\n**来源:**\n" + "\n".join(news_sources)
            
        return f"## 行业趋势深度分析\n\n{industry_trend}\n\n"
    except Exception as e:
        print(f"生成行业趋势分析时出错: {str(e)}")
        return f"## 行业趋势概览\n\n暂无{topic}行业趋势分析。\n\n"

def process_company_news(llm_processor, topic, company, news_items):
    """处理单个公司的新闻"""
    if not news_items:
        return f"### {company}\n\n暂无{company}相关的最新动态。\n\n"
    
    # 准备新闻内容
    news_text = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')}\n链接: {item.get('url', '#')}"
        for item in news_items
    ])
    
    # 提示生成摘要
    prompt = f"""
    请分析以下关于{company}公司的最新新闻报道，并撰写一份总结，突出该公司在{topic}领域的最新动态、产品发布、战略调整或其他重要事件。
    
    {news_text}
    
    总结要求:
    1. 使用专业、客观的语言
    2. 保留关键事实和数据
    3. 按时间或重要性进行结构化组织
    4. 突出与{topic}行业相关的信息
    5. 长度控制在300-500字以内
    """
    
    system_message = f"你是一位专业的{topic}行业分析师，擅长从新闻报道中提取和总结公司的战略动态和最新发展。"
    
    try:
        summary = llm_processor.call_llm_api(prompt, system_message)
        
        # 收集这部分使用的新闻来源
        news_sources = []
        for item in news_items:
            title = item.get('title', '未知标题')
            url = item.get('url', '#')
            source = item.get('source', '未知来源')
            if url != '#':
                news_sources.append(f"- [{title}]({url}) - {source}")
        
        # 添加来源到摘要末尾
        if news_sources:
            summary += "\n\n**来源:**\n" + "\n".join(news_sources)
            
        return f"### {company}\n\n{summary}"
    except Exception as e:
        print(f"为 {company} 生成摘要时出错: {str(e)}")
        # 失败时添加基本内容
        basic_content = "\n\n".join([f"- {item.get('title', '无标题')}" for item in news_items])
        return f"### {company}\n\n{basic_content}"

def process_policy_news(llm_processor, topic, policy_news):
    """处理政策监管动态"""
    if not policy_news:
        return f"## 政策与监管动态\n\n目前暂无{topic}行业的政策相关新闻。\n\n"
    
    # 提取所有政策新闻的关键信息
    all_news_text = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
        for item in policy_news
    ])
    
    prompt = f"""
    请基于以下{topic}行业的最新政策和监管信息，提供详细分析。
    
    {all_news_text}
    
    请提供:
    1. 各项政策和监管动态的概述
    2. 这些政策对{topic}行业的潜在影响
    3. 企业应如何应对这些政策变化
    4. 政策趋势判断和未来展望
    
    要求:
    - 专注于政策内容和实质影响
    - 分析政策背后的意图和导向
    - 对比国内外政策差异(如有)
    - 长度控制在800-1000字
    """
    
    system = f"你是一位专精于{topic}行业政策分析的专家，擅长分析政策对行业发展的影响。"
    
    try:
        policy_summary = llm_processor.call_llm_api(prompt, system, max_tokens=8000)
        
        # 收集这部分使用的新闻来源
        news_sources = []
        for item in policy_news:
            title = item.get('title', '未知标题')
            url = item.get('url', '#')
            source = item.get('source', '未知来源')
            if url != '#':
                news_sources.append(f"- [{title}]({url}) - {source}")
        
        # 添加来源到摘要末尾
        if news_sources:
            policy_summary += "\n\n**来源:**\n" + "\n".join(news_sources)
            
        return f"## 政策与监管动态\n\n{policy_summary}\n\n"
    except Exception as e:
        print(f"生成政策分析摘要时出错: {str(e)}")
        return f"## 政策与监管动态\n\n暂无{topic}行业政策分析摘要。\n\n"

def generate_comprehensive_trend_summary(llm_processor, topic, all_news_data):
    """生成简短的行业趋势概况总结"""
    
    # 构建一个简短的总结提示
    prompt = f"""
    请针对上述已分析的{topic}行业各个方面（重大事件、技术创新、投资动向、政策监管、行业趋势等），
    提供一个简短的总体概括和趋势总结。不要重复之前的详细内容，只需简明扼要地突出核心观点。
    
    要求:
    1. 这是对已有内容的概括总结，不需要引入全新信息
    2. 长度控制在300-400字以内
    3. 使用简洁、专业的语言
    4. 突出核心趋势和对企业的建议
    5. 不需要添加参考来源
    """
    
    system = f"""你是一位{topic}行业资深分析师，现在需要你对一份行业报告的各部分内容做一个简洁的总结概括。
这个总结应当点明全局趋势，不再重复已有内容的细节，只需提炼核心观点。请保持简短精练。"""
    
    try:
        summary = llm_processor.call_llm_api(prompt, system, max_tokens=3000)
        return f"## 行业趋势总结\n\n{summary}\n\n"
    except Exception as e:
        print(f"生成行业趋势总结时出错: {str(e)}")
        return f"## 行业趋势总结\n\n{topic}行业正处于快速发展阶段，上述分析反映了当前市场的主要动态和未来发展方向。\n\n"

def generate_news_report(topic, companies=None, days=7, output_file=None):
    """
    生成行业新闻报告
    
    Args:
        topic (str): 行业主题
        companies (list, optional): 重点关注的公司列表
        days (int): 收集最近几天的新闻
        output_file (str, optional): 输出文件路径
        
    Returns:
        str: 报告内容
    """
    print(f"\n=== 开始生成{topic}行业新闻报告 ===")
    
    # 1. 获取行业动态数据
    report_data = get_industry_news_comprehensive(topic, days, companies)
    
    # 2. 获取报告内容
    report_content = report_data["content"]
    
    # 如果未指定输出文件，使用默认路径
    if not output_file:
        # 创建日期字符串用于文件名
        date_str = datetime.now().strftime('%Y%m%d')
        # 默认保存到reports目录
        reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        # 生成安全的文件名
        safe_topic = "".join([c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in topic])
        safe_topic = safe_topic.replace(' ', '_')
        # 设置默认文件名
        output_file = os.path.join(reports_dir, f"{safe_topic}_行业报告_{date_str}.md")
        print(f"未指定输出路径，将使用默认路径: {output_file}")
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    
    # 3. 优化格式 - 在保存前修复Markdown格式
    try:
        report_content = fix_markdown_headings(report_content)
        print("报告格式已优化")
    except Exception as e:
        print(f"修复Markdown格式时出错: {str(e)}")
    
    # 保存报告内容到文件
    try:
        from report_utils import safe_save_report
        safe_save_report(report_content, output_file)
    except ImportError:
        # 如果没有导入成功，使用标准方式保存
        print("注意：未找到report_utils模块，使用标准方式保存文件")
        with open(output_file, "w", encoding="utf-8-sig") as f:
            f.write(report_content)
    
    print(f"报告已保存到: {output_file}")
    
    return report_content

if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='生成行业最新动态报告')
    parser.add_argument('--topic', type=str, required=True, help='报告的主题')
    parser.add_argument('--companies', type=str, nargs='*', 
                      help='要特别关注的公司（可选）')
    parser.add_argument('--days', type=int, default=7, help='搜索内容的天数范围')
    parser.add_argument('--output', type=str, help='输出文件名或路径')
    
    # 添加说明文档
    parser.epilog = """
    报告生成说明:
    1. 本工具现已优化为"行业优先"的信息采集模式，更全面地覆盖整个行业动态
    2. 报告将包含以下主要内容:
       - 行业概况：对指定行业的整体概述
       - 突发新闻：最新重要事件的分析
       - 前沿创新：研发与技术突破的分析
       - 投资动态：资金流向与投资趋势分析
       - 政策法规：监管变化与政策影响分析
       - 行业趋势总结：基于所有收集信息的综合分析，特别关注趋势类新闻
    3. 使用示例:
       python generate_news_report.py --topic "人工智能" --days 10 --output "AI行业动态报告.md"
    """
    
    args = parser.parse_args()
    
    # 生成报告
    generate_news_report(args.topic, args.companies, args.days, args.output) 