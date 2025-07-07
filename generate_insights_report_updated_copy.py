import os
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
import sys
from fix_md_headings import fix_markdown_headings
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

from collectors.tavily_collector import TavilyCollector
from collectors.news_collector import NewsCollector
from collectors.brave_search_collector import BraveSearchCollector
from collectors.google_search_collector import GoogleSearchCollector

from generators.report_generator import ReportGenerator
from collectors.llm_processor import LLMProcessor
import config
import logging

# 关闭HTTP请求日志，减少干扰
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

class ParallelInsightsCollector:
    """
    并行洞察数据收集器
    负责多层级的并行数据收集和处理
    """
    
    def __init__(self):
        self.results_lock = threading.Lock()
        
        # 初始化搜索收集器
        self.collectors = {}
        
        # Tavily收集器（必需）
        try:
            self.tavily_collector = TavilyCollector()
            self.collectors['tavily'] = self.tavily_collector
            print("✅ Tavily搜索收集器已初始化")
        except Exception as e:
            print(f"❌ Tavily搜索收集器初始化失败: {str(e)}")
            raise
        
        # Brave收集器（可选）
        try:
            self.brave_collector = BraveSearchCollector()
            if hasattr(self.brave_collector, 'has_api_key') and self.brave_collector.has_api_key:
                self.collectors['brave'] = self.brave_collector
                print("✅ Brave搜索收集器已启用")
            else:
                print("⚠️ Brave搜索收集器未配置API密钥，已跳过")
        except Exception as e:
            print(f"⚠️ Brave搜索收集器初始化失败: {str(e)}")
    
    def parallel_collect_all_sections(self, topic, sections, llm_processor=None, max_workers=4):
        """
        🚀 并行收集所有章节的数据（第1层并行）
        
        Args:
            topic: 主题
            sections: 章节列表
            llm_processor: LLM处理器
            max_workers: 最大并行工作数
            
        Returns:
            dict: 按章节组织的数据结果
        """
        print(f"🚀 [第1层并行] 开始并行收集{len(sections)}个章节的数据...")
        start_time = time.time()
        
        sections_data = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 🚀 并行提交所有章节任务
            future_to_section = {
                executor.submit(
                    self._collect_single_section_data, topic, section, llm_processor
                ): section for section in sections
            }
            
            # 🔄 收集章节结果
            completed_count = 0
            for future in as_completed(future_to_section):
                section = future_to_section[future]
                try:
                    section_data = future.result()
                    completed_count += 1
                    
                    with self.results_lock:
                        sections_data[section] = section_data
                    
                    print(f"  ✅ [{completed_count}/{len(sections)}] 章节'{section}'收集完成，获得{len(section_data)}条数据")
                    
                except Exception as e:
                    print(f"  ❌ 章节'{section}'收集失败: {str(e)}")
                    sections_data[section] = []
        
        total_time = time.time() - start_time
        total_items = sum(len(data) for data in sections_data.values())
        print(f"📊 [第1层并行完成] 总计收集{total_items}条数据，耗时{total_time:.1f}秒")
        
        return sections_data
    
    def _collect_single_section_data(self, topic, section, llm_processor):
        """收集单个章节的数据，内部使用第2层并行"""
        return self.parallel_collect_section_queries(topic, section, llm_processor)
    
    def parallel_collect_section_queries(self, topic, section, llm_processor=None, max_workers=6):
        """
        🎯 并行执行单个章节内的多个查询（第2层并行）
        
        Args:
            topic: 主题
            section: 章节名称
            llm_processor: LLM处理器
            max_workers: 最大并行查询数
            
        Returns:
            list: 该章节的数据结果
        """
        # 首先扩展搜索关键词
        expanded_topics = expand_search_keywords(topic, llm_processor)
        
        # 生成查询列表
        all_queries = self._generate_section_queries(expanded_topics, section)
        
        print(f"  🔍 [第2层并行] 章节'{section}'并行执行{len(all_queries)}个查询...")
        
        section_results = []
        seen_urls = set()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 🚀 并行提交所有查询任务
            future_to_query = {
                executor.submit(
                    self._execute_single_query, query_info["query"]
                ): query_info for query_info in all_queries
            }
            
            # 🔄 收集查询结果
            completed_count = 0
            for future in as_completed(future_to_query):
                query_info = future_to_query[future]
                try:
                    query_results = future.result()
                    completed_count += 1
                    
                    # 去重并添加到结果
                    new_results = 0
                    for result in query_results:
                        url = result.get("url", "")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            result["section"] = section
                            result["source_query"] = query_info["query"]
                            section_results.append(result)
                            new_results += 1
                    
                    if new_results > 0:
                        print(f"    ✅ [{completed_count}/{len(all_queries)}] 查询完成: +{new_results}条新数据")
                    else:
                        print(f"    ➖ [{completed_count}/{len(all_queries)}] 查询完成: 无新数据")
                        
                except Exception as e:
                    print(f"    ❌ 查询失败: {str(e)}")
        
        # 立即进行相关性评估和筛选
        if llm_processor and section_results:
            print(f"    🔍 评估章节'{section}'的{len(section_results)}条数据相关性...")
            scored_results = evaluate_insights_relevance(section_results, f"{topic} {section}", llm_processor)
            
            # 保留最相关的8-12条
            if len(scored_results) > 12:
                final_results = scored_results[:12]
                print(f"    ✂️ 从{len(scored_results)}条中筛选出最相关的12条")
            else:
                final_results = scored_results
                print(f"    ✅ 保留{len(final_results)}条高质量数据")
                
            return final_results
        
        # 简单筛选（无LLM时）
        if len(section_results) > 10:
            section_results.sort(key=lambda x: len(x.get("content", "")), reverse=True)
            return section_results[:10]
        
        return section_results
    
    def _generate_section_queries(self, expanded_topics, section):
        """为特定章节生成查询列表"""
        all_queries = []
        
        for expanded_topic in expanded_topics:
            queries = []
            
            if "行业定义" in section or "核心特点" in section:
                queries.extend([
                    f"{expanded_topic} 行业定义 技术特征 核心价值 边界",
                    f"{expanded_topic} 技术原理 核心功能 特点",
                    f"{expanded_topic} 定义 概念 范围 特点",
                    f"{expanded_topic} 技术架构 基础组件 核心价值主张",
                    f"{expanded_topic} 技术标准 关键特征 区别于传统方法",
                    f"{expanded_topic} 行业解析 核心技术 价值流"
                ])
            elif "发展历程" in section or "阶段演进" in section:
                queries.extend([
                    f"{expanded_topic} 发展历程 关键阶段 里程碑 技术演进",
                    f"{expanded_topic} 历史发展 演进路径 重大突破",
                    f"{expanded_topic} 发展史 阶段 关键事件",
                    f"{expanded_topic} 技术迭代 转折点 年表",
                    f"{expanded_topic} 历史沿革 代际变迁 技术演化",
                    f"{expanded_topic} 发展时间线 突破性事件 行业变革"
                ])
            elif "产业链" in section or "价值分布" in section:
                queries.extend([
                    f"{expanded_topic} 产业链 上游 中游 下游 结构",
                    f"{expanded_topic} 价值分布 成本结构 利润分配",
                    f"{expanded_topic} 产业生态 供应链 价值链",
                    f"{expanded_topic} 上下游企业 价值占比 核心环节",
                    f"{expanded_topic} 产业结构 利润分布 关键角色",
                    f"{expanded_topic} 产业地图 价值流动 环节分析"
                ])
            elif "市场格局" in section or "参与者" in section:
                queries.extend([
                    f"{expanded_topic} 市场格局 竞争状况 市场份额 领先企业",
                    f"{expanded_topic} 主要参与者 代表性企业 商业模式",
                    f"{expanded_topic} 市场竞争 头部企业 排名",
                    f"{expanded_topic} 市场集中度 竞争优势 商业地位",
                    f"{expanded_topic} 细分市场 区域格局 国内外企业对比",
                    f"{expanded_topic} 产业参与者 技术壁垒 竞争策略"
                ])
            elif "核心驱动" in section or "趋势" in section:
                queries.extend([
                    f"{expanded_topic} 驱动因素 发展趋势 市场需求 技术演进",
                    f"{expanded_topic} 趋势预测 技术发展 商业模式变革",
                    f"{expanded_topic} 行业趋势 发展方向 演变",
                    f"{expanded_topic} 主要趋势 科技突破 未来技术路线图",
                    f"{expanded_topic} 行业变革 创新驱动 需求动力",
                    f"{expanded_topic} 增长驱动力 新兴技术融合 产业升级"
                ])
            elif "未来展望" in section or "挑战应对" in section:
                queries.extend([
                    f"{expanded_topic} 未来展望 技术突破 创新机遇",
                    f"{expanded_topic} 行业挑战 问题 解决方案 策略",
                    f"{expanded_topic} 未来发展 创新 突破 前景",
                    f"{expanded_topic} 挑战 困难 应对策略",
                    f"{expanded_topic} 增长空间 机遇窗口 发展瓶颈",
                    f"{expanded_topic} 行业前景 预测分析 战略方向"
                ])
            elif "政策环境" in section:
                queries.extend([
                    f"{expanded_topic} 政策环境 法规 监管 全球对比",
                    f"{expanded_topic} 产业政策 扶持措施 监管趋势 影响",
                    f"{expanded_topic} 法律法规 标准 合规要求",
                    f"{expanded_topic} 国家政策 地方支持 监管框架",
                    f"{expanded_topic} 国际政策 国内法规 合规成本",
                    f"{expanded_topic} 政策导向 行业标准 合规体系"
                ])
            
            # 转换为查询信息对象
            for query in queries:
                all_queries.append({"query": query, "section": section})
        
        return all_queries
    
    def _execute_single_query(self, query):
        """执行单个查询，在多个搜索引擎中搜索"""
        search_results = []
        used_urls = set()
        
        for name, collector in self.collectors.items():
            try:
                if name == 'tavily':
                    results = collector.search(query, max_results=3)
                elif name == 'brave':
                    results = collector.search(query, count=3)
                else:
                    continue
                    
                if results:
                    for result in results:
                        url = result.get('url', '')
                        if url and url not in used_urls:
                            result['search_source'] = name
                            search_results.append(result)
                            used_urls.add(url)
                            
            except Exception:
                continue
        
        return search_results

class ParallelInsightsProcessor:
    """
    并行洞察内容生成器
    负责第3层并行：多个章节的内容生成
    """
    
    def __init__(self, llm_processor):
        self.llm_processor = llm_processor
        self.results_lock = threading.Lock()
    
    def parallel_generate_sections_content(self, sections_data, topic, max_workers=3):
        """
        ⚡ 并行生成多个章节的内容（第3层并行）
        
        Args:
            sections_data: 按章节组织的数据
            topic: 主题
            max_workers: 最大并行工作数
            
        Returns:
            dict: 生成的章节内容
        """
        print(f"⚡ [第3层并行] 开始并行生成{len(sections_data)}个章节的内容...")
        start_time = time.time()
        
        generated_sections = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 🚀 并行提交章节内容生成任务
            future_to_section = {}
            
            for section_name, section_items in sections_data.items():
                if section_items:  # 只处理有数据的章节
                    future_to_section[executor.submit(
                        self._generate_single_section_content, 
                        section_name, section_items, topic
                    )] = section_name
            
            # 🔄 收集生成结果
            completed_count = 0
            for future in as_completed(future_to_section):
                section_name = future_to_section[future]
                try:
                    section_content = future.result()
                    completed_count += 1
                    
                    with self.results_lock:
                        generated_sections[section_name] = section_content
                    
                    content_length = len(section_content) if section_content else 0
                    print(f"  ✅ [{completed_count}/{len(future_to_section)}] 章节'{section_name}'内容生成完成，长度{content_length}字符")
                    
                except Exception as e:
                    print(f"  ❌ 章节'{section_name}'内容生成失败: {str(e)}")
                    generated_sections[section_name] = ""
        
        total_time = time.time() - start_time
        total_length = sum(len(content) for content in generated_sections.values())
        print(f"📊 [第3层并行完成] 总计生成{total_length}字符内容，耗时{total_time:.1f}秒")
        
        return generated_sections
    
    def _generate_single_section_content(self, section_name, section_items, topic):
        """生成单个章节的内容"""
        if not self.llm_processor or not section_items:
            return generate_section_content_simple(section_items)
        
        try:
            # 根据资料数量使用不同的生成策略
            if len(section_items) == 1:
                return self._generate_single_item_content(section_items[0], topic, section_name)
            elif len(section_items) == 2:
                return self._generate_two_items_content(section_items, topic, section_name)
            else:
                return self._generate_multiple_items_content(section_items, topic, section_name)
                
        except Exception as e:
            print(f"⚠️ LLM生成章节'{section_name}'内容失败: {str(e)}，使用简单方法")
            return generate_section_content_simple(section_items)
    
    def _generate_single_item_content(self, item, topic, section_name):
        """单个资料的内容生成"""
        title = item.get("title", "")
        content = item.get("content", "").strip()
        source = item.get("source", "行业分析")
        url = item.get("url", "#")
        
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
        
        system_message = f"你是一位专业的{topic}行业分析师和内容组织专家，擅长创建结构清晰的专业报告。"
        
        return self.llm_processor.call_llm_api(prompt, system_message, temperature=0.2, max_tokens=8000)
    
    def _generate_two_items_content(self, section_items, topic, section_name):
        """两个资料的内容生成"""
        item1, item2 = section_items[0], section_items[1]
        
        prompt = f"""请基于以下两条资料，为'{topic}行业洞察报告'的'{section_name}'章节生成极其详尽、结构清晰的内容。

资料1标题: {item1.get("title", "")}
资料1内容: {item1.get("content", "")[:3000]}...

资料2标题: {item2.get("title", "")}
资料2内容: {item2.get("content", "")[:3000]}...

要求：
1. 深入分析和整合这两条资料，提取所有关键信息和见解
2. 内容必须极其详尽全面，至少包含8-10个主要小节
3. 使用层级标题组织内容：
   - 使用三级标题(###)作为主要分块，至少创建8-10个三级标题
   - 在每个三级标题下，使用四级标题(####)进一步细分内容
4. 每个小节都必须有充分展开的内容
5. 在相应内容后标注来源信息
6. 内容要绝对详尽，总体长度不少于4000字
7. 对于数据和关键观点，使用**粗体**标记或项目符号呈现
8. 必须包含行业最新数据、深度分析和专业洞见
"""
        
        system_message = f"你是一位专业的{topic}行业分析师和内容组织专家。"
        
        return self.llm_processor.call_llm_api(prompt, system_message, temperature=0.2, max_tokens=8000)
    
    def _generate_multiple_items_content(self, section_items, topic, section_name):
        """多个资料的内容生成"""
        resource_texts = []
        source_references = []
        
        for i, item in enumerate(section_items):
            title = item.get("title", "")
            content = item.get("content", "").strip()
            source = item.get("source", "行业分析")
            url = item.get("url", "#")
            
            resource_texts.append(f"资料{i+1}标题: {title}\n资料{i+1}内容: {content[:1200]}...")
            source_references.append(f"[数据来源{i+1}: {source} - {url}]")
        
        all_resources = "\n\n".join(resource_texts)
        source_reference_text = "\n".join(source_references)
        
        prompt = f"""请基于以下关于"{topic}{section_name}"的多个资料来源，创建一个极其详尽、专业且结构清晰的行业分析章节：

{all_resources}

要求：
1. 创建一个内容极其丰富的专业行业分析章节，整合所有资料的核心观点和数据
2. 分析必须非常深入且全面，使用多级标题组织内容（##、###、####）
3. 必须详尽覆盖所有资料中的重要观点，进行系统性整合与深度拓展
4. 章节应分为至少7-10个子标题，每个子标题下内容详尽充实
5. 总体内容长度应达到4000-6000字，确保分析深度远超普通报告
6. 在适当位置添加来源引用：
{source_reference_text}
7. 每个小节标题应具体明确，并能准确概括其内容
8. 不要简单堆砌资料，必须形成有深度的分析框架和独到见解
"""
        
        system_message = f"你是一位专业的{topic}行业分析师和内容组织专家。"
        
        return self.llm_processor.call_llm_api(prompt, system_message, temperature=0.2, max_tokens=8000)

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

def expand_search_keywords(topic, llm_processor=None):
    """
    使用LLM扩展搜索关键词，包括中英文、相关术语等
    
    Args:
        topic (str): 原始主题
        llm_processor: LLM处理器实例
        
    Returns:
        list: 扩展后的关键词列表（最多5个）
    """
    if not llm_processor:
        # 如果没有LLM处理器，返回基本的中英文组合
        english_topic = topic.replace('AI', 'Artificial Intelligence').replace('+', ' ')
        return [topic, english_topic]
    
    try:
        prompt = f"""请基于主题"{topic}"，生成最相关的5个搜索关键词，包括：
1. 中英文对照（必须包含）
2. 相关术语和概念
3. 行业通用说法

要求：
1. 关键词要专业准确
2. 确保相关性从高到低排序
3. 只返回最相关的5个关键词
4. 确保中英文都有覆盖
5. 适合搜索引擎使用

请以JSON格式返回，格式如下：
{{
    "keywords": [
        "关键词1",
        "关键词2",
        "关键词3",
        "关键词4",
        "关键词5"
    ]
}}

注意：严格遵守JSON格式，确保双引号正确使用，确保JSON可以被正确解析。
"""
        
        system_message = f"""你是一位精通{topic}领域的专家，对该领域的各种专业术语和表达方式都非常熟悉。
你需要帮助生成一个简短但准确的搜索关键词列表，这些关键词将用于搜索引擎检索相关内容。
请确保生成的关键词专业、准确、相关性高，并严格遵守JSON格式规范。"""

        # 使用LLM生成关键词列表
        response = llm_processor.call_llm_api_json(prompt, system_message)
        
        if isinstance(response, dict) and "keywords" in response:
            expanded_keywords = response["keywords"]
            # 确保原始关键词在列表中
            if topic not in expanded_keywords:
                expanded_keywords.insert(0, topic)
                # 如果插入后超过5个，删除最后一个
                if len(expanded_keywords) > 5:
                    expanded_keywords = expanded_keywords[:5]
            print(f"成功扩展关键词：从1个扩展到{len(expanded_keywords)}个")
            return expanded_keywords
            
    except Exception as e:
        print(f"扩展关键词时出错: {str(e)}")
    
    # 出错时返回基本的中英文组合
    english_topic = topic.replace('AI', 'Artificial Intelligence').replace('+', ' ')
    return [topic, english_topic]

# 已被 ParallelInsightsCollector 替代的旧函数
# def get_raw_industry_data_by_section(topic, section, llm_processor=None):
#     """
#     [已废弃] 获取单个章节的原始数据，并立即评估筛选 - 多渠道整合版本
#     此函数已被 ParallelInsightsCollector.parallel_collect_section_queries 替代
#     """
#     pass

def get_industry_insights(topic, subtopics=None, parallel_config="balanced"):
    """
    🚀 并行获取行业洞察数据
    
    Args:
        topic (str): 主题
        subtopics (list): 子主题列表
        parallel_config (str): 并行配置 ("conservative", "balanced", "aggressive")
        
    Returns:
        dict: 包含行业洞察内容和来源的字典
    """
    print(f"\n🚀 === 开始并行收集{topic}行业洞察 ===")
    overall_start_time = time.time()
    
    try:
        # 初始化LLM处理器
        llm_processor = None
        try:
            llm_processor = LLMProcessor()
            print("✅ 已初始化LLM处理器用于内容相关性评估和生成")
        except Exception as e:
            print(f"❌ 初始化LLM处理器失败: {str(e)}，将跳过智能功能")
        
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
        
        # 🚀 初始化并行数据收集器
        try:
            parallel_collector = ParallelInsightsCollector()
        except Exception as e:
            print(f"❌ 初始化并行收集器失败: {str(e)}，使用备用方法")
            return _fallback_insights_generation(topic, subtopics)
        
        # 🎯 配置并行参数
        parallel_configs = {
            "conservative": {"section_workers": 3, "query_workers": 4, "content_workers": 2},
            "balanced": {"section_workers": 4, "query_workers": 6, "content_workers": 3},
            "aggressive": {"section_workers": 6, "query_workers": 8, "content_workers": 4}
        }
        
        config = parallel_configs.get(parallel_config, parallel_configs["balanced"])
        print(f"⚙️ 使用并行配置: {parallel_config}")
        print(f"   - 章节并行数: {config['section_workers']}")
        print(f"   - 查询并行数: {config['query_workers']}")
        print(f"   - 内容生成并行数: {config['content_workers']}")
        
        # 🚀 第1-2层并行：并行收集所有章节数据
        sections_data = parallel_collector.parallel_collect_all_sections(
            topic, subtopics, llm_processor, max_workers=config['section_workers']
        )
        
        # 检查数据收集结果
        total_items = sum(len(data) for data in sections_data.values())
        if total_items == 0:
            print("⚠️ 所有章节均未收集到有效数据，使用备用生成方法")
            return _fallback_insights_generation(topic, subtopics)
        
        print(f"📊 数据收集阶段完成，总计收集到 {total_items} 条高质量数据")
        
        # ⚡ 第3层并行：并行生成章节内容
        if llm_processor:
            parallel_processor = ParallelInsightsProcessor(llm_processor)
            generated_sections = parallel_processor.parallel_generate_sections_content(
                sections_data, topic, max_workers=config['content_workers']
            )
        else:
            print("⚠️ 无LLM处理器，使用简单内容生成")
            generated_sections = {}
            for section_name, section_items in sections_data.items():
                generated_sections[section_name] = generate_section_content_simple(section_items)
        
        # 📝 组织最终报告
        insights_data = _organize_parallel_insights_report(
            generated_sections, sections_data, topic, subtopics
        )
        
        # 📊 性能统计
        total_time = time.time() - overall_start_time
        estimated_sequential_time = total_time * 3.5  # 估算串行时间
        time_saved = estimated_sequential_time - total_time
        speedup_ratio = estimated_sequential_time / total_time
        
        print("\n" + "=" * 60)
        print("📊 并行洞察报告生成性能统计:")
        print(f"⏱️  实际耗时: {total_time:.1f}秒")
        print(f"🐌 串行预估: {estimated_sequential_time:.1f}秒")
        print(f"⚡ 时间节省: {time_saved:.1f}秒")
        print(f"🚀 性能提升: {speedup_ratio:.1f}x")
        print(f"📄 生成章节: {len(insights_data.get('sections', []))}个")
        print(f"📚 数据来源: {len(insights_data.get('sources', []))}个")
        print(f"🔧 并行配置: {parallel_config}")
        print("=" * 60)
        
        print(f"🎉 并行行业洞察报告生成完成！")
        return insights_data
            
    except Exception as e:
        print(f"❌ 并行生成行业洞察报告时出错: {str(e)}，使用备用方法...")
        return _fallback_insights_generation(topic, subtopics)

def _fallback_insights_generation(topic, subtopics):
    """备用的洞察生成方法"""
    print("🛡️ 使用备用洞察生成方法...")
    
    fallback_insights = generate_industry_insights_without_api(topic, subtopics)
    
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

def _organize_parallel_insights_report(generated_sections, sections_data, topic, subtopics):
    """组织并行生成的洞察报告"""
    structured_sections = []
    sources = []
    
    # 按标准章节顺序组织内容
    for section_name in subtopics:
        if section_name in generated_sections and generated_sections[section_name]:
            section_title = f"{topic}{section_name}"
            section_content = generated_sections[section_name]
            
            structured_sections.append({
                "title": section_title,
                "content": section_content
            })
            
            # 收集该章节的数据来源
            if section_name in sections_data:
                for item in sections_data[section_name]:
                    source_title = item.get("title", "未知标题")
                    source_url = item.get("url", "#")
                    source_name = item.get("source", "未知来源")
                    
                    sources.append({
                        "title": source_title,
                        "url": source_url,
                        "source": source_name
                    })
    
    # 生成完整报告内容
    report_content = f"# {topic}行业洞察报告\n\n"
    
    for section in structured_sections:
        report_content += f"## {section['title']}\n\n{section['content']}\n\n"
    
    # 添加参考资料（去重）
    if sources:
        report_content += "## 参考资料\n\n"
        seen_urls = set()
        for source in sources:
            url = source.get("url", "#")
            title = source.get("title", "未知标题")
            source_name = source.get("source", "未知来源")
            
            if url not in seen_urls:
                report_content += f"- [{title}]({url}) - {source_name}\n"
                seen_urls.add(url)
    
    return {
        "title": f"{topic}行业洞察报告",
        "content": report_content,
        "sections": structured_sections,
        "sources": sources,
        "date": datetime.now().strftime('%Y-%m-%d')
    }

# 已被 _organize_parallel_insights_report 替代的旧函数
# def organize_industry_insights_with_sources(filtered_data, topic, subtopics, llm_processor=None, sections_data=None):
#     """
#     [已废弃] 使用筛选后的数据组织行业洞察报告
#     此函数已被 _organize_parallel_insights_report 替代
#     """
#     pass

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

def generate_insights_report(topic, subtopics=None, output_file=None, parallel_config="balanced"):
    """
    🚀 生成并行行业洞察报告
    
    Args:
        topic (str): 主题
        subtopics (list): 子主题列表
        output_file (str): 输出文件名或路径
        parallel_config (str): 并行配置 ("conservative", "balanced", "aggressive")
        
    Returns:
        tuple: (报告文件路径, 报告数据)
    """
    print(f"🚀 开始生成并行行业洞察报告: {topic}")
    print(f"⚙️ 并行配置: {parallel_config}")
    
    # 确保输出目录存在
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    # 🚀 使用并行方法获取行业洞察数据
    insights_data = get_industry_insights(topic, subtopics, parallel_config)
    
    # 提取内容
    if "content" in insights_data and insights_data["content"]:
        content = insights_data["content"]
    else:
        # 备用方法：从sections组织内容
        title = insights_data.get("title", f"{topic}行业洞察")
        
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
            seen_urls = set()
            for source in sources:
                url = source.get('url', '#')
                title = source.get('title', '未知标题')
                source_name = source.get('source', '未知来源')
                
                if url not in seen_urls:
                    content += f"- [{title}]({url}) - {source_name}\n"
                    seen_urls.add(url)
    
    # 确定输出文件路径
    if not output_file:
        # 如果没有提供输出文件，使用默认命名
        date_str = datetime.now().strftime('%Y%m%d')
        clean_topic = topic.replace(' ', '_').replace('/', '_').replace('\\', '_').lower()
        output_file = os.path.join(config.OUTPUT_DIR, f"{clean_topic}_insights_parallel_{date_str}.md")
    elif not os.path.isabs(output_file):
        # 如果提供的是相对路径，确保正确拼接
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
    
    # 写入报告
    with open(output_file, 'w', encoding='utf-8-sig') as f:
        f.write(content)
    
    print(f"\n🎉 === 并行行业洞察报告生成完成 ===")
    print(f"📄 报告已保存至: {output_file}")
    print(f"📊 报告统计:")
    print(f"   - 章节数量: {len(insights_data.get('sections', []))}")
    print(f"   - 数据来源: {len(insights_data.get('sources', []))}")
    print(f"   - 文件大小: {len(content)} 字符")
    
    # 修复报告中的标题问题
    print("🔧 正在优化报告标题格式...")
    fix_markdown_headings(output_file)
    
    return output_file, insights_data

if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='🚀 生成并行行业洞察报告',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
并行配置说明:
  conservative  - 保守模式 (3/4/2): 节省系统资源，适合配置较低的机器
  balanced      - 平衡模式 (4/6/3): 默认模式，平衡性能与资源消耗
  aggressive    - 激进模式 (6/8/4): 最大化并行性能，需要较高配置

使用示例:
  python generate_insights_report_updated_copy.py --topic "人工智能" --parallel balanced
  python generate_insights_report_updated_copy.py --topic "区块链" --parallel aggressive --output my_report.md
  python generate_insights_report_updated_copy.py --topic "新能源汽车" --subtopics "电池技术" "充电设施" --parallel conservative
        """
    )
    
    parser.add_argument('--topic', type=str, required=True, help='报告的主题')
    parser.add_argument('--subtopics', type=str, nargs='*', help='与主题相关的子主题')
    parser.add_argument('--output', type=str, help='输出文件名')
    parser.add_argument('--parallel', type=str, choices=['conservative', 'balanced', 'aggressive'], 
                       default='balanced', help='并行配置 (默认: balanced)')
    
    args = parser.parse_args()
    
    # 显示启动信息
    print("🚀 " + "=" * 50)
    print("🚀 并行行业洞察报告生成器")
    print("🚀 " + "=" * 50)
    print(f"📝 主题: {args.topic}")
    if args.subtopics:
        print(f"📝 子主题: {', '.join(args.subtopics)}")
    print(f"⚙️ 并行配置: {args.parallel}")
    if args.output:
        print(f"📄 输出文件: {args.output}")
    print("🚀 " + "=" * 50)
    
    # 生成报告
    try:
        output_file, insights_data = generate_insights_report(
            args.topic, 
            args.subtopics, 
            args.output, 
            args.parallel
        )
        
        print(f"\n✅ 报告生成成功!")
        print(f"📄 文件路径: {output_file}")
        
    except KeyboardInterrupt:
        print("\n❌ 用户中断了报告生成过程")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 报告生成失败: {str(e)}")
        sys.exit(1) 