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
    - 长度要充分，至少1000-1500字
    """
    
    trend_system = f"""你是一位权威的{topic}行业趋势分析专家，拥有丰富的行业经验和深刻的洞察力。
    你擅长从零散信息中提炼出行业发展的关键趋势，并能够预测未来发展方向。
    你的分析需要专业、深入且全面，覆盖行业的各个重要方面，同时保持客观公正。
    每个趋势点都需要充分展开解释，提供足够的事实、数据和案例支持。
    你的回答应该是一篇可以直接发表的高质量行业分析报告。"""
    
    try:
        industry_trend = llm_processor.call_llm_api(trend_prompt, trend_system)
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
        return f"### {company}\n\n{summary}"
    except Exception as e:
        print(f"为 {company} 生成摘要时出错: {str(e)}")
        # 失败时添加基本内容
        basic_content = "\n\n".join([f"- {item.get('title', '无标题')}" for item in news_items])
        return f"### {company}\n\n{basic_content}"

def process_policy_news(llm_processor, topic, policy_news):
    """处理政策新闻"""
    if not policy_news:
        return f"## 政策与监管动态\n\n目前暂无{topic}领域的政策监管相关新闻。\n\n"
    
    # 提取所有政策新闻的内容
    policy_text = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')}\n来源: {item.get('source', '未知')}"
        for item in policy_news
    ])
    
    policy_prompt = f"""
    请基于以下{topic}行业的最新政策相关新闻，总结分析当前的政策环境和监管动向。
    
    {policy_text}
    
    请提供:
    1. 主要的政策法规变化和发布
    2. 政策对{topic}行业发展的影响分析
    3. 政策背后的监管思路和趋势
    4. 企业应对这些政策的建议
    
    要求:
    - 使用专业、客观的语言
    - 准确理解政策内容和意图
    - 分析政策对行业不同参与者的影响
    - 长度控制在600-800字
    """
    
    policy_system = f"你是一位{topic}产业政策专家，擅长解读政策文件并分析其对行业的影响。"
    
    try:
        policy_analysis = llm_processor.call_llm_api(policy_prompt, policy_system)
        return f"## 政策与监管动态\n\n{policy_analysis}\n\n"
    except Exception as e:
        print(f"生成政策分析时出错: {str(e)}")
        # 失败时添加基本内容
        basic_content = "\n\n".join([f"- {item.get('title', '无标题')}" for item in policy_news])
        return f"## 政策与监管动态\n\n{basic_content}\n\n"

def generate_comprehensive_trend_summary(llm_processor, topic, all_news_data):
    """生成更为全面的趋势总结章节"""
    print(f"正在为{topic}行业生成全面趋势总结...")
    
    # 整合所有类型的新闻以提供全面视角，但优先考虑趋势新闻
    trend_news = all_news_data.get("trend_news", [])
    print(f"趋势分析主要基于 {len(trend_news)} 条趋势新闻")
    
    # 其他新闻作为补充
    other_news = []
    for category in ["breaking_news", "innovation_news", "policy_news", "investment_news"]:
        other_news.extend(all_news_data.get(category, []))
    
    # 组合所有新闻，但确保趋势新闻位于前列
    all_relevant_news = trend_news + other_news
    
    # 如果没有足够的新闻数据，返回简单提示
    if len(all_relevant_news) < 3:
        return f"## 行业趋势总结\n\n目前收集到的{topic}行业数据不足，无法生成全面的趋势总结。\n\n"
    
    # 提取最关键的新闻信息，区分趋势新闻和其他新闻
    key_trend_news = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:300]}...\n来源: {item.get('source', '未知')}\n类型: 趋势新闻"
        for item in trend_news[:10]  # 最多使用10条趋势新闻
    ])
    
    key_other_news = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:300]}...\n来源: {item.get('source', '未知')}\n类型: {item.get('news_type', '其他新闻')}"
        for item in other_news[:10]  # 最多使用10条其他新闻作为补充
    ])
    
    # 组合新闻内容
    news_content = key_trend_news
    if key_other_news:
        news_content += "\n\n=== 其他补充新闻 ===\n\n" + key_other_news
    
    summary_prompt = f"""
    请基于以下关于{topic}行业的新闻信息，撰写一份详尽的"行业趋势总结"章节，对整个行业做全面分析。
    
    {news_content}
    
    你的行业趋势总结需要：
    
    1. 开篇概述：简明扼要地概括{topic}行业的当前状态和总体发展趋势
    
    2. 分点详析：使用以下4-6个方面作为小标题，对每个方面进行深入剖析（每点至少200字）：
       - 市场格局变化：详细分析行业中的市场结构、主要玩家和竞争态势的变化
       - 技术创新趋势：详细分析推动行业发展的关键技术及其应用前景
       - 用户需求演变：详细分析客户/消费者行为和需求的变化及其影响
       - 商业模式创新：详细分析新兴的商业模式和盈利方式
       - 跨界融合发展：详细分析该行业与其他领域的融合创新趋势
       - 政策影响分析：详细分析监管环境变化及其影响
       
    3. 结论展望：对行业未来3-5年的发展做出有见地的预测，包括：
       - 潜在的增长点和机遇
       - 可能面临的挑战和风险
       - 关键成功因素的转变
    
    要求：
    - 所有分析都必须基于提供的新闻信息，同时结合行业知识做深入解读
    - 优先关注趋势新闻中反映的行业发展趋势
    - 每个小标题下的内容必须详尽，不能简单列点
    - 使用专业术语，但确保非专业人士也能理解
    - 引用具体事实、数据或案例支持你的分析
    - 突出行业发展的关键拐点和重大变革
    - 总体篇幅不少于1800字，确保内容充实且有深度
    """
    
    summary_system = f"""你是{topic}行业的顶级分析师，拥有15年以上行业经验，对行业发展有深刻理解和独特洞见。
    你的分析被业内广泛引用，因为它们深入、全面且有前瞻性，能准确把握行业趋势并预测行业未来发展方向。
    在这次任务中，你需要创作一篇高质量的行业趋势总结章节，它将成为一份完整行业报告的核心部分。
    你的分析需要详尽、有深度、有结构，能够为读者提供真正的价值和决策参考。"""
    
    try:
        trend_summary = llm_processor.call_llm_api(summary_prompt, summary_system)
        return f"## 行业趋势总结\n\n{trend_summary}\n\n"
    except Exception as e:
        print(f"生成行业趋势总结时出错: {str(e)}")
        fallback_summary = "无法生成详细的行业趋势总结，请查看报告其他部分获取相关信息。"
        return f"## 行业趋势总结\n\n{fallback_summary}\n\n"

def generate_news_report(topic, companies=None, days=7, output_file=None):
    """
    生成行业最新动态报告
    
    Args:
        topic (str): 主题
        companies (list): 公司列表，可选，如提供则会特别关注这些公司
        days (int): 天数范围
        output_file (str): 输出文件名或路径
        
    Returns:
        tuple: (报告文件路径, 报告数据)
    """
    # 确保输出目录存在
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    # 获取并处理新闻数据，使用全面的行业动态收集方法
    print(f"\n=== 开始收集{topic}行业全面动态 ===")
    
    # 初始化数据收集器和LLM处理器
    tavily_collector = TavilyCollector()
    llm_processor = tavily_collector._get_llm_processor()
    
    # 首先使用直接搜索获取行业新闻数据，不依赖于特定公司
    # 这将提供更全面的行业视角，而不是仅关注大公司
    print(f"使用直接搜索方法收集{topic}行业新闻...")
    all_news_data = tavily_collector.get_industry_news_direct(topic, days)
    total_news_count = all_news_data.get("total_count", 0)
    print(f"共收集到 {total_news_count} 条{topic}行业相关新闻")
    
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
    print(f"处理 {len(breaking_news)} 条重大新闻...")
    breaking_news_content = process_breaking_news(llm_processor, topic, breaking_news)
    content += breaking_news_content
    
    # 2. 处理创新新闻部分
    innovation_news = all_news_data.get("innovation_news", [])
    print(f"处理 {len(innovation_news)} 条创新新闻...")
    innovation_news_content = process_innovation_news(llm_processor, topic, innovation_news)
    content += innovation_news_content
    
    # 3. 处理投资新闻部分
    investment_news = all_news_data.get("investment_news", [])
    print(f"处理 {len(investment_news)} 条投资新闻...")
    investment_news_content = process_investment_news(llm_processor, topic, investment_news)
    content += investment_news_content
    
    # 4. 处理政策监管动态
    policy_news = all_news_data.get("policy_news", [])
    print(f"处理 {len(policy_news)} 条政策新闻...")
    policy_content = process_policy_news(llm_processor, topic, policy_news)
    content += policy_content
    
    # 5. 处理行业趋势新闻
    trend_news = all_news_data.get("trend_news", [])
    print(f"处理 {len(trend_news)} 条趋势新闻...")
    trend_content = process_industry_trends(llm_processor, topic, trend_news)
    content += trend_content
    
    # 6. 如果有公司特定新闻，生成公司动态部分
    if company_specifics:
        content += "## 重点公司动态\n\n"
        print(f"处理 {len(company_specifics)} 家公司的特定新闻...")
        
        # 为每个有新闻的公司生成小节
        for company_data in company_specifics:
            company = company_data["company"]
            news_items = company_data["news"]
            
            if news_items:
                company_summary = process_company_news(llm_processor, topic, company, news_items)
                content += company_summary + "\n\n"
    
    # 7. 最后生成趋势总结章节（对整个行业的分析）
    print("生成全面趋势总结...")
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
    
    # 确定输出文件路径
    if not output_file:
        # 如果没有提供输出文件，使用默认命名
        date_str = datetime.now().strftime('%Y%m%d')
        output_file = os.path.join(config.OUTPUT_DIR, f"{topic.replace(' ', '_').lower()}_news_report_{date_str}.md")
    elif not os.path.isabs(output_file):
        # 如果提供的是相对路径，确保正确拼接
        # 检查输出文件所在目录是否存在
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
    
    # 写入报告
    with open(output_file, 'w', encoding='utf-8-sig') as f:
        f.write(content)
    
    print(f"\n=== 行业最新动态报告生成完成 ===")
    print(f"报告已保存至: {output_file}")
    
    # 修复报告中的标题问题
    print("正在优化报告标题格式...")
    fix_markdown_headings(output_file)
    
    return output_file, {"content": content, "data": all_news_data, "date": date_str}

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