import os
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
import sys
from fix_md_headings import fix_markdown_headings

from collectors.market_research_collector import MarketResearchCollector
from collectors.tavily_collector import TavilyCollector
from collectors.news_collector import NewsCollector
from generators.report_generator import ReportGenerator
import config

def generate_comprehensive_market_report(topic, include_financial_data=True, include_forecasts=True, days=30):
    """
    生成综合市场研究报告
    
    Args:
        topic (str): 市场主题
        include_financial_data (bool): 是否包含财务数据
        include_forecasts (bool): 是否包含预测数据
        days (int): 新闻数据的时间范围
        
    Returns:
        dict: 完整的市场报告数据
    """
    print(f"\n=== 开始生成{topic}市场研究报告 ===")
    
    # 初始化数据收集器
    market_collector = MarketResearchCollector()
    tavily_collector = TavilyCollector()
    news_collector = NewsCollector()
    llm_processor = tavily_collector._get_llm_processor()
    
    # 1. 收集市场研究数据
    print("\n=== 第一阶段：收集市场研究数据 ===")
    market_data = market_collector.get_market_data(
        topic=topic,
        data_types=['market_size', 'growth_rate', 'forecast', 'trends'],
        regions=['global', 'north_america', 'asia_pacific', 'europe']
    )
    
    # 2. 收集最新行业新闻
    print("\n=== 第二阶段：收集行业新闻 ===")
    industry_news = []
    
    try:
        # 使用Tavily收集深度行业新闻
        news_data = tavily_collector.get_industry_news_direct(topic, days)
        if news_data:
            industry_news.extend(news_data.get('market_news', []))
            industry_news.extend(news_data.get('investment_news', []))
            industry_news.extend(news_data.get('innovation_news', []))
    except Exception as e:
        print(f"Tavily新闻收集出错: {str(e)}")
    
    try:
        # 使用RSS新闻收集器作为补充
        rss_news = news_collector.search_news_api(f"{topic} market industry", days_back=days)
        if rss_news:
            industry_news.extend(rss_news[:10])  # 限制RSS新闻数量
    except Exception as e:
        print(f"RSS新闻收集出错: {str(e)}")
    
    # 3. 收集公司财务数据（如果启用）
    print("\n=== 第三阶段：收集公司数据 ===")
    company_analysis = []
    if include_financial_data:
        try:
            # 获取相关公司列表
            relevant_companies = market_collector._identify_relevant_companies(topic)
            for company in relevant_companies[:5]:  # 限制前5家公司
                company_data = market_collector._get_company_financial_highlights(company, topic)
                if company_data:
                    company_analysis.append(company_data)
        except Exception as e:
            print(f"公司数据收集出错: {str(e)}")
    
    # 4. 使用LLM处理和分析数据
    print("\n=== 第四阶段：数据分析和报告生成 ===")
    
    # 生成市场概览
    market_overview = generate_market_overview(llm_processor, topic, market_data, industry_news)
    
    # 生成投资分析
    investment_analysis = generate_investment_analysis(llm_processor, topic, market_data, industry_news)
    
    # 生成技术趋势分析
    tech_trends = generate_technology_trends(llm_processor, topic, industry_news)
    
    # 生成竞争格局分析
    competitive_landscape = generate_competitive_analysis(llm_processor, topic, company_analysis, market_data)
    
    # 生成预测和展望
    market_forecast = ""
    if include_forecasts:
        market_forecast = generate_market_forecast(llm_processor, topic, market_data, industry_news)
    
    # 5. 组装完整报告
    report_content = assemble_market_report(
        topic=topic,
        market_overview=market_overview,
        investment_analysis=investment_analysis,
        tech_trends=tech_trends,
        competitive_landscape=competitive_landscape,
        market_forecast=market_forecast,
        market_data=market_data,
        company_analysis=company_analysis,
        industry_news=industry_news
    )
    
    return {
        'content': report_content,
        'market_data': market_data,
        'company_analysis': company_analysis,
        'industry_news': industry_news,
        'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def generate_market_overview(llm_processor, topic, market_data, industry_news):
    """生成市场概览部分"""
    
    # 准备市场数据摘要
    data_summary = market_data.get('data_summary', {})
    market_size_info = ""
    growth_rate_info = ""
    
    if data_summary.get('market_size_estimates'):
        sizes = [est['value'] for est in data_summary['market_size_estimates'][:3]]
        sources = [est['source'] for est in data_summary['market_size_estimates'][:3]]
        market_size_info = f"市场规模估计：{', '.join(sizes)} (来源：{', '.join(sources)})"
    
    if data_summary.get('growth_rate_estimates'):
        rates = [est['rate'] for est in data_summary['growth_rate_estimates'][:3]]
        growth_rate_info = f"增长率预测：{', '.join(rates)}"
    
    # 准备最新新闻摘要
    recent_news = ""
    if industry_news:
        news_titles = [news.get('title', '无标题') for news in industry_news[:5]]
        recent_news = "最近行业动态包括：" + "；".join(news_titles)
    
    prompt = f"""
    请基于以下信息，生成{topic}市场的专业概览分析：
    
    市场数据信息：
    {market_size_info}
    {growth_rate_info}
    
    最新行业动态：
    {recent_news}
    
    数据质量说明：
    {'; '.join(data_summary.get('data_quality_notes', []))}
    
    数据冲突提示：
    {'; '.join(data_summary.get('data_conflicts', []))}
    
    请提供：
    1. 市场现状概述，包括规模和发展阶段
    2. 主要增长驱动因素分析
    3. 市场特征和发展趋势
    4. 数据来源的可靠性说明
    5. 值得关注的市场动态
    
    要求：
    - 保持客观专业的分析语调
    - 明确指出数据的限制性和不确定性
    - 长度控制在800-1000字
    - 使用中文撰写
    """
    
    system = f"""你是一位专业的{topic}行业市场分析师，具有丰富的市场研究经验。
你擅长从多个数据源中提取关键信息，并进行客观、平衡的分析。
你的分析应该帮助读者理解市场的真实状况，包括其不确定性和数据限制。"""
    
    try:
        return llm_processor.call_llm_api(prompt, system)
    except Exception as e:
        print(f"生成市场概览时出错: {str(e)}")
        return f"市场概览生成失败，请参考原始数据：{market_size_info} {growth_rate_info}"

def generate_investment_analysis(llm_processor, topic, market_data, industry_news):
    """生成投资分析部分"""
    
    # 提取投资相关新闻
    investment_news = [news for news in industry_news if any(keyword in news.get('title', '').lower() 
                      for keyword in ['investment', 'funding', 'venture', 'ipo', 'acquisition', '投资', '融资', '并购'])]
    
    investment_info = ""
    if investment_news:
        for news in investment_news[:5]:
            investment_info += f"- {news.get('title', '无标题')}: {news.get('content', '无内容')[:200]}...\n"
    
    # 公司财务数据
    company_reports = [r for r in market_data.get('detailed_reports', []) if r.get('type') == 'company_financial']
    company_info = ""
    if company_reports:
        for report in company_reports[:5]:
            company_info += f"- {report.get('company', '未知')}: 市值 {report.get('market_cap', 'N/A')}, 营收 {report.get('revenue', 'N/A')}\n"
    
    prompt = f"""
    请基于以下信息，对{topic}市场的投资环境和机会进行深度分析。要求分析内容全面、深入、专业，并注重多维度的对比和论证。

    === 最新投资动态 ===
    {investment_info if investment_info else "暂无具体投资新闻数据"}
    
    === 主要公司财务表现 ===
    {company_info if company_info else "暂无详细公司财务数据"}
    
    === 市场增长数据 ===
    {market_data.get('data_summary', {}).get('growth_rate_estimates', [])}
    
    请按以下框架进行详细分析：

    1. 核心事件分析（占比25%）
    - 对每个重大投融资事件进行深入解读
    - 分析投资方的战略意图和布局
    - 评估投资事件对行业格局的影响
    - 对比不同投资事件的特点和趋势

    2. 估值分析（占比20%）
    - 细分各类公司的估值水平和依据
    - 横向对比同类公司估值差异
    - 分析估值溢价/折价的原因
    - 评估当前估值的合理性

    3. 细分领域投资热度（占比20%）
    - 识别最受资本关注的细分赛道
    - 分析各细分领域的投资规模和频次
    - 对比不同细分领域的投资回报预期
    - 预测下一阶段的投资热点转移

    4. 投资风险分析（占比15%）
    - 系统性风险评估（政策、市场、技术等）
    - 企业特定风险分析
    - 潜在的风险对冲策略
    - 风险与收益的平衡建议

    5. 投资建议与展望（占比20%）
    - 短期投资机会（6个月内）
    - 中长期布局建议（1-3年）
    - 细分领域的差异化投资策略
    - 具体的投资时机和方式建议

    要求：
    1. 内容深度：深入分析底层逻辑，不停留于表面现象
    2. 数据支撑：尽可能使用具体数据和案例支持观点
    3. 多维对比：注重横向和纵向的对比分析
    4. 实用性：提供可操作的具体建议
    5. 预测性：对未来趋势做出合理预测
    6. 专业性：使用专业的分析框架和术语
    7. 客观性：保持中立的分析视角，全面呈现不同观点
    8. 长度要求：1500-2000字，确保内容充实且结构清晰

    注意：
    - 如果某些数据缺失，请基于已有信息进行合理推断
    - 对于重要观点，需要提供支持论据
    - 结论要有前瞻性，但也要保持谨慎
    - 建议要具体可行，避免过于宏观和笼统
    """
    
    system = f"""你是一位专注于{topic}行业的资深投资分析师，拥有丰富的行业研究和投资分析经验。
你的分析需要：
1. 展现深厚的专业功底和对行业的深入理解
2. 善于发现投资机会背后的深层逻辑
3. 能够从多个维度进行对比分析
4. 对市场趋势有敏锐的判断
5. 在保持专业性的同时，注重分析的可读性和实用性"""
    
    try:
        investment_summary = llm_processor.call_llm_api(prompt, system, max_tokens=8000)
        
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
            investment_summary += "\n\n**参考来源:**\n" + "\n".join(news_sources)
            
        return f"## 投资与市场动向分析\n\n{investment_summary}\n\n"
    except Exception as e:
        print(f"生成投资分析摘要时出错: {str(e)}")
        return f"## 投资与市场动向分析\n\n暂无{topic}行业投资分析摘要。\n\n"

def generate_technology_trends(llm_processor, topic, industry_news):
    """生成技术趋势分析"""
    
    # 提取技术相关新闻
    tech_news = [news for news in industry_news if any(keyword in news.get('title', '').lower() 
                for keyword in ['technology', 'innovation', 'breakthrough', 'development', '技术', '创新', '突破', '发展'])]
    
    tech_info = ""
    if tech_news:
        for news in tech_news[:5]:
            tech_info += f"- {news.get('title', '无标题')}: {news.get('content', '无内容')[:300]}...\n"
    
    prompt = f"""
    请基于以下技术相关信息，分析{topic}领域的技术发展趋势：
    
    最新技术动态：
    {tech_info if tech_info else "暂无具体技术新闻数据"}
    
    请分析：
    1. 当前主要技术发展方向
    2. 突破性技术和创新点
    3. 技术成熟度和商业化进程
    4. 未来技术演进路径
    5. 技术壁垒和挑战
    
    要求：
    - 关注技术的实际应用价值
    - 分析技术发展对市场的影响
    - 识别技术趋势的可信度
    - 长度控制在600-800字
    - 使用中文撰写
    """
    
    system = f"""你是一位{topic}领域的技术分析专家，对行业技术发展有深入理解。
你能够从技术新闻和发展动态中识别重要趋势，并评估其商业价值和市场影响。"""
    
    try:
        return llm_processor.call_llm_api(prompt, system)
    except Exception as e:
        print(f"生成技术趋势分析时出错: {str(e)}")
        return "技术趋势分析生成失败，建议关注行业技术报告和专利申请动态。"

def generate_competitive_analysis(llm_processor, topic, company_analysis, market_data):
    """生成竞争格局分析"""
    
    # 准备公司数据
    company_info = ""
    if company_analysis:
        for company in company_analysis:
            company_info += f"- {company.get('company', '未知公司')}: "
            if company.get('market_cap'):
                company_info += f"市值 {company['market_cap']}, "
            if company.get('revenue'):
                company_info += f"营收 {company['revenue']}, "
            company_info += f"来源: {company.get('source', 'N/A')}\n"
    
    # 市场集中度信息
    market_structure = ""
    data_sources = market_data.get('data_sources', [])
    if data_sources:
        market_structure = f"数据来源包括：{', '.join([s.get('name', 'unknown') for s in data_sources[:5]])}"
    
    prompt = f"""
    请基于以下信息，分析{topic}市场的竞争格局：
    
    主要市场参与者财务数据：
    {company_info if company_info else "暂无详细公司财务数据"}
    
    市场研究数据来源：
    {market_structure}
    
    请分析：
    1. 市场领导者和主要参与者
    2. 市场集中度和竞争强度
    3. 主要竞争优势和差异化策略
    4. 新进入者和潜在威胁
    5. 竞争格局的发展趋势
    
    要求：
    - 基于可获得的财务数据进行分析
    - 客观评估各参与者的市场地位
    - 识别竞争的关键因素
    - 长度控制在600-800字
    - 使用中文撰写
    """
    
    system = f"""你是一位专业的{topic}行业竞争分析师，擅长从财务数据和市场信息中分析竞争格局。
你能够客观评估不同参与者的竞争优势，并预测竞争格局的发展趋势。"""
    
    try:
        return llm_processor.call_llm_api(prompt, system)
    except Exception as e:
        print(f"生成竞争分析时出错: {str(e)}")
        return "竞争格局分析生成失败，建议参考公司年报和行业分析报告。"

def generate_market_forecast(llm_processor, topic, market_data, industry_news):
    """生成市场预测和展望"""
    
    # 提取预测相关数据
    forecast_data = ""
    data_summary = market_data.get('data_summary', {})
    
    if data_summary.get('market_size_estimates'):
        forecast_data += "市场规模预测数据："
        for est in data_summary['market_size_estimates'][:3]:
            forecast_data += f"{est['value']} ({est['source']}); "
    
    if data_summary.get('growth_rate_estimates'):
        forecast_data += "\n增长率预测："
        for est in data_summary['growth_rate_estimates'][:3]:
            forecast_data += f"{est['rate']} ({est['source']}); "
    
    # 关键趋势
    key_trends = "; ".join(data_summary.get('key_trends', [])[:5])
    
    prompt = f"""
    请基于以下信息，对{topic}市场进行未来展望和预测：
    
    当前预测数据：
    {forecast_data}
    
    关键市场趋势：
    {key_trends if key_trends else "暂无具体趋势数据"}
    
    数据限制说明：
    {'; '.join(data_summary.get('data_quality_notes', []))}
    
    请提供：
    1. 短期市场预测（1-2年）
    2. 中长期发展展望（3-5年）
    3. 影响市场发展的关键因素
    4. 潜在的风险和不确定性
    5. 对投资者和企业的建议
    
    要求：
    - 明确说明预测的依据和限制
    - 提供不同情景下的可能发展路径
    - 保持预测的客观性和审慎性
    - 长度控制在800-1000字
    - 使用中文撰写
    """
    
    system = f"""你是一位{topic}行业的市场预测专家，具有丰富的行业研究经验。
你擅长基于现有数据进行合理的市场预测，同时清楚地说明预测的不确定性和风险。
你的预测应该平衡乐观与谨慎，为读者提供有价值的参考。"""
    
    try:
        return llm_processor.call_llm_api(prompt, system)
    except Exception as e:
        print(f"生成市场预测时出错: {str(e)}")
        return "市场预测生成失败，建议参考多个权威研究机构的预测报告。"

def assemble_market_report(topic, market_overview, investment_analysis, tech_trends, 
                          competitive_landscape, market_forecast, market_data, 
                          company_analysis, industry_news):
    """组装完整的市场报告 - 专门针对市场研究的结构化报告"""
    
    current_date = datetime.now().strftime('%Y年%m月%d日')
    
    # 市场研究报告专用结构
    report_content = f"""# {topic}市场研究报告

**报告日期**: {current_date}  
**报告类型**: 市场研究分析报告  
**数据来源**: 多个市场研究机构、公司财报、行业新闻

---

## 核心发现

本报告通过多维度数据分析，为{topic}市场提供全面的商业洞察和投资指导。

### 市场规模与增长

{market_overview}

### 投资机会与风险评估

{investment_analysis}

### 技术创新驱动因素

{tech_trends}

### 市场竞争态势

{competitive_landscape}

### 未来发展预测

{market_forecast}

## 研究方法与数据说明

### 数据来源
"""
    
    # 添加数据来源信息
    sources_info = market_data.get('data_sources', [])
    if sources_info:
        report_content += "\n**市场研究数据来源：**\n"
        for source in sources_info[:10]:  # 限制显示前10个来源
            report_content += f"- {source.get('name', 'unknown')}: {source.get('access_level', 'unknown')}\n"
    
    if company_analysis:
        report_content += "\n**公司财务数据来源：**\n"
        for company in company_analysis[:5]:
            report_content += f"- {company.get('company', 'unknown')}: {company.get('source', 'unknown')}\n"
    
    if industry_news:
        report_content += f"\n**行业新闻来源：** 收集了{len(industry_news)}条相关新闻\n"
    
    # 添加数据质量说明
    data_summary = market_data.get('data_summary', {})
    if data_summary.get('data_quality_notes'):
        report_content += "\n### 数据质量说明\n"
        for note in data_summary['data_quality_notes']:
            report_content += f"- {note}\n"
    
    if data_summary.get('data_conflicts'):
        report_content += "\n### 数据一致性提示\n"
        for conflict in data_summary['data_conflicts']:
            report_content += f"- ⚠️ {conflict}\n"
    
    # 添加免责声明
    report_content += """
## 免责声明

1. 本报告基于公开可获得的数据和免费摘要信息
2. 部分市场数据可能不完整，建议结合付费专业报告进行验证
3. 市场预测具有不确定性，仅供参考，不构成投资建议
4. 投资有风险，决策需谨慎
5. 数据收集时间可能存在滞后，最新情况请参考实时信息

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**数据收集方法**: 网络爬虫 + 公开API + 财报分析
"""
    
    return report_content

def main():
    """主函数"""
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='生成市场研究报告')
    parser.add_argument('--topic', help='市场主题')
    parser.add_argument('--days', type=int, default=30, help='新闻数据时间范围（天）')
    parser.add_argument('--no-financial', action='store_true', help='不包含财务数据')
    parser.add_argument('--no-forecast', action='store_true', help='不包含预测数据')
    parser.add_argument('--output', '-o', help='输出文件名')
    
    args = parser.parse_args()
    
    try:
        # 生成报告
        report_data = generate_comprehensive_market_report(
            topic=args.topic,
            include_financial_data=not args.no_financial,
            include_forecasts=not args.no_forecast,
            days=args.days
        )
        
        # 保存报告
        output_filename = args.output or f"{args.topic.replace(' ', '_')}_market_report_{datetime.now().strftime('%Y%m%d')}.md"
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(report_data['content'])
        
        print(f"\n✅ 市场报告已生成: {output_filename}")
        print(f"📊 收集的数据源: {len(report_data['market_data'].get('detailed_reports', []))}")
        print(f"🏢 分析的公司: {len(report_data['company_analysis'])}")
        print(f"📰 相关新闻: {len(report_data['industry_news'])}")
        
        # 修复markdown标题层级
        try:
            fix_markdown_headings(output_filename)
            print(f"✅ Markdown格式已优化")
        except Exception as e:
            print(f"⚠️ Markdown格式优化失败: {str(e)}")
        
    except Exception as e:
        print(f"❌ 报告生成失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()