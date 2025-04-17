import os
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
import logging
import re

from collectors.tavily_collector import TavilyCollector
from generators.report_generator import ReportGenerator
import config

def get_industry_news_comprehensive(topic, days=7, companies=None):
    """
    全面获取行业最新动态，包括突发新闻、创新动态、趋势和政策等
    
    Args:
        topic (str): 行业主题
        days (int): 时间范围（天数）
        companies (list): 重点公司列表（可选）
        
    Returns:
        dict: 包含各类型新闻和报告内容的字典
    """
    logging.info(f"开始收集 {topic} 行业最新动态...")
    
    # 初始化收集器和处理器
    tavily_collector = TavilyCollector()
    llm_processor = tavily_collector._get_llm_processor() or None
    
    # 使用直接搜索行业新闻的方法
    try:
        logging.info("使用直接行业新闻搜索方法...")
        industry_news_result = tavily_collector.get_industry_news_direct(topic, days=days)
        
        breaking_news = industry_news_result.get("breaking_news", [])
        innovation_news = industry_news_result.get("innovation_news", [])
        trend_news = industry_news_result.get("trend_news", [])
        policy_news = industry_news_result.get("policy_news", [])
        investment_news = industry_news_result.get("investment_news", [])
        
        logging.info(f"收集到 {len(breaking_news)} 条突发新闻，{len(innovation_news)} 条创新新闻，"
                    f"{len(trend_news)} 条趋势新闻，{len(policy_news)} 条政策新闻，"
                    f"{len(investment_news)} 条投资新闻")
    except Exception as e:
        logging.error(f"直接搜索行业新闻失败: {str(e)}")
        breaking_news = []
        innovation_news = []
        trend_news = []
        policy_news = []
        investment_news = []

    # 如果提供了公司列表，则获取特定公司的新闻
    company_news_sections = []
    if companies:
        logging.info(f"开始获取 {len(companies)} 个特定公司的新闻...")
        for company in companies:
            try:
                company_news = tavily_collector.get_company_news(company, topic, days)
                if company_news:
                    logging.info(f"为 {company} 收集到 {len(company_news)} 条新闻")
                    company_section = process_company_news(llm_processor, company, topic, company_news)
                    company_news_sections.append(company_section)
            except Exception as e:
                logging.error(f"获取 {company} 公司新闻失败: {str(e)}")
    
    # 如果没有直接搜索到足够的行业新闻，尝试使用备用方法
    if (len(breaking_news) + len(innovation_news) + len(trend_news) + 
        len(policy_news) + len(investment_news)) < 5:
        logging.warning("直接搜索未获取到足够的行业新闻，尝试使用备用方法...")
        try:
            # 这里可以保留原来的搜索方法作为备用
            pass
        except Exception as backup_e:
            logging.error(f"备用搜索方法也失败: {str(backup_e)}")

    # 生成报告内容
    title = f"# {topic}行业最新动态报告\n\n"
    date_info = f"报告生成日期: {datetime.now().strftime('%Y-%m-%d')}\n\n"
    
    # 处理各类新闻
    breaking_news_section = process_breaking_news(llm_processor, topic, breaking_news)
    innovation_news_section = process_innovation_news(llm_processor, topic, innovation_news)
    investment_news_section = process_investment_news(llm_processor, topic, investment_news)
    policy_news_section = process_policy_news(llm_processor, topic, policy_news)
    
    # 如果直接收集到行业趋势新闻，使用它们生成趋势部分
    all_news_data = {
        "breaking_news": breaking_news,
        "innovation_news": innovation_news,
        "trend_news": trend_news,
        "policy_news": policy_news,
        "investment_news": investment_news
    }
    
    # 生成行业趋势总结
    trend_summary_section = generate_comprehensive_trend_summary(
        llm_processor, 
        topic, 
        all_news_data
    )
    
    # 添加公司部分（如果有）
    companies_section = ""
    if company_news_sections:
        companies_section = "## 重点公司动态\n\n" + "\n\n".join(company_news_sections) + "\n\n"
    
    # 组合所有部分
    content_sections = [
        title,
        date_info,
        breaking_news_section,
        innovation_news_section,
        investment_news_section,
        policy_news_section,
        companies_section if companies_section else "",
        trend_summary_section,
        "## 参考来源\n\n"
    ]
    
    # 添加参考来源
    all_news = (breaking_news + innovation_news + trend_news + 
               policy_news + investment_news)
    
    # 去重参考来源
    reference_urls = {}
    for item in all_news:
        url = item.get('url')
        if url and url not in reference_urls:
            title = item.get('title', 'Unknown Title')
            source = item.get('source', 'Unknown Source')
            reference_urls[url] = f"- [{title}]({url}) - {source}"
    
    references = "\n".join(list(reference_urls.values()))
    content_sections.append(references)
    
    # 合并内容
    content = "\n".join([section for section in content_sections if section])
    
    return {
        "content": content,
        "breaking_news": breaking_news,
        "innovation_news": innovation_news,
        "trend_news": trend_news,
        "policy_news": policy_news,
        "investment_news": investment_news
    }

def process_breaking_news(llm_processor, topic, breaking_news):
    """处理行业重大新闻"""
    if not breaking_news:
        return f"## 行业重大事件\n\n目前暂无{topic}行业的重大新闻。\n\n"
    
    # 获取当前年份
    current_year = datetime.now().year
    
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
    
    重要提示:
    - 这些内容必须反映{current_year}年的最新情况，不要包含过时信息
    - 保持客观，专注于事实
    - 按重要性排序
    - 特别关注可能改变行业格局的突发事件
    - 长度控制在800-1000字
    """
    
    system = f"""你是一位权威的{topic}行业分析师，擅长从复杂信息中提取和总结最重要的行业事件与发展。
    你的任务是分析{current_year}年的最新行业动态，不要使用或提及旧年份(如2023年)的信息作为当前动态。
    确保所有分析都基于最新数据，并明确标明这是{current_year}年的行业情况。"""
    
    try:
        breaking_news_summary = llm_processor.call_llm_api(prompt, system)
        return f"## {current_year}年{topic}行业重大事件\n\n{breaking_news_summary}\n\n"
    except Exception as e:
        print(f"生成行业重大事件摘要时出错: {str(e)}")
        return f"## {topic}行业重大事件\n\n暂无{topic}行业重大事件摘要。\n\n"

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
    请基于以下{topic}行业的最新新闻，分析并总结行业整体趋势和发展方向。
    
    {all_news_text}
    
    请提供详细的行业趋势分析报告，内容需要包括但不限于：
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
    - 长度要充分，至少1500-2000字
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

def process_company_news(llm_processor, company, topic, news_items):
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
    
    # 获取当前年份
    current_year = datetime.now().year
    
    # 整合所有类型的新闻以提供全面视角
    all_relevant_news = []
    for category in ["breaking_news", "innovation_news", "trend_news", "policy_news", "investment_news"]:
        all_relevant_news.extend(all_news_data.get(category, []))
    
    # 如果没有足够的新闻数据，返回简单提示
    if len(all_relevant_news) < 3:
        return f"## {current_year}年{topic}行业趋势总结\n\n目前收集到的{topic}行业数据不足，无法生成全面的趋势总结。\n\n"
    
    # 提取最关键的新闻信息
    key_news = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:300]}...\n来源: {item.get('source', '未知')}\n类型: {item.get('news_type', '未知类型')}"
        for item in all_relevant_news[:15]  # 最多使用15条最相关的新闻
    ])
    
    summary_prompt = f"""
    请基于以下关于{topic}行业的综合信息，撰写一份详尽的"{current_year}年{topic}行业趋势总结"章节，对整个行业做全面分析。
    
    {key_news}
    
    你的行业趋势总结需要：
    
    1. 开篇概述：简明扼要地概括{current_year}年{topic}行业的当前状态和总体发展趋势
    
    2. 分点详析：使用以下4-6个方面作为小标题，对每个方面进行深入剖析（每点至少200字）：
       - 行业发展新方向：详细分析{current_year}年{topic}行业出现的新趋势和方向
       - 创新与技术进步：详细分析{current_year}年{topic}行业的技术创新和突破
       - 政策环境变化：详细分析{current_year}年影响{topic}行业的新政策和监管变化
       - 市场竞争格局：详细分析{current_year}年{topic}行业主要参与者和竞争态势
       - 其他你认为重要的行业趋势（如适用）
    
    3. 结论展望：对行业未来发展做出有见地的预测
    
    要求：
    - 所有分析都必须明确表示这是{current_year}年的最新情况，不要引用或呈现旧年份(如2023年)的数据作为当前情况
    - 所有分析都必须基于提供的新闻信息，同时结合行业知识做深入解读
    - 每个小标题下的内容必须详尽，不能简单列点
    - 使用专业术语，但确保非专业人士也能理解
    - 引用具体事实、数据或案例支持你的分析
    - 突出行业发展的关键拐点和重大变革
    - 总体篇幅不少于1500字
    """
    
    summary_system = f"""你是{topic}行业的顶级分析师，拥有深入的行业经验和洞察力。
    你的任务是分析{current_year}年的最新行业动态，不要使用过时信息，特别是不要将旧年份(如2023年)的信息作为当前动态。
    确保所有分析都基于最新数据，并明确标明这是{current_year}年的行业情况。
    你的分析需要详尽、有深度、有结构，能够为读者提供真正的价值。"""
    
    try:
        trend_summary = llm_processor.call_llm_api(summary_prompt, summary_system)
        return f"## {current_year}年{topic}行业趋势总结\n\n{trend_summary}\n\n"
    except Exception as e:
        print(f"生成行业趋势总结时出错: {str(e)}")
        fallback_summary = f"无法生成{current_year}年{topic}行业趋势详细总结，请查看报告其他部分获取相关信息。"
        return f"## {current_year}年{topic}行业趋势总结\n\n{fallback_summary}\n\n"

def refine_report_content(content, llm_processor):
    """
    对生成的报告内容进行适度精炼，确保报告简洁有力但保留所有关键内容
    
    Args:
        content: 原始报告内容
        llm_processor: LLM处理器实例
    
    Returns:
        精炼后的报告内容
    """
    logging.info("开始对报告内容进行精炼...")
    
    # 确保内容不为空
    if not content or len(content) < 100:
        logging.warning("报告内容过短，跳过精炼过程")
        return content
    
    # 先保存报告原始长度和关键部分位置
    original_length = len(content)
    
    # 提取参考来源部分，避免在精炼过程中丢失
    references_section = ""
    if "## 参考来源" in content:
        main_content = content.split("## 参考来源")[0]
        references_section = "## 参考来源" + content.split("## 参考来源")[1]
    else:
        main_content = content
    
    # 获取当前年份
    current_year = datetime.now().year
    
    prompt = f"""
    作为一名专业的报告编辑，请对以下行业报告内容进行适度精炼，遵循以下要求：
    
    1. 删除重复或表达相似的内容，确保每个要点只出现一次
    2. 保持所有关键信息和数据，使整体篇幅更紧凑，但内容减少不应超过20%
    3. 确保各部分之间逻辑连贯，避免不必要的交叉引用
    4. 保留报告的完整结构和所有章节标题
    5. 确保保留所有数据点和关键洞察
    6. 确保报告语言专业、简洁、明了
    7. 确保所有内容都反映{current_year}年的最新情况
    
    原始报告内容：
    {main_content}
    
    请直接返回精炼后的完整报告内容，不需要额外说明。
    """
    
    system_message = f"""
    你是一名专业的行业报告编辑，擅长精简内容并保持关键信息。
    你的任务是适度精炼报告，删除冗余但保留所有重要内容。
    不要过度删减内容，确保精炼后的报告仍然包含全面的行业分析。
    确保所有内容都反映{current_year}年的最新情况，不要将旧年份的信息呈现为当前状况。
    直接返回精炼后的报告内容，不要添加任何解释或元描述。
    """
    
    try:
        refined_content = llm_processor.call_llm_api(
            prompt=prompt,
            system_message=system_message,
            temperature=0.1,  # 降低温度以获得更可预测的输出
            max_tokens=4000
        )
        
        # 如果精炼后的内容少于原始内容的50%，可能说明内容被过度精简
        if len(refined_content) < original_length * 0.5:
            logging.warning(f"精炼过程可能过度删减内容: 原始长度 {original_length}，精炼后长度 {len(refined_content)}")
            logging.info("使用原始内容")
            refined_main_content = main_content
        else:
            refined_main_content = refined_content
        
        # 重新添加参考来源部分
        final_content = refined_main_content + "\n\n" + references_section if references_section else refined_main_content
        
        logging.info(f"报告内容精炼完成: 原始长度 {original_length}，精炼后长度 {len(final_content)}")
        return final_content
    except Exception as e:
        logging.error(f"报告精炼过程出错: {str(e)}")
        # 如果精炼失败，返回原始内容
        return content

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
    # 设置日志级别
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 获取当前年份
    current_year = datetime.now().year
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # 确保输出目录存在
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    logging.info(f"开始生成{current_year}年{topic}行业最新动态报告")
    logging.info(f"搜索范围: 过去{days}天的相关新闻")
    
    # 获取并处理新闻数据，使用全面的行业动态收集方法
    news_data = get_industry_news_comprehensive(topic, days, companies)
    
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
    
    # 替换标题和日期信息，确保使用当前年份
    if "content" in news_data:
        # 替换标题中可能的旧年份
        title_pattern = r"# (.+?)行业最新动态"
        if re.search(title_pattern, news_data["content"]):
            updated_title = f"# {current_year}年{topic}行业最新动态报告"
            news_data["content"] = re.sub(title_pattern, updated_title, news_data["content"])
        
        # 更新报告日期
        date_pattern = r"报告生成日期: \d{4}-\d{2}-\d{2}"
        if re.search(date_pattern, news_data["content"]):
            news_data["content"] = re.sub(date_pattern, f"报告生成日期: {current_date}", news_data["content"])
    
    # 写入报告
    with open(output_file, 'w', encoding='utf-8-sig') as f:
        f.write(news_data["content"])
    
    logging.info(f"报告初稿已保存至: {output_file}")
    
    # 获取LLM处理器
    tavily_collector = TavilyCollector()
    llm_processor = tavily_collector._get_llm_processor()
    
    if llm_processor:
        logging.info("开始对报告内容进行精炼...")
        try:
            # 对报告内容进行精炼
            refined_content = refine_report_content(news_data["content"], llm_processor)
            
            # 确保精炼内容不为空且包含关键部分
            if refined_content and "## 参考来源" in refined_content:
                # 使用精炼后的内容覆盖原文件
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(refined_content)
                
                logging.info("报告内容精炼完成")
                # 更新返回的内容
                news_data["content"] = refined_content
            else:
                logging.warning("精炼后内容质量不佳，将使用原始报告内容")
        except Exception as e:
            logging.error(f"报告精炼过程出错: {str(e)}")
            logging.info("将使用原始报告内容")
    else:
        logging.warning("无法获取LLM处理器，将使用原始报告内容")
    
    print(f"\n=== {current_year}年{topic}行业最新动态报告生成完成 ===")
    print(f"报告已保存至: {output_file}")
    
    return output_file, news_data

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
    
    args = parser.parse_args()
    
    # 生成报告
    generate_news_report(args.topic, args.companies, args.days, args.output) 