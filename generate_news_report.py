import os
import json
import argparse
from datetime import datetime, timedelta
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
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}\n来源URL: {item.get('url', '#')}"
        for item in breaking_news
    ])
    
    # 修改提示，要求LLM在输出中添加SOURCE_TAG标记作为锚点
    prompt = f"""
    请基于以下{topic}行业的最新重大新闻，提供简洁但全面的摘要，突出最重要的事件和发展。
    
    {all_news_text}
    
    请提供:
    1. 按重要性排序，每条新闻使用**加粗标题**、摘要、影响、背景的结构
    2. 每个段落结束时，最多添加一个"[SOURCE_TAG_X]"标记(X是数字，从1开始递增)，我将在后期将其替换为正确的链接
    
    要求:
    - 保持客观，专注于事实
    - 按重要性排序
    - 特别关注可能改变行业格局的突发事件
    - 长度控制在800-1000字
    - 确保每个新闻项都有清晰的**加粗标题**、摘要、影响、背景结构
    - 不要将来源信息直接嵌入文本中，源链接应单独成行
    - 每段内容最多引用一个来源，避免在一段中添加多个来源标记
    - 一个来源在一个大段落最多引用一次，不要重复引用相同的来源
    """
    
    system = f"你是一位权威的{topic}行业分析师，擅长从复杂信息中提取和总结最重要的行业事件与发展。"
    
    try:
        breaking_news_summary = llm_processor.call_llm_api(prompt, system)
        
        # 创建URL到索引的映射，确保每个URL只被替换一次
        url_indexes = {}
        current_index = 1
        
        # 替换SOURCE_TAG为实际的链接信息
        for i, news in enumerate(breaking_news, 1):
            url = news.get('url', '#')
            if url != '#':
                if url not in url_indexes:
                    url_indexes[url] = current_index
                    current_index += 1
                
                tag = f"[SOURCE_TAG_{i}]"
                source_text = f"\n来源：{url}"
                breaking_news_summary = breaking_news_summary.replace(tag, source_text)
        
        # 移除任何未被替换的标记
        import re
        breaking_news_summary = re.sub(r"\[SOURCE_TAG_\d+\]", "", breaking_news_summary)
        
        # 确保没有重复的来源链接
        processed_lines = []
        seen_urls = set()
        
        for line in breaking_news_summary.split('\n'):
            if line.startswith('来源：'):
                url = line[3:].strip()
                if url in seen_urls:
                    continue  # 跳过重复的URL
                seen_urls.add(url)
            processed_lines.append(line)
        
        breaking_news_summary = '\n'.join(processed_lines)
        
        return f"## 行业重大事件\n\n{breaking_news_summary}\n\n"
    except Exception as e:
        print(f"生成行业重大事件摘要时出错: {str(e)}")
        return f"## 行业重大事件\n\n暂无{topic}行业重大事件摘要。\n\n"

def process_innovation_news(llm_processor, topic, innovation_news):
    """处理创新新闻"""
    if not innovation_news:
        return f"## 技术创新与突破\n\n目前暂无{topic}领域的创新相关新闻。\n\n"
    
    # 提取所有创新新闻的内容
    innovation_text = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')}\n来源: {item.get('source', '未知')}\n来源URL: {item.get('url', '#')}"
        for item in innovation_news
    ])
    
    innovation_prompt = f"""
    请基于以下{topic}领域的最新创新新闻，分析总结近期在该领域的创新与技术突破。
    
    {innovation_text}
    
    请详细分析:
    1. 主要技术突破与创新点
    2. 新产品或新技术特点及优势
    3. 行业影响与应用前景
    4. 市场反应与专家评价
    
    在每个段落结束时，最多添加一个"[SOURCE_TAG_X]"标记(X是数字，从1开始递增)，我将在后期将其替换为正确的链接。
    
    要求:
    - 使用专业、客观的语言
    - 深入分析技术原理和创新点
    - 评估该创新的行业影响力和潜在变革
    - 长度控制在600-800字
    - 不要将来源信息直接嵌入文本中，源链接应单独成行
    - 每段内容最多引用一个来源，避免在一段中添加多个来源标记
    - 重要观点或子主题使用**加粗**标记
    - 一个来源在一个大段落最多引用一次，不要重复引用相同的来源
    """
    
    innovation_system = f"你是一位{topic}技术与创新专家，擅长分析新技术、新产品及其对行业的影响。"
    
    try:
        innovation_analysis = llm_processor.call_llm_api(innovation_prompt, innovation_system)
        
        # 创建URL到索引的映射，确保每个URL只被替换一次
        url_indexes = {}
        current_index = 1
        
        # 替换SOURCE_TAG为实际的链接信息
        for i, news in enumerate(innovation_news, 1):
            url = news.get('url', '#')
            if url != '#':
                if url not in url_indexes:
                    url_indexes[url] = current_index
                    current_index += 1
                
                tag = f"[SOURCE_TAG_{i}]"
                source_text = f"\n来源：{url}"
                innovation_analysis = innovation_analysis.replace(tag, source_text)
        
        # 移除任何未被替换的标记
        import re
        innovation_analysis = re.sub(r"\[SOURCE_TAG_\d+\]", "", innovation_analysis)
        
        # 确保没有重复的来源链接
        processed_lines = []
        seen_urls = set()
        
        for line in innovation_analysis.split('\n'):
            if line.startswith('来源：'):
                url = line[3:].strip()
                if url in seen_urls:
                    continue  # 跳过重复的URL
                seen_urls.add(url)
            processed_lines.append(line)
        
        innovation_analysis = '\n'.join(processed_lines)
        
        return f"## 技术创新与突破\n\n{innovation_analysis}\n\n"
    except Exception as e:
        print(f"生成创新分析时出错: {str(e)}")
        # 失败时添加基本内容
        basic_content = "\n\n".join([f"- {item.get('title', '无标题')}" for item in innovation_news])
        return f"## 技术创新与突破\n\n{basic_content}\n\n"

def process_investment_news(llm_processor, topic, investment_news):
    """处理投资新闻"""
    if not investment_news:
        return f"## 投资与融资动态\n\n目前暂无{topic}领域的投资相关新闻。\n\n"
    
    # 提取所有投资新闻的内容
    investment_text = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')}\n来源: {item.get('source', '未知')}\n来源URL: {item.get('url', '#')}"
        for item in investment_news
    ])
    
    investment_prompt = f"""
    请基于以下{topic}领域的最新投融资新闻，分析总结近期在该领域的投资与融资动态。
    
    {investment_text}
    
    请详细分析:
    1. 主要投资事件与资金规模
    2. 投资热点领域及原因
    3. 主要投资方及其投资策略
    4. 对行业发展的影响与趋势预测
    
    在每个段落结束时，最多添加一个"[SOURCE_TAG_X]"标记(X是数字，从1开始递增)，我将在后期将其替换为正确的链接。
    
    要求:
    - 使用专业、客观的语言
    - 分析投资背后的市场逻辑
    - 评估投资活动对行业格局的影响
    - 长度控制在600-800字
    - 不要将来源信息直接嵌入文本中，源链接应单独成行
    - 每段内容最多引用一个来源，避免在一段中添加多个来源标记
    - 重要观点或子主题使用**加粗**标记
    - 一个来源在一个大段落最多引用一次，不要重复引用相同的来源
    """
    
    investment_system = f"你是一位{topic}行业投资分析师，擅长分析投融资事件及其市场影响。"
    
    try:
        investment_analysis = llm_processor.call_llm_api(investment_prompt, investment_system)
        
        # 创建URL到索引的映射，确保每个URL只被替换一次
        url_indexes = {}
        current_index = 1
        
        # 替换SOURCE_TAG为实际的链接信息
        for i, news in enumerate(investment_news, 1):
            url = news.get('url', '#')
            if url != '#':
                if url not in url_indexes:
                    url_indexes[url] = current_index
                    current_index += 1
                
                tag = f"[SOURCE_TAG_{i}]"
                source_text = f"\n来源：{url}"
                investment_analysis = investment_analysis.replace(tag, source_text)
        
        # 移除任何未被替换的标记
        import re
        investment_analysis = re.sub(r"\[SOURCE_TAG_\d+\]", "", investment_analysis)
        
        # 确保没有重复的来源链接
        processed_lines = []
        seen_urls = set()
        
        for line in investment_analysis.split('\n'):
            if line.startswith('来源：'):
                url = line[3:].strip()
                if url in seen_urls:
                    continue  # 跳过重复的URL
                seen_urls.add(url)
            processed_lines.append(line)
        
        investment_analysis = '\n'.join(processed_lines)
        
        return f"## 投资与融资动态\n\n{investment_analysis}\n\n"
    except Exception as e:
        print(f"生成投资分析时出错: {str(e)}")
        # 失败时添加基本内容
        basic_content = "\n\n".join([f"- {item.get('title', '无标题')}" for item in investment_news])
        return f"## 投资与融资动态\n\n{basic_content}\n\n"

def process_industry_trends(llm_processor, topic, trend_news):
    """处理行业趋势新闻"""
    if not trend_news:
        return f"## 行业动态与趋势\n\n目前暂无{topic}领域的行业趋势相关新闻。\n\n"
    
    # 提取所有趋势新闻的内容
    trend_text = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')}\n来源: {item.get('source', '未知')}\n来源URL: {item.get('url', '#')}"
        for item in trend_news
    ])
    
    trend_prompt = f"""
    请基于以下{topic}领域的最新新闻，分析总结近期该领域的主要趋势与发展动态。
    
    {trend_text}
    
    请详细分析:
    1. 当前行业的主要发展趋势与变化
    2. 市场需求的变化与消费者行为转变
    3. 政策环境对行业的影响
    4. 行业未来发展的预测与展望
    
    在每个段落结束时，最多添加一个"[SOURCE_TAG_X]"标记(X是数字，从1开始递增)，我将在后期将其替换为正确的链接。
    
    要求:
    - 使用专业、客观的语言
    - 分析趋势背后的市场逻辑
    - 评估这些趋势对行业格局的潜在影响
    - 长度控制在600-800字
    - 不要将来源信息直接嵌入文本中，源链接应单独成行
    - 每段内容最多引用一个来源，避免在一段中添加多个来源标记
    - 重要观点或子主题使用**加粗**标记
    - 一个来源在一个大段落最多引用一次，不要重复引用相同的来源
    """
    
    trend_system = f"你是一位{topic}行业分析师，擅长解读行业趋势和市场动向。"
    
    try:
        trend_analysis = llm_processor.call_llm_api(trend_prompt, trend_system)
        
        # 创建URL到索引的映射，确保每个URL只被替换一次
        url_indexes = {}
        current_index = 1
        
        # 替换SOURCE_TAG为实际的链接信息
        for i, news in enumerate(trend_news, 1):
            url = news.get('url', '#')
            if url != '#':
                if url not in url_indexes:
                    url_indexes[url] = current_index
                    current_index += 1
                
                tag = f"[SOURCE_TAG_{i}]"
                source_text = f"\n来源：{url}"
                trend_analysis = trend_analysis.replace(tag, source_text)
        
        # 移除任何未被替换的标记
        import re
        trend_analysis = re.sub(r"\[SOURCE_TAG_\d+\]", "", trend_analysis)
        
        # 确保没有重复的来源链接
        processed_lines = []
        seen_urls = set()
        
        for line in trend_analysis.split('\n'):
            if line.startswith('来源：'):
                url = line[3:].strip()
                if url in seen_urls:
                    continue  # 跳过重复的URL
                seen_urls.add(url)
            processed_lines.append(line)
        
        trend_analysis = '\n'.join(processed_lines)
        
        return f"## 行业动态与趋势\n\n{trend_analysis}\n\n"
    except Exception as e:
        print(f"生成行业趋势分析时出错: {str(e)}")
        # 失败时添加基本内容
        basic_content = "\n\n".join([f"- {item.get('title', '无标题')}" for item in trend_news])
        return f"## 行业动态与趋势\n\n{basic_content}\n\n"

def process_company_news(llm_processor, topic, company, news_items):
    """处理公司相关新闻"""
    if not news_items:
        return f"## 企业动态: {company}\n\n目前暂无{company}的相关新闻。\n\n"
    
    # 提取所有公司新闻内容
    company_text = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')}\n来源: {item.get('source', '未知')}\n来源URL: {item.get('url', '#')}"
        for item in news_items
    ])
    
    company_prompt = f"""
    请基于以下{company}公司的最新新闻，分析总结该公司近期的重要动态与发展。
    
    {company_text}
    
    请详细分析:
    1. 公司的重要业务动态与战略调整
    2. 产品创新与技术发展
    3. 市场表现与竞争态势
    4. 公司面临的挑战与机遇
    
    在每个段落结束时，最多添加一个"[SOURCE_TAG_X]"标记(X是数字，从1开始递增)，我将在后期将其替换为正确的链接。
    
    要求:
    - 使用专业、客观的语言
    - 分析公司动态背后的战略意图
    - 评估这些发展对公司未来的潜在影响
    - 长度控制在500-700字
    - 不要将来源信息直接嵌入文本中，源链接应单独成行
    - 每段内容最多引用一个来源，避免在一段中添加多个来源标记
    - 重要观点或子主题使用**加粗**标记
    - 一个来源在一个大段落最多引用一次，不要重复引用相同的来源
    """
    
    company_system = f"你是一位专注于{topic}行业的公司分析师，擅长解读企业动态和战略发展。"
    
    try:
        company_analysis = llm_processor.call_llm_api(company_prompt, company_system)
        
        # 创建URL到索引的映射，确保每个URL只被替换一次
        url_indexes = {}
        current_index = 1
        
        # 替换SOURCE_TAG为实际的来源信息
        for i, news in enumerate(news_items, 1):
            url = news.get('url', '#')
            if url != '#':
                if url not in url_indexes:
                    url_indexes[url] = current_index
                    current_index += 1
                
                tag = f"[SOURCE_TAG_{i}]"
                source_text = f"\n来源：{url}"
                company_analysis = company_analysis.replace(tag, source_text)
        
        # 移除任何未被替换的标记
        import re
        company_analysis = re.sub(r"\[SOURCE_TAG_\d+\]", "", company_analysis)
        
        # 确保没有重复的来源链接
        processed_lines = []
        seen_urls = set()
        
        for line in company_analysis.split('\n'):
            if line.startswith('来源：'):
                url = line[3:].strip()
                if url in seen_urls:
                    continue  # 跳过重复的URL
                seen_urls.add(url)
            processed_lines.append(line)
        
        company_analysis = '\n'.join(processed_lines)
        
        return f"## 企业动态: {company}\n\n{company_analysis}\n\n"
    except Exception as e:
        print(f"生成公司新闻分析时出错: {str(e)}")
        # 失败时添加基本内容
        basic_content = "\n\n".join([f"- {item.get('title', '无标题')}" for item in news_items])
        return f"## 企业动态: {company}\n\n{basic_content}\n\n"

def process_policy_news(llm_processor, topic, policy_news):
    """处理政策新闻"""
    if not policy_news:
        return f"## 行业发展指南\n\n目前暂无{topic}领域的相关指导文件信息。\n\n"
    
    # 按发布日期对政策新闻进行排序，优先显示最新的
    from datetime import datetime, timedelta
    
    # 首先尝试从news中提取日期信息
    current_date = datetime.now()
    # 设置默认的日期范围，优先显示最近3个月的政策
    default_days_range = 90
    date_cutoff = current_date - timedelta(days=default_days_range)
    
    # 提取所有带日期的新闻
    dated_policies = []
    undated_policies = []
    
    for item in policy_news:
        # 尝试从内容中提取日期
        try:
            content = item.get('content', '')
            title = item.get('title', '')
            
            # 查找常见的日期格式，如2023年1月1日，2023-01-01等
            import re
            date_patterns = [
                r'(\d{4})年(\d{1,2})月(\d{1,2})日',  # 2023年1月1日
                r'(\d{4})-(\d{1,2})-(\d{1,2})',      # 2023-01-01
                r'(\d{4})\.(\d{1,2})\.(\d{1,2})'     # 2023.01.01
            ]
            
            found_date = None
            for pattern in date_patterns:
                matches = re.findall(pattern, content + " " + title)
                if matches:
                    # 使用找到的第一个日期
                    year, month, day = matches[0]
                    try:
                        found_date = datetime(int(year), int(month), int(day))
                        break
                    except ValueError:
                        continue
            
            if found_date:
                item['published_date'] = found_date
                dated_policies.append(item)
            else:
                undated_policies.append(item)
        except Exception as e:
            print(f"提取政策日期时出错: {str(e)}")
            undated_policies.append(item)
    
    # 对有日期的政策按日期从新到旧排序
    dated_policies.sort(key=lambda x: x.get('published_date', datetime.now()), reverse=True)
    
    # 优先选择最新的政策，显示最近发布的
    recent_policies = [p for p in dated_policies if p.get('published_date', current_date) >= date_cutoff]
    
    # 如果最近3个月的政策少于3个，则补充一些较早的政策或无日期的政策
    if len(recent_policies) < 3:
        older_policies = [p for p in dated_policies if p.get('published_date', current_date) < date_cutoff]
        recent_policies.extend(older_policies[:3-len(recent_policies)])
        
        # 如果仍然不足3个，添加无日期的政策
        if len(recent_policies) < 3 and undated_policies:
            recent_policies.extend(undated_policies[:3-len(recent_policies)])
    
    # 最终使用的政策列表，限制在5个以内
    final_policies = recent_policies[:5]
    
    print(f"从{len(policy_news)}条政策新闻中筛选出{len(final_policies)}条最新政策进行处理")
    
    # 提取所有相关新闻的内容
    policy_text = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')}\n来源: {item.get('source', '未知')}\n来源URL: {item.get('url', '#')}\n日期: {item.get('published_date', '未知日期')}"
        for item in final_policies
    ])
    
    # 完全中性的提示词，避免任何可能触发内容限制的词汇
    policy_prompt = f"""
    请基于以下提供的{topic}领域相关资讯，客观整理近期发布的文件要点：

    {policy_text}

    请仅提供以下事实性信息：
    1. 文件发布：按时间顺序列出文件名称、发布日期、发布主体
    2. 主要要点：摘录文件中提到的关键信息要点
    3. 技术指南：整理相关技术建议和行业标准内容

    整理要求：
    - 完全客观描述，只列出事实信息
    - 不进行任何评价、分析或解读
    - 使用**加粗**标记要点
    - 可在段落后添加"[TAG_X]"标记，我将替换为信息来源
    - 长度控制在600字以内
    """
    
    # 更中性的system信息
    policy_system = f"你是一位{topic}领域的资料整理专家，擅长客观摘录和整理行业文件要点，不做任何额外分析或评价。"
    
    try:
        # 错误处理和多次尝试机制
        max_retries = 3
        policy_analysis = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # 在每次重试时逐渐简化提示词
                if attempt > 0:
                    simplified_prompt = f"""
                    请基于以下{topic}领域资料，仅列出最重要的几个文件标题、发布日期和发布机构：
                    
                    {policy_text}
                    
                    要求：
                    - 只提供文件标题、发布日期和简短描述
                    - 不做任何分析或评价
                    - 完全客观，仅列出事实
                    - 每个要点不超过20字
                    """
                    policy_analysis = llm_processor.call_llm_api(simplified_prompt, policy_system)
                else:
                    policy_analysis = llm_processor.call_llm_api(policy_prompt, policy_system)
                
                if policy_analysis:
                    break
            except Exception as e:
                last_error = e
                print(f"处理文件信息时出错 (尝试 {attempt+1}/{max_retries}): {str(e)}")
        
        # 如果所有尝试都失败，创建极其简单的基本内容
        if not policy_analysis:
            if last_error:
                print(f"所有尝试均失败: {str(last_error)}")
            
            # 创建最基本的内容，仅列出标题
            policy_analysis = ""
            for item in final_policies:
                title = item.get('title', '无标题')
                date_str = ""
                if 'published_date' in item and isinstance(item['published_date'], datetime):
                    date_str = f" ({item['published_date'].strftime('%Y年%m月%d日')})"
                policy_analysis += f"**{title}{date_str}**\n\n"
                if item.get('url', '#') != '#':
                    policy_analysis += f"来源：{item.get('url')}\n\n"
        
        # 处理标记替换
        for i, news in enumerate(final_policies, 1):
            url = news.get('url', '#')
            if url != '#':
                tag = f"[TAG_{i}]"
                source_text = f"\n来源：{url}"
                policy_analysis = policy_analysis.replace(tag, source_text)
        
        # 移除任何未被替换的标记
        import re
        policy_analysis = re.sub(r"\[TAG_\d+\]", "", policy_analysis)
        
        # 去除重复的来源链接
        processed_lines = []
        seen_urls = set()
        
        for line in policy_analysis.split('\n'):
            if line.startswith('来源：'):
                url = line[3:].strip()
                if url in seen_urls:
                    continue
                seen_urls.add(url)
            processed_lines.append(line)
        
        policy_analysis = '\n'.join(processed_lines)
        
        return f"## 行业发展指南\n\n{policy_analysis}\n\n"
    except Exception as e:
        print(f"整理文件信息时出错: {str(e)}")
        # 最简单的回退机制，仅列出标题
        basic_content = ""
        for item in final_policies:
            title = item.get('title', '无标题')
            date_str = ""
            if 'published_date' in item and isinstance(item['published_date'], datetime):
                date_str = f" ({item['published_date'].strftime('%Y年%m月%d日')})"
            basic_content += f"- {title}{date_str}\n"
        return f"## 行业发展指南\n\n{basic_content}\n\n"

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
    
    # 准备新闻内容，包含来源信息
    prepared_news = []
    for item in all_relevant_news[:20]:  # 限制使用的新闻数量
        title = item.get('title', '无标题')
        content = item.get('content', '无内容')[:300]
        source = item.get('source', '未知来源')
        news_type = item.get('news_type', '其他新闻')
        
        # 将来源直接添加到内容中
        prepared_item = {
            "title": title,
            "content": content,
            "source": source,
            "original_source": source,  # 保存原始来源
            "type": "趋势新闻" if item in trend_news else news_type
        }
        prepared_news.append(prepared_item)
    
    # 提取最关键的新闻信息，区分趋势新闻和其他新闻
    key_trend_news = [item for item in prepared_news if item["type"] == "趋势新闻"]
    key_other_news = [item for item in prepared_news if item["type"] != "趋势新闻"]
    
    # 组合新闻内容
    trend_text = "\n\n".join([
        f"标题: {item['title']}\n内容: {item['content']}...\n来源: {item['source']}\n类型: {item['type']}"
        for item in key_trend_news
    ])
    
    other_text = "\n\n".join([
        f"标题: {item['title']}\n内容: {item['content']}...\n来源: {item['source']}\n类型: {item['type']}"
        for item in key_other_news
    ])
    
    news_content = trend_text
    if other_text:
        news_content += "\n\n=== 其他补充新闻 ===\n\n" + other_text
    
    summary_prompt = f"""
    请基于以下关于{topic}行业的新闻信息，撰写一份详尽的"行业趋势总结"章节，对整个行业做全面分析。
    
    {news_content}
    
    你的行业趋势总结需要：
    
    1. 开篇概述：简明扼要地概括{topic}行业的当前状态和总体发展趋势
    
    2. 分点详析：使用以下4-6个方面作为小标题，对每个方面进行深入剖析（每点至少150字）：
       - **市场格局变化**：详细分析行业中的市场结构、主要玩家和竞争态势的变化
       - **技术创新趋势**：详细分析推动行业发展的关键技术及其应用前景
       - **用户需求演变**：详细分析客户/消费者行为和需求的变化及其影响
       - **商业模式创新**：详细分析新兴的商业模式和盈利方式
       - **跨界融合发展**：详细分析该行业与其他领域的融合创新趋势
       - **政策影响分析**：详细分析监管环境变化及其影响
       
    3. 结论展望：对行业未来3-5年的发展做出有见地的预测，包括：
       - 潜在的增长点和机遇
       - 可能面临的挑战和风险
       - 关键成功因素的转变
    
    要求：
    - 所有分析都必须基于提供的新闻信息，同时结合行业知识做深入解读
    - 优先关注趋势新闻中反映的行业发展趋势
    - 每个小标题下的内容必须详尽，不能简单列点
    - 使用专业术语，但确保非专业人士也能理解
    - 引用具体事实、数据或案例支持你的观点
    - 突出行业发展的关键拐点和重大变革
    - 在每个主要观点或数据引用后，单独一行添加来源链接，格式为"来源：https://example.com"
    - 确保对不同观点或数据的来源都做清晰标注
    - 每段内容最多引用一个来源，避免在一段中引用多个来源
    - 一个来源在一个大段落最多引用一次，不要重复引用相同的来源
    - 小标题必须使用Markdown加粗格式，如**标题**
    """
    
    summary_system = f"""你是{topic}行业的顶级分析师，拥有15年以上行业经验，对行业发展有深刻理解和独特洞见。
    你的分析被业内广泛引用，因为它们深入、全面且有前瞻性，能准确把握行业趋势并预测行业未来发展方向。
    在这次任务中，你需要创作一篇高质量的行业趋势总结章节，它将成为一份完整行业报告的核心部分。
    你的分析需要详尽、有深度、有结构，能够为读者提供真正的价值和决策参考。"""
    
    try:
        trend_summary = llm_processor.call_llm_api(summary_prompt, summary_system)
        
        # 确保每个来源都正确显示
        for item in prepared_news[:10]:  # 检查主要来源
            original_source = item["original_source"]
            # 检查是否已包含该来源
            if f"（{original_source}）" not in trend_summary and f"({original_source})" not in trend_summary:
                # 如果没有包含，可以考虑添加一个注释
                print(f"警告：'{original_source}'来源可能未在趋势总结中正确引用")
        
        return f"## 行业趋势总结\n\n{trend_summary}\n"
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