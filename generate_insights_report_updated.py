import os
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
import sys
from fix_md_headings import fix_markdown_headings

from collectors.tavily_collector import TavilyCollector
from collectors.news_collector import NewsCollector
from generators.report_generator import ReportGenerator
from collectors.llm_processor import LLMProcessor
import config

def generate_industry_insights_without_api(topic, subtopics=None):
    """
    在没有API密钥的情况下生成行业洞察
    使用优化后的行业洞察报告结构
    """
    # 优化后的行业洞察报告结构
    insights_sections = {
        f"{topic}行业定义与核心特点": f"本节将介绍{topic}的行业边界、技术特征和核心价值主张。",
        f"{topic}发展历程与阶段演进": f"分析{topic}的关键发展阶段、技术里程碑和演进路径。",
        f"{topic}产业链与价值分布": f"探讨{topic}的上中下游结构及各环节价值占比分析。",
        f"{topic}市场格局与参与者": f"研究{topic}市场的竞争格局、市场份额和代表性企业。",
        f"{topic}核心驱动与趋势": f"分析推动{topic}发展的内外部因素及主要趋势预测。",
        f"{topic}未来展望与挑战应对": f"预测{topic}的技术突破点、潜在挑战及解决方案，并提出战略建议。",
        f"{topic}政策环境分析": f"对比全球和区域{topic}相关政策，分析监管趋势及影响。"
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

def evaluate_insights_relevance(raw_insights, topic, llm_processor=None):
    """
    评估原始洞察内容与主题的相关性，并进行筛选和排序
    
    Args:
        raw_insights (list): 原始洞察数据列表
        topic (str): 主题
        llm_processor: LLM处理器实例，用于高级评分
        
    Returns:
        list: 筛选并排序后的洞察数据
    """
    if not raw_insights or not llm_processor:
        return raw_insights
    
    print(f"正在评估{len(raw_insights)}条原始洞察数据与'{topic}'的相关性...")
    
    # 评估标准
    criteria = {
        "主题相关性": 0.5,   # 内容与主题的直接相关性
        "信息质量": 0.3,     # 内容的完整性、深度和信息量
        "时效性": 0.1,       # 内容的新鲜度
        "可操作性": 0.1      # 内容的实用性和指导价值
    }
    
    scored_insights = []
    
    try:
        for item in raw_insights:
            # 确保内容字段的存在
            title = item.get('title', '')
            content = item.get('content', '')
            if not content and not title:
                continue
                
            # 创建评估提示
            prompt = f"""
            请评估以下原始内容与'{topic}'主题的相关性和信息质量，根据以下标准给出1-10分的评分：
            
            标题: {title}
            内容: {content[:800]}...
            
            评分标准:
            1. 主题相关性 (1-10分): 内容与'{topic}'主题的直接相关程度，是否涵盖主题的核心方面
            2. 信息质量 (1-10分): 内容的完整性、深度、信息密度和准确性
            3. 时效性 (1-10分): 内容的新鲜度和对当前情况的反映程度
            4. 可操作性 (1-10分): 内容是否提供有实用价值的见解或建议
            
            请以JSON格式返回评分和一句话理由，只包含以下字段:
            {{
                "主题相关性": 分数,
                "信息质量": 分数,
                "时效性": 分数,
                "可操作性": 分数,
                "总分": 加权总分,
                "推荐理由": "一句话说明这条洞察的价值或推荐/不推荐理由",
                "适合章节": "这条内容最适合放在哪个章节（行业定义/发展历程/产业链/市场格局/核心驱动/未来展望/政策环境）"
            }}
            """
            
            try:
                # 使用专门的JSON API调用方法
                system_message = "你是一位专业的行业分析师，擅长评估内容的相关性、质量和实用价值。你的回答必须是严格的JSON格式，不包含任何其他文本。"
                
                scores = llm_processor.call_llm_api_json(prompt, system_message)
                
                # 计算加权得分
                weighted_score = 0
                for criterion, weight in criteria.items():
                    if criterion in scores:
                        weighted_score += scores[criterion] * weight
                        
                # 使用计算的加权分数或API返回的总分
                final_score = scores.get("总分", weighted_score)
                
                # 将分数存储到内容项中
                item["relevance_score"] = final_score
                item["detailed_scores"] = scores
                item["recommendation_reason"] = scores.get("推荐理由", "")
                item["suggested_section"] = scores.get("适合章节", "")
                
                scored_insights.append(item)
                
            except Exception as e:
                print(f"评估洞察内容时出错: {str(e)}")
                # 出错时给予默认分数
                item["relevance_score"] = 5.0
                item["detailed_scores"] = {
                    "主题相关性": 5.0,
                    "信息质量": 5.0,
                    "时效性": 5.0,
                    "可操作性": 5.0,
                    "总分": 5.0
                }
                scored_insights.append(item)
        
        # 按相关性得分排序
        scored_insights.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        # 筛选评分高于阈值的内容（例如7分以上）
        high_quality_insights = [item for item in scored_insights if item.get("relevance_score", 0) >= 7.0]
        
        # 如果高质量内容太少，放宽标准
        if len(high_quality_insights) < 3:
            high_quality_insights = scored_insights[:5]  # 至少取前5个
        
        print(f"完成洞察内容相关性评分，从{len(scored_insights)}条中筛选出{len(high_quality_insights)}条高质量内容")
        return high_quality_insights
        
    except Exception as e:
        print(f"LLM相关性评估失败: {str(e)}，返回未筛选的原始数据")
        return raw_insights

def get_raw_industry_data_by_section(topic, section, llm_processor=None):
    """
    获取单个章节的原始数据，并立即评估筛选
    
    Args:
        topic (str): 主题
        section (str): 章节名称
        llm_processor: LLM处理器实例
        
    Returns:
        list: 该章节筛选后的高质量数据（8-15条）
    """
    tavily_collector = TavilyCollector()
    queries = []
    
    # 根据章节增加更多查询组合
    if "行业定义" in section or "核心特点" in section:
        queries.append({"query": f"{topic} 行业定义 技术特征 核心价值 边界", "section": section})
        queries.append({"query": f"{topic} 技术原理 核心功能 特点", "section": section})
        queries.append({"query": f"{topic} 定义 概念 范围 特点", "section": section})
        queries.append({"query": f"{topic} 技术架构 基础组件 核心价值主张", "section": section})
        queries.append({"query": f"{topic} 技术标准 关键特征 区别于传统方法", "section": section})
        queries.append({"query": f"{topic} 行业解析 核心技术 价值流", "section": section})
    
    elif "发展历程" in section or "阶段演进" in section:
        queries.append({"query": f"{topic} 发展历程 关键阶段 里程碑 技术演进", "section": section})
        queries.append({"query": f"{topic} 历史发展 演进路径 重大突破", "section": section})
        queries.append({"query": f"{topic} 发展史 阶段 关键事件", "section": section})
        queries.append({"query": f"{topic} 技术迭代 转折点 年表", "section": section})
        queries.append({"query": f"{topic} 历史沿革 代际变迁 技术演化", "section": section})
        queries.append({"query": f"{topic} 发展时间线 突破性事件 行业变革", "section": section})
    
    elif "产业链" in section or "价值分布" in section:
        queries.append({"query": f"{topic} 产业链 上游 中游 下游 结构", "section": section})
        queries.append({"query": f"{topic} 价值分布 成本结构 利润分配", "section": section})
        queries.append({"query": f"{topic} 产业生态 供应链 价值链", "section": section})
        queries.append({"query": f"{topic} 上下游企业 价值占比 核心环节", "section": section})
        queries.append({"query": f"{topic} 产业结构 利润分布 关键角色", "section": section})
        queries.append({"query": f"{topic} 产业地图 价值流动 环节分析", "section": section})
    
    elif "市场格局" in section or "参与者" in section:
        queries.append({"query": f"{topic} 市场格局 竞争状况 市场份额 领先企业", "section": section})
        queries.append({"query": f"{topic} 主要参与者 代表性企业 商业模式", "section": section})
        queries.append({"query": f"{topic} 市场竞争 头部企业 排名", "section": section})
        queries.append({"query": f"{topic} 市场集中度 竞争优势 商业地位", "section": section})
        queries.append({"query": f"{topic} 细分市场 区域格局 国内外企业对比", "section": section})
        queries.append({"query": f"{topic} 产业参与者 技术壁垒 竞争策略", "section": section})
    
    elif "核心驱动" in section or "趋势" in section:
        queries.append({"query": f"{topic} 驱动因素 发展趋势 市场需求 技术演进", "section": section})
        queries.append({"query": f"{topic} 趋势预测 技术发展 商业模式变革", "section": section})
        queries.append({"query": f"{topic} 行业趋势 发展方向 演变", "section": section})
        queries.append({"query": f"{topic} 主要趋势 科技突破 未来技术路线图", "section": section})
        queries.append({"query": f"{topic} 行业变革 创新驱动 需求动力", "section": section})
        queries.append({"query": f"{topic} 增长驱动力 新兴技术融合 产业升级", "section": section})
    
    elif "未来展望" in section or "挑战应对" in section:
        queries.append({"query": f"{topic} 未来展望 技术突破 创新机遇", "section": section})
        queries.append({"query": f"{topic} 行业挑战 问题 解决方案 策略", "section": section})
        queries.append({"query": f"{topic} 未来发展 创新 突破 前景", "section": section})
        queries.append({"query": f"{topic} 挑战 困难 应对策略", "section": section})
        queries.append({"query": f"{topic} 增长空间 机遇窗口 发展瓶颈", "section": section})
        queries.append({"query": f"{topic} 行业前景 预测分析 战略方向", "section": section})
    
    elif "政策环境" in section:
        queries.append({"query": f"{topic} 政策环境 法规 监管 全球对比", "section": section})
        queries.append({"query": f"{topic} 产业政策 扶持措施 监管趋势 影响", "section": section})
        queries.append({"query": f"{topic} 法律法规 标准 合规要求", "section": section})
        queries.append({"query": f"{topic} 国家政策 地方支持 监管框架", "section": section})
        queries.append({"query": f"{topic} 国际政策 国内法规 合规成本", "section": section})
        queries.append({"query": f"{topic} 政策导向 行业标准 合规体系", "section": section})
    
    # 执行查询并收集结果
    section_results = []
    query_errors = 0
    
    for query_info in queries:
        query = query_info["query"]
        
        try:
            print(f"正在搜索章节'{section}'的资料: {query}")
            results = tavily_collector.search(query, max_results=10)  # 增加每个查询的结果数量
            
            print(f"查询 '{query}' 返回了 {len(results)} 条结果")
            
            if not results:
                print(f"警告: 查询 '{query}' 没有返回任何结果")
                continue
            
            # 验证结果格式
            for i, result in enumerate(results):
                if not isinstance(result, dict):
                    continue
                    
                # 确保result有必要的字段
                if "content" not in result or not result["content"]:
                    result["content"] = f"关于{query}的内容未获取到详细信息。"
                
                # 设置章节字段和来源查询
                result["section"] = section
                result["source_query"] = query
            
            # 添加到章节结果集
            section_results.extend(results)
            
        except Exception as e:
            print(f"查询'{query}'时出错: {str(e)}")
            query_errors += 1
    
    print(f"章节'{section}'共收集到 {len(section_results)} 条原始结果")
    
    # 如果查询全部失败或没有结果，返回空列表
    if query_errors == len(queries) or len(section_results) == 0:
        print(f"章节'{section}'的所有查询失败或没有返回结果")
        return []
    
    # 立即进行相关性评估和筛选
    if llm_processor and section_results:
        print(f"立即评估章节'{section}'的 {len(section_results)} 条资料相关性...")
        scored_results = evaluate_insights_relevance(section_results, f"{topic} {section}", llm_processor)
        
        # 保留最相关的8-15条，大幅增加数量以提供更丰富内容
        if len(scored_results) > 15:
            print(f"章节'{section}'从 {len(scored_results)} 条中筛选出最相关的15条")
            high_quality_results = scored_results[:15]
        elif len(scored_results) > 8:
            print(f"章节'{section}'从 {len(scored_results)} 条中筛选出最相关的{len(scored_results)}条")
            high_quality_results = scored_results
        else:
            # 如果结果少于8条，尽量保留所有结果
            high_quality_results = scored_results
            
        return high_quality_results
    
    # 如果没有LLM处理器，简单筛选
    if len(section_results) > 10:
        # 基于标题和内容长度的简单筛选
        section_results.sort(key=lambda x: len(x.get("content", "")), reverse=True)
        return section_results[:10]
    
    return section_results

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
    
    try:
        # 初始化LLM处理器用于相关性评估
        llm_processor = None
        try:
            llm_processor = LLMProcessor()
            print("已初始化LLM处理器用于内容相关性评估")
        except Exception as e:
            print(f"初始化LLM处理器失败: {str(e)}，将跳过相关性评估")
        
        # 使用标准章节结构
        if not subtopics:
            subtopics = [
                "行业定义与核心特点",
                "发展历程与阶段演进",
                "产业链与价值分布",
                "市场格局与参与者",
                "核心驱动与趋势",
                "未来展望与挑战应对",
                "政策环境分析"
            ]
        
        # 按章节分批收集、评估和筛选资料
        filtered_data = []
        sections_data = {}
        
        for section in subtopics:
            print(f"\n开始处理章节: {section}")
            
            # 获取并评估该章节的资料
            section_data = get_raw_industry_data_by_section(topic, section, llm_processor)
            
            if section_data:
                # 添加到总结果集
                filtered_data.extend(section_data)
                # 按章节归类
                sections_data[section] = section_data
                print(f"章节'{section}'成功获取 {len(section_data)} 条高质量资料")
            else:
                print(f"章节'{section}'未找到合适资料，将使用备用内容")
        
        # 如果没有获取到任何有效数据，使用备选方法
        if not filtered_data:
            print("所有章节均未找到有效资料，使用备用生成方法")
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
            
        # 使用已筛选好的数据按章节组织报告
        print("\n使用筛选后的高质量数据组织报告内容...")
        insights_data = organize_industry_insights_with_sources(filtered_data, topic, subtopics, llm_processor, sections_data)
        
        print(f"已成功生成行业洞察报告，共包含{len(insights_data.get('sections', []))}个章节")
        return insights_data
            
    except Exception as e:
        print(f"生成行业洞察报告时出错: {str(e)}，使用系统生成的内容...")
        
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

def organize_industry_insights_with_sources(filtered_data, topic, subtopics, llm_processor=None, sections_data=None):
    """
    使用筛选后的数据组织行业洞察报告，并在每个小点下添加来源信息
    注意：每个章节保留5-8条资料
    
    Args:
        filtered_data (list): 筛选后的高质量数据
        topic (str): 主题
        subtopics (list): 子主题列表
        llm_processor: LLM处理器
        sections_data: 已按章节分类的数据
        
    Returns:
        dict: 包含组织好的报告内容
    """
    if not filtered_data:
        print("没有筛选后的数据，使用备用生成方法")
        return {
            "title": f"{topic}行业洞察 (系统生成)",
            "sections": [],
            "sources": [],
            "date": datetime.now().strftime('%Y-%m-%d')
        }
    
    # 导入行业洞察的标准结构
    standard_sections = []
    if subtopics:
        standard_sections = subtopics
    else:
        standard_sections = [
            "行业定义与核心特点",
            "发展历程与阶段演进",
            "产业链与价值分布",
            "市场格局与参与者", 
            "核心驱动与趋势",
            "未来展望与挑战应对",
            "政策环境分析"
        ]
    
    # 初始化报告内容
    report_content = f"# {topic}行业洞察\n\n"
    
    # 初始化结构化章节数据和来源引用
    structured_sections = []
    sources = []
    
    # 如果没有提供sections_data，则重新按章节组织数据
    if not sections_data:
        sections_data = {}
        for item in filtered_data:
            section = item.get("section", "其他")
            # 使用suggested_section如果有的话
            if "suggested_section" in item and item["suggested_section"]:
                # 映射到标准章节名称
                suggested = item["suggested_section"].lower()
                if "定义" in suggested or "特点" in suggested:
                    section = "行业定义与核心特点"
                elif "历程" in suggested or "演进" in suggested or "发展" in suggested:
                    section = "发展历程与阶段演进"
                elif "产业链" in suggested or "价值" in suggested:
                    section = "产业链与价值分布"
                elif "市场" in suggested or "格局" in suggested or "参与者" in suggested:
                    section = "市场格局与参与者"
                elif "驱动" in suggested or "趋势" in suggested:
                    section = "核心驱动与趋势"
                elif "未来" in suggested or "展望" in suggested or "挑战" in suggested:
                    section = "未来展望与挑战应对"
                elif "政策" in suggested or "环境" in suggested:
                    section = "政策环境分析"
            
            if section not in sections_data:
                sections_data[section] = []
            sections_data[section].append(item)
    
    # 使用LLM处理器生成章节内容
    for section_name in standard_sections:
        if section_name in sections_data and sections_data[section_name]:
            # 为每个章节添加二级标题
            section_title = f"{topic}{section_name}"
            report_content += f"## {section_title}\n\n"
            
            # 获取章节数据（已经是筛选过的3-4条）
            section_items = sections_data[section_name]
            
            # 使用LLM处理生成章节内容
            section_content = ""
            if llm_processor:
                try:
                    # 根据资料数量使用不同处理逻辑
                    if len(section_items) == 1:
                        item = section_items[0]
                        title = item.get("title", "")
                        content = item.get("content", "").strip()
                        source = item.get("source", "行业分析")
                        url = item.get("url", "#")
                        
                        # 针对单资料的详细处理提示
                        prompt = f"""请基于以下关于"{topic}{section_name}"的详细资料，创建一个内容非常丰富、结构清晰的分析报告章节。务必详尽展开，不要简略处理：

资料标题: {title}
资料内容: {content}

要求：
1. 生成一个标题为"# {title}"的markdown格式章节
2. 分析必须极其深入且详尽，包含至少7-10个有层次的子标题
3. 每个小节必须有充分展开的内容，确保内容的深度和广度
4. 使用Markdown格式组织内容，重要观点和数据使用**粗体**标记
5. 分析长度必须在2500-3500字以上，确保内容极其充实和深入
6. 保留所有重要数据点和事实，整合到合适的上下文中
7. 使用多级标题（##、###、####）组织内容，确保结构分明
8. 对原始内容进行充分扩展和深入挖掘，绝不简单复述
9. 在文末添加数据来源: {source} - {url}
10. 内容必须专业、权威且有极高的分析深度，彻底避免浅尝辄止
11. 每个小节建议包含4-6个段落，确保充分展开论述
12. 使用简短小标题+详尽内容的组织方式，使内容既有层次又便于阅读
"""
                    elif len(section_items) == 2:
                        # 两条资料处理逻辑
                        item1 = section_items[0]
                        item2 = section_items[1]
                        title1 = item1.get("title", "")
                        title2 = item2.get("title", "")
                        content1 = item1.get("content", "").strip()
                        content2 = item2.get("content", "").strip()
                        source1 = item1.get("source", "行业分析")
                        source2 = item2.get("source", "行业分析")
                        url1 = item1.get("url", "#")
                        url2 = item2.get("url", "#")
                        
                        prompt = f"""请基于以下两条资料，为'{topic}行业洞察报告'的'{section_name}'章节生成极其详尽、结构清晰的内容。

                        资料1标题: {title1}
                        资料1内容: {content1[:3000]}...
                        
                        资料2标题: {title2}
                        资料2内容: {content2[:3000]}...
                        
                        要求：
                        1. 深入分析和整合这两条资料，提取所有关键信息和见解
                        2. 内容必须极其详尽全面，至少包含8-10个主要小节
                        3. 使用层级标题组织内容：
                           - 使用三级标题(###)作为主要分块，至少创建8-10个三级标题
                           - 在每个三级标题下，使用四级标题(####)进一步细分内容，每个三级标题下至少有3-5个四级标题
                        4. 每个小节都必须有充分展开的内容，建议每个四级标题下200-400字
                        5. 确保标题简洁明了，能够概括该小节的核心内容
                        6. 在相应内容后标注来源信息: 
                           [数据来源1: {source1} - {url1}]
                           [数据来源2: {source2} - {url2}]
                        7. 内容要绝对详尽，总体长度不少于4000字
                        8. 对于数据和关键观点，使用**粗体**标记或项目符号(•)呈现，确保重点突出
                        9. 必须包含行业最新数据、深度分析和专业洞见，避免泛泛而谈
                        10. 对于矛盾的观点或数据，进行对比分析并提供客观评估
                        """
                    else:
                        # 3-4条资料的处理提示，确保生成更丰富的内容
                        resource_texts = []
                        source_references = []
                        
                        # 准备资料和来源引用
                        for i, item in enumerate(section_items):
                            title = item.get("title", "")
                            content = item.get("content", "").strip()
                            source = item.get("source", "行业分析")
                            url = item.get("url", "#")
                            
                            resource_texts.append(f"资料{i+1}标题: {title}\n资料{i+1}内容: {content[:1200]}...")
                            source_references.append(f"[数据来源{i+1}: {source} - {url}]")
                        
                        # 组合所有资料
                        all_resources = "\n\n".join(resource_texts)
                        source_reference_text = "\n".join(source_references)
                        
                        prompt = f"""请基于以下关于"{topic}{section_name}"的多个资料来源，创建一个极其详尽、专业且结构清晰的行业分析章节。本章节需要是报告中最全面深入的部分：

{all_resources}

要求：
1. 创建一个内容极其丰富的专业行业分析章节，整合所有资料的核心观点和数据
2. 分析必须非常深入且全面，使用多级标题组织内容（##、###、####）
3. 必须详尽覆盖所有资料中的重要观点，进行系统性整合与深度拓展
4. 章节应分为至少7-10个子标题，每个子标题下内容详尽充实
5. 总体内容长度应达到4000-6000字，确保分析深度远超普通报告
6. 对重要数据和概念使用**粗体**标记，提高可读性
7. 使用专业术语和行业标准表述，保证内容权威性和专业性
8. 在适当位置添加以下来源引用，确保内容可溯源：
{source_reference_text}
9. 每个小节标题应具体明确，并能准确概括其内容
10. 不要简单堆砌资料，必须形成有深度的分析框架和独到见解
11. 每个观点必须有充分展开的论述，避免点到即止
12. 各小节之间应有逻辑衔接，形成连贯的分析体系
13. 确保包含最新行业数据、案例分析和未来趋势预测
14. 在章节开头提供简短概述，结尾处给出全面总结
"""
                    
                    system_message = f"""
                    你是一位专业的{topic}行业分析师和内容组织专家，擅长创建结构清晰的专业报告。
                    你的特长是将复杂内容拆分成逻辑连贯、层次分明的小节，使读者能轻松理解深度内容。
                    你会使用多级标题结构，确保每个小节都有适当的长度和深度。
                    你会避免创建过长的段落，而是采用简短段落、列表和表格等多种展现形式。
                    请确保生成的内容结构明确，小节划分合理，段落简短易读。
                    """
                    
                    # 设置较大的token限制，确保内容生成充分
                    try:
                        # 使用较低的temperature值以确保结构一致性
                        section_content = llm_processor.call_llm_api(prompt, system_message, temperature=0.2, max_tokens=8000)
                    except:
                        # 如果上述调用失败，退回到标准调用
                        section_content = llm_processor.call_llm_api(prompt, system_message)
                    
                    # === 新增：将[数据来源X]编号替换为完整来源 ===
                    import re
                    # 构建编号到来源的映射
                    source_map = {}
                    for idx, item in enumerate(section_items, 1):
                        name = item.get("source", "行业分析")
                        url = item.get("url", "#")
                        source_map[str(idx)] = f"[数据来源: {name} - {url}]"
                    # 替换所有[数据来源X]为完整来源
                    def replace_source(match):
                        idx = match.group(1)
                        return source_map.get(idx, match.group(0))
                    section_content = re.sub(r"\[数据来源(\d+)\]", replace_source, section_content)

                    # 确保来源信息在章节中
                    if len(section_items) == 1 and f"[数据来源" not in section_content:
                        item = section_items[0]
                        source = item.get("source", "行业分析")
                        url = item.get("url", "#")
                        section_content += f"\n\n[数据来源: {source} - {url}]"
                    
                except Exception as e:
                    print(f"使用LLM生成'{section_name}'章节内容时出错: {str(e)}，使用简单方法")
                    # 使用简单合并方法作为备选
                    section_content = generate_section_content_simple(section_items)
            else:
                # 如果没有LLM处理器，使用简单方法
                section_content = generate_section_content_simple(section_items)
            
            # 添加章节内容到报告
            report_content += section_content + "\n\n"
            
            # 收集来源
            for item in section_items:
                source_title = item.get("title", "未知标题")
                source_url = item.get("url", "#")
                source_name = item.get("source", "未知来源")
                
                sources.append({
                    "title": source_title,
                    "url": source_url,
                    "source": source_name
                })
            
            # 添加到结构化章节
            structured_sections.append({
                "title": section_title,
                "content": section_content
            })
    
    # 添加参考资料部分
    if sources:
        report_content += "## 参考资料\n\n"
        seen_urls = set()
        for source in sources:
            url = source.get("url", "#")
            title = source.get("title", "未知标题")
            source_name = source.get("source", "未知来源")
            
            # 去重
            if url not in seen_urls:
                report_content += f"- [{title}]({url}) - {source_name}\n"
                seen_urls.add(url)
    
    # 返回组织好的报告
    return {
        "title": f"{topic}行业洞察报告",
        "content": report_content,
        "sections": structured_sections,
        "sources": sources,
        "date": datetime.now().strftime('%Y-%m-%d')
    }

def generate_section_content_simple(section_items):
    """
    使用简单方法生成章节内容，确保在每个小点下添加来源
    注意：现在每个章节有8-15条资料，需要分成更小的小节，并确保内容详尽
    
    Args:
        section_items: 章节数据项列表（通常有8-15个元素）
        
    Returns:
        str: 生成的章节内容
    """
    content = ""
    
    # 按相关性评分排序（确保最好的内容在前）
    section_items.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    # 添加章节摘要
    if len(section_items) > 0:
        content += "### 章节概述\n\n"
        overview = "本章节基于对多种权威资料的整合分析，提供了全面且深入的行业洞察。以下内容将从多个维度展开详细分析，涵盖了最新数据、关键趋势和专业观点。\n\n"
        content += overview
    
    # 处理每个项目
    for i, item in enumerate(section_items):
        title = item.get("title", f"要点{i+1}")
        item_content = item.get("content", "").strip()
        
        # 获取来源信息
        source_name = item.get("source", "行业分析")
        source_url = item.get("url", "#")
        
        # 创建三级标题
        content += f"### {title}\n\n"
        
        # 将内容分成更小的段落，但保留更多内容并确保详尽
        if len(item_content) > 500:
            # 尝试按段落分割
            paragraphs = item_content.split('\n\n')
            
            # 如果没有合适的段落分隔，尝试按句号分割
            if len(paragraphs) < 3:
                sentences = item_content.replace('。', '。\n').replace('！', '！\n').replace('？', '？\n').split('\n')
                # 重新组织成更小的段落，每3-5个句子一个段落
                paragraphs = []
                current_para = []
                
                for sentence in sentences:
                    if not sentence.strip():
                        continue
                    current_para.append(sentence)
                    if len(current_para) >= 3:
                        paragraphs.append(''.join(current_para))
                        current_para = []
                
                # 添加剩余句子
                if current_para:
                    paragraphs.append(''.join(current_para))
            
            # 创建四级标题和小节
            # 根据内容推断可能的小节标题
            section_keywords = ["概述", "定义", "特点", "历史", "发展", "应用", "案例", "挑战", "前景", "趋势", 
                              "原理", "方法", "分析", "影响", "评估", "现状", "机制", "比较", "优势", "劣势", 
                              "技术路线", "市场数据", "区域分布", "关键指标", "主要参与者"]
            
            # 创建分段内容，大幅增加保留内容量
            for j, para in enumerate(paragraphs[:18]):  # 增加小节数量限制
                if j < len(section_keywords):
                    subtitle = f"{title}的{section_keywords[j]}"
                else:
                    subtitle = f"{title}的扩展分析({j+1})"
                
                # 添加四级标题
                content += f"#### {subtitle}\n\n"
                
                # 添加段落内容，增加字符限制
                if len(para) > 8000:  # 增加字符限制
                    para = para[:8000] + "..."
                
                content += f"{para}\n\n"
                # 每个小节都加引用
                content += f"[数据来源: {source_name} - {source_url}]\n\n"
        else:
            # 如果内容本身就很短，直接添加
            content += f"{item_content}\n\n"
            content += f"[数据来源: {source_name} - {source_url}]\n\n"
    
    # 添加章节总结
    if len(section_items) > 0:
        content += "### 章节小结\n\n"
        summary = "综合以上分析，本章节全面阐述了相关领域的核心要点和最新发展。通过多维度的数据和案例分析，为读者提供了深入理解行业现状与趋势的基础。后续章节将进一步探讨其他关键方面，形成完整的行业洞察体系。\n\n"
        content += summary
    
    return content

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
    
    # 如果有content字段，直接使用
    if "content" in insights_data and insights_data["content"]:
        content = insights_data["content"]
    else:
        # 否则使用旧方法提取内容并格式化
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
    
    # 修复报告中的标题问题
    print("正在优化报告标题格式...")
    fix_markdown_headings(output_file)
    
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