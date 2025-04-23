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
        list: 该章节筛选后的高质量数据（3-4条）
    """
    tavily_collector = TavilyCollector()
    queries = []
    
    # 根据章节创建具体查询
    if "行业定义" in section or "核心特点" in section:
        queries.append({"query": f"{topic} 行业定义 技术特征 核心价值 边界", "section": section})
        queries.append({"query": f"{topic} 技术原理 核心功能 特点", "section": section})
        queries.append({"query": f"{topic} 定义 概念 范围 特点", "section": section})
    
    elif "发展历程" in section or "阶段演进" in section:
        queries.append({"query": f"{topic} 发展历程 关键阶段 里程碑 技术演进", "section": section})
        queries.append({"query": f"{topic} 历史发展 演进路径 重大突破", "section": section})
        queries.append({"query": f"{topic} 发展史 阶段 关键事件", "section": section})
    
    elif "产业链" in section or "价值分布" in section:
        queries.append({"query": f"{topic} 产业链 上游 中游 下游 结构", "section": section})
        queries.append({"query": f"{topic} 价值分布 成本结构 利润分配", "section": section})
        queries.append({"query": f"{topic} 产业生态 供应链 价值链", "section": section})
    
    elif "市场格局" in section or "参与者" in section:
        queries.append({"query": f"{topic} 市场格局 竞争状况 市场份额 领先企业", "section": section})
        queries.append({"query": f"{topic} 主要参与者 代表性企业 商业模式", "section": section})
        queries.append({"query": f"{topic} 市场竞争 头部企业 排名", "section": section})
    
    elif "核心驱动" in section or "趋势" in section:
        queries.append({"query": f"{topic} 驱动因素 发展趋势 市场需求 技术演进", "section": section})
        queries.append({"query": f"{topic} 趋势预测 技术发展 商业模式变革", "section": section})
        queries.append({"query": f"{topic} 行业趋势 发展方向 演变", "section": section})
    
    elif "未来展望" in section or "挑战应对" in section:
        queries.append({"query": f"{topic} 未来展望 技术突破 创新机遇", "section": section})
        queries.append({"query": f"{topic} 行业挑战 问题 解决方案 策略", "section": section})
        queries.append({"query": f"{topic} 未来发展 创新 突破 前景", "section": section})
        queries.append({"query": f"{topic} 挑战 困难 应对策略", "section": section})
    
    elif "政策环境" in section:
        queries.append({"query": f"{topic} 政策环境 法规 监管 全球对比", "section": section})
        queries.append({"query": f"{topic} 产业政策 扶持措施 监管趋势 影响", "section": section})
        queries.append({"query": f"{topic} 法律法规 标准 合规要求", "section": section})
    
    # 执行查询并收集结果
    section_results = []
    query_errors = 0
    
    for query_info in queries:
        query = query_info["query"]
        
        try:
            print(f"正在搜索章节'{section}'的资料: {query}")
            results = tavily_collector.search(query, max_results=6)  # 增加每个查询的结果数
            
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
        
        # 保留最相关的3-4条
        if len(scored_results) > 4:
            print(f"章节'{section}'从 {len(scored_results)} 条中筛选出最相关的4条")
            high_quality_results = scored_results[:4]
        elif len(scored_results) > 2:
            print(f"章节'{section}'从 {len(scored_results)} 条中筛选出最相关的{len(scored_results)}条")
            high_quality_results = scored_results
        else:
            # 如果结果少于3条，尽量保留所有结果
            high_quality_results = scored_results
            
        return high_quality_results
    
    # 如果没有LLM处理器，简单筛选
    if len(section_results) > 4:
        # 基于标题和内容长度的简单筛选
        section_results.sort(key=lambda x: len(x.get("content", "")), reverse=True)
        return section_results[:4]
    
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
    注意：每个章节保留3-4条资料
    
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
    structured_sections = []
    sources = []
    report_content = f"# {topic}行业洞察报告\n\n"
    
    # 定义标准章节顺序
    standard_sections = [
        "行业定义与核心特点",
        "发展历程与阶段演进",
        "产业链与价值分布",
        "市场格局与参与者",
        "核心驱动与趋势",
        "未来展望与挑战应对",
        "政策环境分析"
    ]
    
    # 按标准顺序生成章节
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
                        # 单条资料处理逻辑
                        item = section_items[0]
                        title = item.get("title", "")
                        content = item.get("content", "").strip()
                        source = item.get("source", "行业分析")
                        url = item.get("url", "#")
                        
                        prompt = f"""
                        请基于以下单条资料，为'{topic}行业洞察报告'的'{section_name}'章节生成专业、结构清晰的内容。

                        资料标题: {title}
                        资料内容: {content[:3500]}...
                        
                        要求：
                        1. 深入分析这条资料，提取关键信息和见解
                        2. 将内容组织成多个简短的小节，确保结构清晰
                        3. 使用层级标题组织内容：
                           - 使用三级标题(###)作为主要分块，至少创建4-6个三级标题
                           - 在每个三级标题下，使用四级标题(####)进一步细分内容，每个三级标题下至少有2-3个四级标题
                        4. 控制每个段落的长度在100-250字之间，避免出现过长段落
                        5. 确保标题简洁明了，能够概括该小节的核心内容
                        6. 在相关内容后标注来源信息: [数据来源: {source} - {url}]
                        7. 内容要客观专业，突出核心洞见，总体长度约2000-3000字
                        8. 每个四级标题下的内容控制在200-300字之间，确保简洁明了
                        9. 不要出现连续超过10行的无标题文本
                        10. 对于数据和关键观点，使用项目符号(•)或编号列表呈现，提高可读性
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
                        
                        prompt = f"""
                        请基于以下两条资料，为'{topic}行业洞察报告'的'{section_name}'章节生成专业、结构清晰的内容。

                        资料1标题: {title1}
                        资料1内容: {content1[:2000]}...
                        
                        资料2标题: {title2}
                        资料2内容: {content2[:2000]}...
                        
                        要求：
                        1. 深入分析和整合这两条资料，提取关键信息和见解
                        2. 将内容组织成多个简短的小节，确保结构清晰
                        3. 使用层级标题组织内容：
                           - 使用三级标题(###)作为主要分块，至少创建5-7个三级标题
                           - 在每个三级标题下，使用四级标题(####)进一步细分内容，每个三级标题下至少有2-3个四级标题
                        4. 控制每个段落的长度在100-250字之间，避免出现过长段落
                        5. 确保标题简洁明了，能够概括该小节的核心内容
                        6. 在相应内容后标注来源信息: 
                           [数据来源1: {source1} - {url1}]
                           [数据来源2: {source2} - {url2}]
                        7. 内容要客观专业，突出核心洞见，总体长度约2500-3500字
                        8. 每个四级标题下的内容控制在200-300字之间，确保简洁明了
                        9. 不要出现连续超过10行的无标题文本
                        10. 对于数据和关键观点，使用项目符号(•)或编号列表呈现，提高可读性
                        """
                    else:
                        # 3-4条资料处理逻辑
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
                        
                        prompt = f"""
                        请基于以下{len(section_items)}条资料，为'{topic}行业洞察报告'的'{section_name}'章节生成专业、结构清晰的内容。
                        
                        {all_resources}
                        
                        要求：
                        1. 深入分析和整合这些资料，提取关键信息和见解
                        2. 将内容组织成多个简短的小节，确保结构清晰
                        3. 使用层级标题组织内容：
                           - 使用三级标题(###)作为主要分块，至少创建6-8个三级标题
                           - 在每个三级标题下，使用四级标题(####)进一步细分内容，每个三级标题下至少有2-4个四级标题
                        4. 控制每个段落的长度在100-250字之间，避免出现过长段落
                        5. 确保标题简洁明了，能够概括该小节的核心内容
                        6. 在相应内容后标注来源信息，示例格式: 
                           {source_references[0]}
                        7. 内容要客观专业，突出核心洞见，总体长度约3000-4000字
                        8. 每个四级标题下的内容控制在200-300字之间，确保简洁明了
                        9. 不要出现连续超过10行的无标题文本
                        10. 对于数据和关键观点，使用项目符号(•)或编号列表呈现，提高可读性
                        11. 在适当位置使用表格对比呈现不同要点
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
                        section_content = llm_processor.call_llm_api(prompt, system_message, temperature=0.2, max_tokens=4000)
                    except:
                        # 如果上述调用失败，退回到标准调用
                        section_content = llm_processor.call_llm_api(prompt, system_message)
                    
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
    注意：现在每个章节有3-4条资料，需要分成更小的小节
    
    Args:
        section_items: 章节数据项列表（通常有3-4个元素）
        
    Returns:
        str: 生成的章节内容
    """
    content = ""
    
    # 按相关性评分排序（确保最好的内容在前）
    section_items.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    # 处理每个项目
    for i, item in enumerate(section_items):
        title = item.get("title", f"要点{i+1}")
        item_content = item.get("content", "").strip()
        
        # 获取来源信息
        source_name = item.get("source", "行业分析")
        source_url = item.get("url", "#")
        
        # 创建三级标题
        content += f"### {title}\n\n"
        
        # 将内容分成更小的段落
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
            section_keywords = ["概述", "定义", "特点", "历史", "发展", "应用", "案例", "挑战", "前景", "趋势"]
            
            # 创建分段内容
            for j, para in enumerate(paragraphs[:8]):  # 限制最多8个小节
                if j < len(section_keywords):
                    subtitle = f"{title}的{section_keywords[j]}"
                else:
                    subtitle = f"{title}的其他方面({j+1})"
                
                # 添加四级标题
                content += f"#### {subtitle}\n\n"
                
                # 添加段落内容
                if len(para) > 3500:
                    para = para[:3500] + "..."
                
                content += f"{para}\n\n"
                
                # 每两个小节后添加一次来源引用
                if j % 2 == 1 or j == len(paragraphs[:8]) - 1:
                    content += f"[数据来源: {source_name} - {source_url}]\n\n"
        else:
            # 如果内容本身就很短，直接添加
            content += f"{item_content}\n\n"
            content += f"[数据来源: {source_name} - {source_url}]\n\n"
    
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