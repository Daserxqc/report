import os
import json
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sys
from fix_md_headings import fix_markdown_headings
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.tavily_collector import TavilyCollector
from collectors.google_search_collector import GoogleSearchCollector
from collectors.brave_search_collector import BraveSearchCollector
from generators.report_generator import ReportGenerator
import config

# 关闭HTTP请求日志，减少干扰
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

class IntelligentReportAgent:
    """智能报告生成代理，具备思考和反思能力"""
    
    def __init__(self):
        self.tavily_collector = TavilyCollector()
        self.llm_processor = self.tavily_collector._get_llm_processor()
        
        # 初始化多个搜索收集器
        self.collectors = {
            'tavily': self.tavily_collector,
        }
        
        # 尝试初始化Google搜索收集器
        try:
            self.google_collector = GoogleSearchCollector()
            if self.google_collector.has_api_key:
                self.collectors['google'] = self.google_collector
                print("✅ Google搜索收集器已启用")
            else:
                print("⚠️ Google搜索收集器未配置API密钥，已跳过")
                self.google_collector = None
        except Exception as e:
            print(f"⚠️ Google搜索收集器不可用: {str(e)}")
            self.google_collector = None
            
        # 尝试初始化Brave搜索收集器
        try:
            self.brave_collector = BraveSearchCollector()
            if self.brave_collector.has_api_key:
                self.collectors['brave'] = self.brave_collector
                print("✅ Brave搜索收集器已启用")
            else:
                print("⚠️ Brave搜索收集器未配置API密钥，已跳过")
                self.brave_collector = None
        except Exception as e:
            print(f"⚠️ Brave搜索收集器不可用: {str(e)}")
            self.brave_collector = None
        
        self.max_iterations = 5  # 最大迭代次数
        self.knowledge_gaps = []  # 知识缺口记录
        self.search_history = []  # 搜索历史
        self.detailed_analysis_mode = True  # 详细分析模式，生成更长更深入的内容
        
        print(f"🔍 已启用 {len(self.collectors)} 个搜索渠道: {', '.join(self.collectors.keys())}")
    
    def multi_channel_search(self, query, max_results=5):
        """
        多渠道搜索方法，整合多个搜索引擎的结果
        """
        all_results = []
        used_urls = set()  # 用于去重
        
        for name, collector in self.collectors.items():
            try:
                print(f"  🔍 {name}搜索: {query[:50]}...")
                
                if name == 'tavily':
                    results = collector.search(query, max_results=max_results)
                elif name == 'google':
                    results = collector.search(query, max_results=max_results)
                elif name == 'brave':
                    results = collector.search(query, count=max_results)
                else:
                    continue
                    
                if results:
                    # 去重并添加搜索来源标识
                    for result in results:
                        url = result.get('url', '')
                        if url and url not in used_urls:
                            result['search_source'] = name
                            all_results.append(result)
                            used_urls.add(url)
                    
                    print(f"    ✅ {name}: 获得 {len(results)} 条结果")
                else:
                    print(f"    ⚠️ {name}: 无结果")
                    
            except Exception as e:
                print(f"    ❌ {name}搜索出错: {str(e)}")
                continue
        
        print(f"  📊 多渠道搜索完成，共获得 {len(all_results)} 条去重结果")
        return all_results
        
    def generate_initial_queries(self, topic, days=7, companies=None):
        """
        第一步：智能查询生成
        分析用户需求，生成初始搜索策略
        """
        print(f"\n🧠 [思考阶段] 正在分析'{topic}'行业报告需求...")
        
        # 计算时间范围
        from datetime import datetime, timedelta
        today = datetime.now()
        
        # 构建初始查询生成提示
        query_prompt = f"""
        作为一个专业的行业分析师，我需要为'{topic}'行业生成一份全面的最新动态报告。
        请帮我分析这个主题的深度和广度，然后生成一系列初始搜索查询策略。
        
        ⚠️ **重要时间要求**：所有查询必须聚焦于{today.year}年最新信息，特别是最近{days}天的动态！
        
        分析要求：
        1. 这个行业的核心关注点是什么？
        2. 当前可能的热点话题有哪些？
        3. 需要从哪些角度来全面了解这个行业？
        4. 什么类型的信息对读者最有价值？
        
        请生成以下类型的搜索查询（每个查询都要包含时间限制）：
        - 重大事件类（4-6个查询）- 必须包含"{today.year}年最新"、"recent"等时间词
        - 技术创新类（3-4个查询）- 必须包含"{today.year}年新技术"、"latest innovation"等
        - 投资动态类（3-4个查询）- 必须包含"{today.year}年投资"、"recent funding"等
        - 政策监管类（2-3个查询）- 必须包含"{today.year}年政策"、"latest policy"等
        - 行业趋势类（3-4个查询）- 必须包含"{today.year}年趋势"、"current trends"等
        
        时间范围：最近{days}天，重点关注{today.strftime('%Y年%m月')}
        {'重点关注公司：' + ', '.join(companies) if companies else ''}
        
        请确保每个查询都包含明确的时间限制词汇，避免搜索到过时信息。
        """
        
        system_msg = f"你是一位经验丰富的{topic}行业研究专家，擅长制定全面的信息收集策略。"
        
        try:
            if not self.llm_processor:
                print("⚠️ [降级模式] LLM处理器不可用，使用默认搜索策略")
                return self._get_fallback_queries(topic, days, companies)
                
            response = self.llm_processor.call_llm_api(query_prompt, system_msg, max_tokens=4000)
            # 解析查询策略（这里简化处理，实际可以解析JSON）
            print(f"✅ [查询策略] 已生成{topic}行业的多维度搜索策略")
            return self._parse_query_strategy(response, topic, days, companies)
        except Exception as e:
            print(f"❌ [错误] 生成查询策略时出错: {str(e)}")
            print("🔄 [降级模式] 切换到默认搜索策略")
            return self._get_fallback_queries(topic, days, companies)
    
    def _parse_query_strategy(self, response, topic, days, companies):
        """解析查询策略响应 - 真正的多渠道整合搜索"""
        print(f"🔄 [多渠道整合] 正在整合多个搜索引擎的结果...")
        
        # 初始化合并后的数据结构
        merged_data = {
            "breaking_news": [],
            "innovation_news": [],
            "investment_news": [],
            "policy_news": [],
            "trend_news": [],
            "company_news": [],
            "total_count": 0
        }
        
        seen_urls = set()  # 用于去重
        
        # 1. 使用Brave搜索
        if self.brave_collector:
            try:
                print("  🔍 执行Brave综合搜索...")
                brave_data = self.brave_collector.get_comprehensive_research(topic, days)
                
                # 对Brave数据进行时间过滤
                for category in ["breaking_news", "innovation_news", "investment_news", "policy_news", "trend_news"]:
                    category_items = brave_data.get(category, [])
                    if category_items:
                        # 应用时间过滤
                        filtered_items = self.brave_collector._filter_by_date(category_items, days)
                        
                        # 合并过滤后的数据
                        for item in filtered_items:
                            url = item.get('url', '')
                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                merged_data[category].append(item)
                
                print(f"    ✅ Brave搜索完成，获得 {brave_data.get('total_count', 0)} 条结果")
            except Exception as e:
                print(f"    ❌ Brave搜索出错: {str(e)}")
        
        # 2. 使用Google搜索补充
        if self.google_collector:
            try:
                print("  🔍 执行Google补充搜索...")
                
                # 为每个类别执行Google搜索
                google_queries = {
                    "breaking_news": f"{topic} 行业 重大新闻 突发 重要事件 {datetime.now().year}年 最新",
                    "innovation_news": f"{topic} 技术创新 新产品 新技术 {datetime.now().year}年 最新",
                    "investment_news": f"{topic} 投资 融资 并购 {datetime.now().year}年 最新",
                    "policy_news": f"{topic} 政策 监管 法规 {datetime.now().year}年 最新",
                    "trend_news": f"{topic} 趋势 发展 前景 {datetime.now().year}年 最新"
                }
                
                google_added_count = 0
                for category, query in google_queries.items():
                    try:
                        google_results = self.google_collector.search(query, days_back=days, max_results=5)
                        if google_results:
                            # 应用时间过滤
                            filtered_results = self.google_collector._filter_by_date(google_results, days)
                            
                            # 合并过滤后的数据
                            for item in filtered_results:
                                url = item.get('url', '')
                                if url and url not in seen_urls:
                                    seen_urls.add(url)
                                    merged_data[category].append(item)
                                    google_added_count += 1
                    except Exception as e:
                        print(f"    ⚠️ Google搜索 {category} 出错: {str(e)}")
                        continue
                
                print(f"    ✅ Google搜索完成，新增 {google_added_count} 条去重结果")
            except Exception as e:
                print(f"    ❌ Google搜索出错: {str(e)}")
        
        # 3. 使用Tavily搜索补充
        try:
            print("  🔍 执行Tavily补充搜索...")
            tavily_data = self.tavily_collector.get_industry_news_direct(topic, days)
            
            # 合并Tavily数据，避免重复（Tavily已经在内部进行了时间过滤）
            added_count = 0
            for category in ["breaking_news", "innovation_news", "investment_news", "policy_news", "trend_news"]:
                for item in tavily_data.get(category, []):
                    url = item.get('url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        merged_data[category].append(item)
                        added_count += 1
            
            print(f"    ✅ Tavily搜索完成，新增 {added_count} 条去重结果")
        except Exception as e:
            print(f"    ❌ Tavily搜索出错: {str(e)}")
        
        # 4. 计算总数
        merged_data["total_count"] = sum(
            len(merged_data[key]) for key in merged_data.keys() 
            if key != "total_count"
        )
        
        print(f"📊 [整合完成] 多渠道搜索总计获得 {merged_data['total_count']} 条去重且时间过滤后的结果")
        return merged_data
    
    def _get_fallback_queries(self, topic, days, companies):
        """备用查询策略，当LLM不可用时使用"""
        print(f"🛡️ [备用策略] 使用预设的{topic}行业搜索策略")
        
        # 使用现有的搜索方法，但确保时间范围正确
        try:
            return self.tavily_collector.get_industry_news_direct(topic, days)
        except Exception as e:
            print(f"❌ [错误] 备用查询策略也失败: {str(e)}")
            # 返回空数据结构，避免程序崩溃
            return {
                "breaking_news": [],
                "innovation_news": [],
                "investment_news": [],
                "policy_news": [],
                "trend_news": [],
                "company_news": [],
                "total_count": 0
            }
    
    def reflect_on_information_gaps(self, collected_data, topic, days=7):
        """
        第三步：反思与知识缺口分析  
        分析已收集信息的完整性和质量
        """
        print(f"\n🤔 [反思阶段] 正在分析{topic}行业信息的完整性...")
        
        # 统计已收集的信息
        info_stats = {
            'breaking_news': len(collected_data.get('breaking_news', [])),
            'innovation_news': len(collected_data.get('innovation_news', [])),
            'investment_news': len(collected_data.get('investment_news', [])),
            'policy_news': len(collected_data.get('policy_news', [])),
            'trend_news': len(collected_data.get('trend_news', [])),
            'company_news': len(collected_data.get('company_news', []))
        }
        
        # 计算总信息条数
        total_items = sum(info_stats.values())
        
        # 分析信息缺口 - 更严格的标准
        reflection_prompt = f"""
        作为{topic}行业的资深分析师，请对以下信息收集情况进行严格评估：
        
        📊 **信息统计**：
        - 重大事件: {info_stats['breaking_news']}条
        - 技术创新: {info_stats['innovation_news']}条  
        - 投资动态: {info_stats['investment_news']}条
        - 政策监管: {info_stats['policy_news']}条
        - 行业趋势: {info_stats['trend_news']}条
        - 公司动态: {info_stats['company_news']}条
        - **总计**: {total_items}条
        
        🎯 **严格评估标准**：
        请按以下严格标准进行评估，只有**同时满足**所有条件才能认为信息充分：
        
        ✅ **数量要求**：
        - 每个类别至少5条高质量信息
        - 总信息量不少于40条
        - 各类别信息分布相对均匀
        
        ✅ **质量要求**：
        - 信息来源权威可靠
        - 时效性强（最近7天内的信息比例足够）
        - 涵盖行业核心发展动态
        
        ✅ **完整性要求**：
        - 技术、市场、政策、投资四大维度信息齐全
        - 包含不同规模企业的动态
        - 涵盖产业链上下游信息
        
        ✅ **平衡性要求**：
        - 包含正面和负面观点
        - 涵盖不同立场的声音（企业、监管、学术、投资者）
        - 包含国际和国内视角
        - 存在争议性话题的多元化观点
        
        **请严格按照上述标准评估**：
        
        如果**任何一个**方面不满足要求，请明确指出：
        1. 具体缺口是什么？
        2. 为什么这个缺口很重要？
        3. 需要搜索什么类型的信息？
        4. 建议的具体搜索策略？
        
        ⚠️ **重要**：只有在**完全满足**所有评估标准时，才能说"信息收集充分，可以开始报告生成"。
        否则，请详细说明需要补充的具体信息缺口。
        """
        
        system_msg = f"你是一位专业的{topic}行业分析师，具有敏锐的信息完整性判断能力。"
        
        try:
            if not self.llm_processor:
                print("⚠️ [降级模式] LLM不可用，跳过反思分析")
                return [], True  # 假设信息充分，直接生成报告
                
            reflection_result = self.llm_processor.call_llm_api(reflection_prompt, system_msg, max_tokens=6000)
            
            # 更合理的解析反思结果 - 调整标准使其更实用
            has_sufficient_text = "信息收集充分" in reflection_result or "可以开始" in reflection_result
            
            # 动态调整数量标准，基于实际搜索难度
            min_total = max(15, days * 2)  # 基于天数动态调整，最少15条
            min_per_category = max(2, days // 4)  # 每类别最少条数也动态调整
            
            has_sufficient_quantity = (
                total_items >= min_total and  # 动态总量要求
                sum(1 for count in info_stats.values() if count >= min_per_category) >= 3  # 至少3个类别有足够数据
            )
            
            # 特殊情况：如果重大事件类别有足够数据，可以适当放宽其他要求
            has_major_events = info_stats.get('breaking_news', 0) >= 3
            
            print(f"📊 [量化检查] 总量:{total_items}/{min_total}, 各类别最少:{min(info_stats.values())}/{min_per_category}")
            print(f"📊 [类别分布] 重大事件:{info_stats.get('breaking_news', 0)}, 创新:{info_stats.get('innovation_news', 0)}, 投资:{info_stats.get('investment_news', 0)}")
            
            if has_sufficient_text and (has_sufficient_quantity or has_major_events):
                print("✅ [反思结果] 信息收集充分，准备生成报告")
                return [], True
            else:
                if not has_sufficient_quantity and not has_major_events:
                    print(f"⚠️ [数量不足] 需要补充搜索 - 总量:{total_items}/{min_total}")
                else:
                    print("⚠️ [质量不足] AI分析认为需要补充搜索")
                print("🔄 [继续迭代] 发现信息缺口，进入下轮补充搜索")
                return [reflection_result], False
                
        except Exception as e:
            print(f"❌ [错误] 反思分析时出错: {str(e)}")
            print("🔄 [降级模式] 假设信息充分，继续生成报告")
            return [], True  # 出错时假设信息充分
    
    def generate_targeted_queries(self, gaps, topic, days=7):
        """
        第四步：迭代优化搜索
        根据知识缺口生成针对性搜索
        """
        print(f"\n🎯 [优化搜索] 正在为{topic}行业生成针对性查询...")
        
        if not gaps:
            return {}
            
        # 计算当前时间和搜索范围
        from datetime import datetime, timedelta
        today = datetime.now()
        start_date = today - timedelta(days=days)  # 使用传入的天数参数
        
        targeted_prompt = f"""
        基于以下{topic}行业报告的知识缺口分析：
        
        {gaps[0]}
        
        请分析具体的信息缺口，并生成3-5个针对性的搜索查询来补充这些缺口。
        
        ⚠️ **重要时间要求**：查询必须包含最新时间限制，获取{today.strftime('%Y年%m月')}的最新信息！
        
        🎯 **观点对比搜索策略**：
        - 如果缺口分析提到需要"观点对比分析"，请专门设计1-2个查询来获取不同观点
        - 搜索关键词包括：争议、质疑、批评、反对、风险、挑战、不同观点、alternative view
        - 平衡正面和负面信息，确保客观性
        
        输出格式：
        缺口1: [缺口描述]
        查询: "[具体搜索词] {today.strftime('%Y年%m月')} 最新"
        
        缺口2: [缺口描述] 
        查询: "[具体搜索词] {today.year} latest news"
        
        观点对比: [如需要，描述观点缺口]
        对比查询: "[行业关键词] 争议 质疑 风险 {today.year}年 不同观点"
        
        查询要求：
        1. 具体且有针对性
        2. 必须包含时间限制词：{today.year}年、latest、recent、最新、最近
        3. 覆盖识别出的主要缺口
        4. 适合搜索引擎查询
        5. 包含行业关键词：{topic}
        6. 每个查询都要包含时间相关词汇确保获取最新信息
        7. 如需观点对比，专门搜索质疑、批评、不同立场的声音
        """
        
        try:
            if not self.llm_processor:
                print("⚠️ [降级模式] LLM不可用，使用预设查询补充搜索")
                return self._fallback_targeted_search(topic, days)
                
            response = self.llm_processor.call_llm_api(targeted_prompt, f"你是{topic}行业的搜索专家")
            
            # 解析查询
            queries = self._parse_targeted_queries(response)
            
            if queries:
                print(f"🔍 [执行搜索] 开始执行{len(queries)}个针对性查询...")
                
                # 实际执行搜索
                additional_data = {}
                for i, query in enumerate(queries, 1):
                    print(f"  📊 查询 {i}/{len(queries)}: {query[:50]}...")
                    
                    # 使用多渠道搜索
                    try:
                        search_results = self.multi_channel_search(query, max_results=5)
                        if search_results:
                            # 将结果按类型分类
                            category = self._categorize_search_result(query, topic)
                            if category not in additional_data:
                                additional_data[category] = []
                            additional_data[category].extend(search_results)
                            print(f"    ✅ 找到 {len(search_results)} 条相关信息")
                        else:
                            print(f"    ⚠️ 未找到相关信息")
                    except Exception as e:
                        print(f"    ❌ 搜索出错: {str(e)}")
                
                print(f"✅ [搜索完成] 获得额外数据: {sum(len(v) for v in additional_data.values())} 条")
                return additional_data
            else:
                print("⚠️ [警告] 未能解析出有效的搜索查询")
                return self._fallback_targeted_search(topic, days)
            
        except Exception as e:
            print(f"❌ [错误] 生成针对性查询时出错: {str(e)}")
            print("🔄 [降级模式] 使用预设查询")
            return self._fallback_targeted_search(topic, days)
    
    def _parse_targeted_queries(self, response):
        """解析AI生成的查询响应"""
        queries = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if '查询:' in line or 'Query:' in line:
                # 提取引号内的内容
                if '"' in line:
                    start = line.find('"') + 1
                    end = line.rfind('"')
                    if start > 0 and end > start:
                        query = line[start:end].strip()
                        if query:
                            queries.append(query)
                # 如果没有引号，提取冒号后的内容
                elif ':' in line:
                    query = line.split(':', 1)[1].strip()
                    if query:
                        queries.append(query)
        
        # 如果解析失败，尝试简单分割
        if not queries:
            for line in lines:
                line = line.strip()
                if line and not line.startswith('缺口') and not line.startswith('Gap'):
                    if len(line) > 5 and len(line) < 100:  # 合理的查询长度
                        queries.append(line)
        
        return queries[:5]  # 最多返回5个查询
    
    def _fallback_targeted_search(self, topic, days=7):
        """当LLM不可用时的备用搜索策略 - 增强版，专注重大事件"""
        from datetime import datetime, timedelta
        today = datetime.now()
        
        # 预设的补充搜索查询（包含时间限制）- 专门针对重大事件优化
        end_date = today
        start_date = today - timedelta(days=days)
        
        # 重大事件专用查询
        major_event_queries = [
            f"{topic} 重大事件 突发 {today.year}年 最新 breaking news major event",
            f"{topic} 行业震动 重磅消息 {today.year} 最近{days}天 industry shock major news",
            f"{topic} 并购 收购 合并 {today.year}年 最新 merger acquisition latest",
            f"{topic} 重大发布 产品发布 {today.year} 最新 major launch product release",
            f"{topic} 监管 政策变化 {today.year}年 最新 regulation policy change latest"
        ]
        
        # 通用补充查询
        general_queries = [
            f"{topic} {today.year}年最新发展 recent developments latest {days} days",
            f"{topic} industry news {today.strftime('%B %Y')} latest recent {days} days",
            f"{topic} 行业动态 {today.year} 新闻 trends 最近{days}天",
            f"{topic} 争议 质疑 风险 挑战 {today.year}年 不同观点 criticism"
        ]
        
        # 合并所有查询，重大事件查询优先
        all_queries = major_event_queries + general_queries
        
        print(f"🔍 [备用搜索] 执行{len(all_queries)}个预设查询（重大事件优先）...")
        additional_data = {}
        
        for i, query in enumerate(all_queries, 1):
            print(f"  📊 预设查询 {i}/{len(all_queries)}: {query[:50]}...")
            try:
                # 对重大事件查询使用更多结果
                max_results = 5 if i <= len(major_event_queries) else 3
                search_results = self.multi_channel_search(query, max_results=max_results)
                if search_results:
                    # 重大事件查询的结果优先分类为breaking_news
                    if i <= len(major_event_queries):
                        category = 'breaking_news'
                    else:
                        category = self._categorize_search_result(query, topic)
                    
                    if category not in additional_data:
                        additional_data[category] = []
                    additional_data[category].extend(search_results)
                    print(f"    ✅ 找到 {len(search_results)} 条相关信息 -> {category}")
                else:
                    print(f"    ⚠️ 未找到相关信息")
            except Exception as e:
                print(f"    ❌ 搜索出错: {str(e)}")
        
        # 统计结果
        total_found = sum(len(v) for v in additional_data.values())
        breaking_found = len(additional_data.get('breaking_news', []))
        print(f"✅ [备用搜索完成] 总计找到 {total_found} 条信息，其中重大事件 {breaking_found} 条")
        
        return additional_data
    
    def _calculate_text_similarity(self, text1, text2):
        """计算两个文本的相似度（简单版本）"""
        if not text1 or not text2:
            return 0.0
        
        # 转换为小写并分词
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # 计算交集和并集
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        # 计算Jaccard相似度
        if len(union) == 0:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _is_content_similar(self, item1, item2, similarity_threshold=0.6):
        """判断两个新闻项目是否内容相似"""
        # 比较标题相似度
        title1 = item1.get('title', '')
        title2 = item2.get('title', '')
        title_similarity = self._calculate_text_similarity(title1, title2)
        
        # 比较内容相似度
        content1 = item1.get('content', '')[:200]  # 只比较前200字符
        content2 = item2.get('content', '')[:200]
        content_similarity = self._calculate_text_similarity(content1, content2)
        
        # 如果标题相似度很高，认为是重复内容
        if title_similarity > 0.7:
            return True
        
        # 如果标题和内容都有一定相似度，认为是重复内容
        if title_similarity > 0.4 and content_similarity > similarity_threshold:
            return True
        
        return False
    
    def _deduplicate_by_content(self, items, category_name=""):
        """基于内容相似度去重"""
        if not items:
            return items
        
        print(f"🔍 [智能去重] 正在对{category_name}类别的{len(items)}条数据进行内容去重...")
        
        deduplicated = []
        removed_count = 0
        
        for item in items:
            is_duplicate = False
            
            # 检查是否与已有项目相似
            for existing_item in deduplicated:
                if self._is_content_similar(item, existing_item):
                    is_duplicate = True
                    removed_count += 1
                    print(f"  ⚠️ 发现重复内容: {item.get('title', '无标题')[:50]}...")
                    break
            
            if not is_duplicate:
                deduplicated.append(item)
        
        if removed_count > 0:
            print(f"  ✅ {category_name}: 去除{removed_count}条重复内容，保留{len(deduplicated)}条")
        else:
            print(f"  ✅ {category_name}: 无重复内容")
        
        return deduplicated
    
    def _merge_data(self, existing_data, new_data):
        """合并新数据到现有数据中，只进行URL去重"""
        print(f"🔄 [数据合并] 正在合并新数据...")
        
        # 创建合并后的数据副本
        merged_data = existing_data.copy()
        
        for category, new_items in new_data.items():
            if category not in merged_data:
                merged_data[category] = []
            
            # 获取现有数据的URL集合，用于基础去重
            existing_urls = set()
            for item in merged_data[category]:
                if item.get('url'):
                    existing_urls.add(item['url'])
            
            # 基于URL的基础去重
            url_filtered_items = []
            for new_item in new_items:
                if new_item.get('url') and new_item['url'] not in existing_urls:
                    url_filtered_items.append(new_item)
                    existing_urls.add(new_item['url'])
                elif not new_item.get('url'):  # 如果没有URL，基于标题去重
                    title = new_item.get('title', '')
                    existing_titles = [item.get('title', '') for item in merged_data[category]]
                    if title and title not in existing_titles:
                        url_filtered_items.append(new_item)
            
            # 直接添加去重后的新数据
            if url_filtered_items:
                merged_data[category].extend(url_filtered_items)
                print(f"  ✅ {category}: 新增 {len(url_filtered_items)} 条数据")
            else:
                print(f"  ➖ {category}: 无新增数据（URL重复）")
        
        # 统计合并后的数据（只统计列表类型的数据）
        total_before = sum(len(v) for v in existing_data.values() if isinstance(v, list))
        total_after = sum(len(v) for v in merged_data.values() if isinstance(v, list))
        print(f"📊 [合并结果] 数据总量: {total_before} → {total_after} (+{total_after - total_before})")
        
        return merged_data
    
    def _categorize_search_result(self, query, topic):
        """根据查询内容将搜索结果分类"""
        query_lower = query.lower()
        
        # 优先检查是否为观点对比类
        if any(word in query_lower for word in ['争议', '质疑', '批评', '反对', '风险', '挑战', '不同观点', 'alternative', 'criticism', 'controversy', 'challenge', 'risk']):
            return 'perspective_analysis'
        elif any(word in query_lower for word in ['投资', '融资', 'investment', 'funding', '估值', 'valuation']):
            return 'investment_news'
        elif any(word in query_lower for word in ['政策', 'policy', '监管', 'regulation', '法规', 'law']):
            return 'policy_news'
        elif any(word in query_lower for word in ['技术', 'technology', '创新', 'innovation', '产品', 'product']):
            return 'innovation_news'
        elif any(word in query_lower for word in ['趋势', 'trend', '发展', 'development', '未来', 'future']):
            return 'trend_news'
        else:
            return 'breaking_news'  # 默认分类
    
    def generate_comprehensive_report_with_thinking(self, topic, days=7, companies=None):
        """
        智能报告生成主流程，包含完整的思考过程
        """
        print(f"\n🚀 开始为'{topic}'行业生成智能分析报告...")
        print("=" * 60)
        
        # 第一步：智能查询生成
        initial_data = self.generate_initial_queries(topic, days, companies)
        
        # 第二步：信息收集（使用现有方法）
        print(f"\n📊 [信息收集] 正在收集{topic}行业多维度信息...")
        all_news_data = initial_data
        
        # 如果有公司列表，补充公司特定信息
        if companies and isinstance(companies, list):
            print(f"🏢 [公司分析] 正在收集{len(companies)}家重点公司信息...")
            company_specifics = []
            for company in companies:
                # 尝试使用多个收集器获取公司新闻
                company_news = []
                
                # 暂时注释掉Google搜索
                if self.google_collector:
                    try:
                        google_news = self.google_collector.search(f"{company} {topic} 新闻 news {days}天 latest")
                        if google_news:
                            company_news.extend(google_news[:3])
                    except Exception as e:
                        print(f"  ⚠️ Google搜索{company}失败: {str(e)}")
                
                # 尝试使用Brave搜索
                if self.brave_collector and len(company_news) < 3:
                    try:
                        brave_news = self.brave_collector.search(f"{company} {topic} 动态 latest news", count=3-len(company_news))
                        if brave_news:
                            company_news.extend(brave_news)
                    except Exception as e:
                        print(f"  ⚠️ Brave搜索{company}失败: {str(e)}")
                
                # 最后使用Tavily搜索
                if len(company_news) < 3:
                    try:
                        tavily_news = self.tavily_collector.get_company_news(company, topic, days, max_results=3-len(company_news))
                        if tavily_news:
                            company_news.extend(tavily_news)
                    except Exception as e:
                        print(f"  ⚠️ Tavily搜索{company}失败: {str(e)}")
                        
                if company_news:
                    company_specifics.append({"company": company, "news": company_news})
            
            if company_specifics:
                all_news_data["company_news"] = [item for company_data in company_specifics for item in company_data["news"]]
        
        iteration_count = 0
        
        # 第三步：反思与迭代
        while iteration_count < self.max_iterations:
            iteration_count += 1
            print(f"\n🔄 [迭代轮次 {iteration_count}/{self.max_iterations}] - 当前数据总量: {all_news_data.get('total_count', 0)}条")
            
            # 反思分析
            gaps, is_sufficient = self.reflect_on_information_gaps(all_news_data, topic, days)
            
            if is_sufficient:
                print("✅ [决策] 信息收集完成，开始生成最终报告")
                break
            
            if iteration_count < self.max_iterations:
                print(f"🎯 [第{iteration_count}轮搜索] 开始补充信息缺口...")
                # 生成针对性查询并执行搜索
                additional_data = self.generate_targeted_queries(gaps, topic, days)
                
                # 合并新数据
                if additional_data:
                    old_total = all_news_data.get('total_count', 0)
                    all_news_data = self._merge_data(all_news_data, additional_data)
                    new_total = all_news_data.get('total_count', 0)
                    print(f"📈 [数据更新] 第{iteration_count}轮新增 {new_total - old_total} 条数据，总量: {new_total}")
                else:
                    print(f"📊 [第{iteration_count}轮结果] 本轮未获得新数据，可能需要调整搜索策略")
            else:
                print(f"⚠️ [达到上限] 已完成{self.max_iterations}轮迭代，开始生成报告")
                
        # 第五步：综合报告生成
        print(f"\n📝 [报告生成] 正在综合分析生成{topic}行业报告...")
        return self._generate_final_report(topic, all_news_data, companies, days)
    
    def _generate_final_report(self, topic, all_news_data, companies, days=7):
        """生成最终报告，使用原有的报告生成逻辑"""
        
        # 初始化报告内容
        content = f"# {topic}行业智能分析报告\n\n"
        # content += f"*本报告由AI智能代理生成，具备深度思考和反思能力*\n\n"
        date_str = datetime.now().strftime('%Y-%m-%d')
        content += f"报告日期: {date_str}\n\n"
        
        # 添加报告概述
        content += f"""## 📋 报告概述

本报告采用AI智能代理的五步分析法，对{topic}行业进行全方位深度解析。通过智能查询生成、
多维信息搜集、反思式缺口分析、迭代优化搜索和综合报告生成，确保信息的全面性和分析的深度。

**报告特色：**
- 🧠 深度思考：模拟专家级分析师的思维过程
- 🔄 多轮迭代：通过反思机制确保信息充分性
- 🎯 针对性强：根据识别的知识缺口进行补充搜索
- 📊 数据丰富：整合多源信息，提供全面视角
- 🔮 前瞻性强：不仅分析现状，更预测未来趋势

---

"""
        
        # 使用原有的处理函数生成各部分内容
        content += self._process_breaking_news_enhanced(topic, all_news_data.get("breaking_news", []), days)
        content += self._process_innovation_news_enhanced(topic, all_news_data.get("innovation_news", []))  
        content += self._process_investment_news_enhanced(topic, all_news_data.get("investment_news", []))
        content += self._process_policy_news_enhanced(topic, all_news_data.get("policy_news", []))
        content += self._process_industry_trends_enhanced(topic, all_news_data.get("trend_news", []), days)
        
        # 新增：观点对比分析部分
        if all_news_data.get("perspective_analysis"):
            content += self._process_perspective_analysis_enhanced(topic, all_news_data.get("perspective_analysis", []))
        
        # 公司动态部分
        if companies and all_news_data.get("company_news"):
            content += "## 重点公司动态分析\n\n"
            # 这里可以添加公司分析逻辑
        
        # 智能总结
        content += self._generate_intelligent_summary(topic, all_news_data, days)
        
        # 参考资料
        content += self._generate_references(all_news_data)
        
        return {
            "content": content,
            "data": all_news_data,
            "date": date_str
        }
    
    def _process_breaking_news_enhanced(self, topic, breaking_news, days=7):
        """增强版重大新闻处理，包含思考过程"""
        if not breaking_news:
            return f"## 行业重大事件\n\n📊 **分析说明**: 在当前时间窗口内，暂未发现{topic}行业的重大突发事件。\n\n"
        
        print(f"🔍 [深度分析] 正在分析{len(breaking_news)}条重大事件...")
        
        # 使用增强的分析提示
        all_news_text = "\n\n".join([
            f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
            for item in breaking_news
        ])
        
        # 首先生成重大事件摘要（严格按照days参数过滤时间）
        summary_section = self._generate_major_events_summary(topic, breaking_news, days)
        
        enhanced_prompt = f"""
        作为{topic}行业的首席分析师，请对以下重大事件进行深度分析：
        
        {all_news_text}
        
        分析框架：
        1. **事件重要性评估**: 按影响程度对事件进行排序和分类
        2. **多维度影响分析**: 分析对技术、市场、政策、竞争格局的影响
        3. **关联性分析**: 识别事件之间的内在联系和因果关系
        4. **趋势指向性**: 这些事件反映了什么趋势信号？
        5. **风险与机遇**: 为行业参与者带来的机遇和挑战
        
        🤔 **分析师思考过程**:
        - 首先梳理事件的时间线和逻辑关系
        - 然后评估每个事件的短期和长期影响
        - 最后综合判断对行业发展的指向意义
        
                 请保持分析的客观性和前瞻性，要求深度分析，字数控制在2000-2500字。
         
         📝 **深度分析要求**:
         - 每个重大事件都要从多个角度深入剖析
         - 提供详细的背景信息和发展脉络
         - 分析事件对产业链各环节的具体影响
         - 评估短期、中期、长期的影响程度
         - 识别事件背后的深层次原因和规律
         - 提供具体的应对策略和发展建议
         - 预测后续可能的连锁反应和发展趋势
        """
        
        system_msg = f"""你是{topic}行业的资深首席分析师，具备：
        1. 敏锐的行业洞察力
        2. 系统性的分析思维
        3. 前瞻性的判断能力
        4. 客观理性的分析态度
        请展现出专业分析师的思考深度。"""
        
        try:
            analysis = self.llm_processor.call_llm_api(enhanced_prompt, system_msg, max_tokens=8000)
            
            # 添加分析来源
            sources = []
            for item in breaking_news:
                if item.get('url', '#') != '#':
                    sources.append(f"- [{item.get('title', '未知标题')}]({item.get('url')}) - {item.get('source', '未知来源')}")
            
            if sources:
                analysis += "\n\n**信息来源:**\n" + "\n".join(sources)
            
            return f"## 🚨 行业重大事件深度分析\n\n{summary_section}\n\n### 📊 综合分析与影响评估\n\n{analysis}\n\n"
            
        except Exception as e:
            print(f"❌ [错误] 生成重大事件分析时出错: {str(e)}")
            return f"## 行业重大事件\n\n{summary_section}\n\n"
    
    def _generate_major_events_summary(self, topic, breaking_news, days=7):
        """生成行业重大事件摘要与关键细节部分（5-7个重点事件）"""
        if not breaking_news:
            return f"### 一、重大新闻摘要与关键细节\n\n📊 **事件概览**: 在最近{days}天内暂无重大事件。"
        
        print(f"📋 [事件摘要] 正在筛选和总结最重要的{min(7, len(breaking_news))}个重大事件...")
        
        # 准备所有新闻数据，并进行时间过滤验证
        from datetime import datetime, timedelta
        today = datetime.now()
        
        # 严格的时间过滤逻辑
        time_filtered_news = []
        current_year = today.year
        cutoff_date = today - timedelta(days=days)
        
        for item in breaking_news:
            should_include = False
            title = item.get('title', '')
            content = item.get('content', '')
            source = item.get('source', '')
            news_date = item.get('date', '') or item.get('published_date', '')
            
            # 检查是否包含明显的旧年份标识
            text_content = f"{title} {content} {source}".lower()
            old_year_patterns = ['2024年', '2023年', '2022年', '2021年', '2020年']
            has_old_year = any(pattern in text_content for pattern in old_year_patterns)
            
            if has_old_year:
                print(f"⚠️ [时间过滤] 跳过包含旧年份的新闻: {title[:50]}")
                continue
            
            # 检查是否包含当前年份或最新时间词汇
            current_time_patterns = [
                f'{current_year}年', f'{current_year}', 'latest', 'recent', 
                '最新', '最近', 'breaking', '刚刚', '今日', '今天',
                today.strftime('%Y年%m月'), today.strftime('%m月')
            ]
            
            has_recent_indicators = any(pattern in text_content for pattern in current_time_patterns)
            
            # 如果有明确的发布日期，检查是否在时间范围内
            if news_date and news_date != "未知日期":
                try:
                    # 尝试解析日期
                    parsed_date = None
                    try:
                        from dateutil import parser
                        parsed_date = parser.parse(str(news_date))
                    except ImportError:
                        # 如果没有dateutil，使用基础解析
                        if isinstance(news_date, str):
                            # 尝试基础的ISO日期格式
                            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d']:
                                try:
                                    parsed_date = datetime.strptime(news_date, fmt)
                                    break
                                except ValueError:
                                    continue
                    
                    if parsed_date and parsed_date >= cutoff_date:
                        should_include = True
                        print(f"✅ [时间验证] 日期符合要求: {title[:30]} ({parsed_date.strftime('%Y-%m-%d')})")
                    elif parsed_date:
                        print(f"⚠️ [时间过滤] 日期过早: {title[:30]} ({parsed_date.strftime('%Y-%m-%d')})")
                        continue
                    else:
                        raise ValueError("无法解析日期")
                except:
                    # 日期解析失败，使用关键词判断
                    if has_recent_indicators:
                        should_include = True
                        print(f"✅ [关键词验证] 包含最新时间词汇: {title[:30]}")
                    else:
                        print(f"⚠️ [时间过滤] 无法确定时间且缺乏最新标识: {title[:30]}")
                        continue
            else:
                # 没有发布日期，完全依靠内容关键词
                if has_recent_indicators:
                    should_include = True
                    print(f"✅ [关键词验证] 包含最新时间词汇: {title[:30]}")
                else:
                    print(f"⚠️ [时间过滤] 缺乏时间信息和最新标识: {title[:30]}")
                    continue
            
            if should_include:
                time_filtered_news.append(item)
        
        if not time_filtered_news:
            return f"### 一、重大新闻摘要与关键细节\n\n⚠️ **时间过滤结果**: 在最近{days}天内暂无符合要求的重大事件，可能需要放宽时间范围或检查数据源。"
        
        # 选择最重要的5-7个事件
        selected_news = time_filtered_news[:min(7, len(time_filtered_news))]
        
        all_news_text = "\n\n".join([
            f"事件{i+1}:\n标题: {item.get('title', '无标题')}\n时间: {item.get('date', '最近')}\n内容: {item.get('content', '无内容')[:400]}...\n来源: {item.get('source', '未知来源')}\n网址: {item.get('url', '#')}"
            for i, item in enumerate(selected_news)
        ])
        
        summary_prompt = f"""
        作为{topic}行业的资深分析师，请对以下最新重大事件进行智能筛选、去重和整理。

        最新事件信息：
        {all_news_text}

        🔍 **智能筛选任务**：
        1. **去重识别**：仔细分析所有事件，识别内容相似或重复的事件（如同一事件的不同报道）
        2. **重要性评估**：评估每个事件对{topic}行业的影响程度和重要性
        3. **时效性判断**：优先选择最新、最具时效性的事件
        4. **多样性保证**：确保选出的事件涵盖不同方面（技术、政策、市场、投资等）

        📋 **输出要求** - 请从所有事件中筛选出最重要的3-5个不重复事件，按以下格式输出：

        1. [事件标题] (来源网站域名)
           ○ 事件：[用1-2句话简洁描述事件核心内容]
           ○ 关键点：[列出2-3个最重要的关键信息点]

        2. [事件标题] (来源网站域名)
           ○ 事件：[用1-2句话简洁描述事件核心内容]  
           ○ 关键点：[列出2-3个最重要的关键信息点]

        [继续相同格式...]

        🎯 **筛选标准**：
        - **去重优先**：如果多个事件讲述同一件事，只选择信息最全面、来源最权威的一个
        - **影响力优先**：优先选择对{topic}行业影响最大的事件
        - **时效性优先**：优先选择最新发生的事件
        - **多样性保证**：避免所有事件都集中在同一个子领域
        - **信息完整性**：优先选择信息详细、具体的事件

        ⚠️ **重要提醒**：
        - 如果发现多个事件是关于同一件事的不同报道，请合并信息并只输出一个事件
        - 严格按照重要性排序，最重要的事件排在前面
        - 每个事件的描述控制在100-150字以内
        - 来源网站只写域名，不要完整URL
        - 不要添加额外的标题或说明文字
        """
        
        system_msg = f"""你是{topic}行业的专业信息整理专家，擅长将复杂信息提炼成简洁实用的摘要格式。请确保输出格式准确，内容简洁有用。"""
        
        try:
            if not self.llm_processor:
                return self._generate_fallback_events_summary_simple(topic, selected_news)
            
            summary_analysis = self.llm_processor.call_llm_api(summary_prompt, system_msg, max_tokens=6000)
            
            return f"### 一、重大新闻摘要与关键细节\n\n{summary_analysis}"
            
        except Exception as e:
            print(f"❌ [错误] 生成重大事件摘要时出错: {str(e)}")
            # 提供备用的简单摘要
            fallback_summary = self._generate_fallback_events_summary_simple(topic, selected_news)
            return f"### 一、重大新闻摘要与关键细节\n\n{fallback_summary}"
    
    def _generate_fallback_events_summary(self, topic, breaking_news):
        """备用的事件摘要生成方法（保留原格式，兼容性考虑）"""
        if not breaking_news:
            return "📊 **当前状况**: 暂无重大事件。"
        
        # 选择前5-7个事件
        selected_events = breaking_news[:min(7, len(breaking_news))]
        
        summary_text = f"📊 **事件概览**: 当前监测到{len(selected_events)}个{topic}行业重大事件\n\n"
        
        for i, event in enumerate(selected_events, 1):
            title = event.get('title', '未知事件')
            source = event.get('source', '未知来源')
            content = event.get('content', '无详细内容')[:200]
            
            summary_text += f"#### 🔥 事件{i}：{title}\n"
            summary_text += f"**📰 来源**: {source}\n"
            summary_text += f"**概述**: {content}...\n\n"
        
        return summary_text
    
    def _generate_fallback_events_summary_simple(self, topic, selected_news):
        """备用的简洁格式事件摘要生成方法"""
        if not selected_news:
            return "📊 **当前状况**: 在指定时间范围内暂无重大事件。"
        
        summary_text = ""
        
        for i, event in enumerate(selected_news, 1):
            title = event.get('title', '未知事件')
            source = event.get('source', '未知来源')
            content = event.get('content', '无详细内容')[:150]
            
            # 提取域名
            source_domain = source
            if 'http' in source.lower():
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(source)
                    source_domain = parsed.netloc or source
                except:
                    source_domain = source
            
            summary_text += f"{i}. {title} ({source_domain})\n"
            summary_text += f"   ○ 事件：{content}...\n"
            summary_text += f"   ○ 关键点：{topic}行业相关重要动态，需要持续关注。\n\n"
        
        return summary_text
    
    def _process_innovation_news_enhanced(self, topic, innovation_news):
        """增强版创新新闻处理"""
        if not innovation_news:
            return f"## 🔬 技术创新与新产品\n\n📊 **观察**: 当前时间窗口内{topic}行业技术创新活动相对平静。\n\n"
        
        print(f"🧪 [技术分析] 正在深度分析{len(innovation_news)}项技术创新...")
        
        all_news_text = "\n\n".join([
            f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
            for item in innovation_news
        ])
        
        enhanced_prompt = f"""
        作为{topic}行业的技术专家，请对以下技术创新进行智能筛选、去重和深度分析：
        
        {all_news_text}
        
        🔍 **智能筛选任务**：
        1. **去重识别**：识别相似或重复的技术创新报道，合并相同技术的不同报道
        2. **重要性评估**：评估每个技术创新的突破性和影响力
        3. **多样性保证**：确保涵盖不同技术领域和应用方向
        
        🔬 **技术分析框架**:
        1. **创新突破性评估**: 筛选出的技术的颠覆性程度如何？
        2. **技术成熟度分析**: 当前处于什么发展阶段？
        3. **商业化可行性**: 距离规模化应用还有多远？
        4. **竞争格局影响**: 对现有技术路线的冲击程度？
        5. **未来发展趋势**: 技术演进的可能方向？
        
        🤔 **分析师思考过程**:
        - 首先去除重复技术报道，保留信息最全面的版本
        - 然后评估技术的原创性和突破性
        - 接着分析技术的实用性和商业价值
        - 最后预测对行业生态的长远影响
        
        请提供客观、专业的技术解读，要求详细深入，字数1500-2000字。
         
         📝 **内容要求**:
         - 如果发现相同技术的多个报道，请合并信息只分析一次
         - 每个独特技术创新都要详细展开分析
         - 提供具体的技术细节和应用场景
         - 包含市场前景和商业化时间表
         - 分析技术的优势、局限性和发展瓶颈
         - 对比同类技术方案的差异
        """
        
        try:
            analysis = self.llm_processor.call_llm_api(enhanced_prompt, 
                f"你是{topic}行业的资深技术专家，具备深厚的技术洞察力", max_tokens=8000)
            
            sources = []
            for item in innovation_news:
                if item.get('url', '#') != '#':
                    sources.append(f"- [{item.get('title', '未知标题')}]({item.get('url')}) - {item.get('source', '未知来源')}")
            
            if sources:
                analysis += "\n\n**技术资料来源:**\n" + "\n".join(sources)
            
            return f"## 🔬 技术创新与新产品深度解析\n\n{analysis}\n\n"
            
        except Exception as e:
            print(f"❌ [错误] 生成技术创新分析时出错: {str(e)}")
            return f"## 🔬 技术创新与新产品\n\n技术分析暂时不可用。\n\n"
    
    def _process_investment_news_enhanced(self, topic, investment_news):
        """增强版投资新闻处理"""  
        if not investment_news:
            return f"## 💰 投资与市场动向\n\n📊 **市场观察**: {topic}行业投资活动在当前时段相对平静。\n\n"
        
        print(f"💰 [投资分析] 正在分析{len(investment_news)}个投资事件...")
        
        all_news_text = "\n\n".join([
            f"标题: {item.get('title', '无标题')}\n时间: {item.get('date', '未知日期')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
            for item in investment_news
        ])
        
        enhanced_prompt = f"""
        作为{topic}行业的投资分析专家，请对以下投资动态进行智能筛选、去重和深度解读：
        
        {all_news_text}
        
        🔍 **智能筛选任务**：
        1. **去重识别**：识别相同投资事件的不同报道，合并信息保留最完整版本
        2. **重要性评估**：评估每个投资事件的规模和影响力
        3. **多样性保证**：确保涵盖不同投资类型和细分领域
        
        💰 **投资分析框架**:
        1. **资本流向分析**: 资金主要投向哪些细分领域？
        2. **投资逻辑解读**: 投资方的战略考量是什么？
        3. **估值水平评估**: 当前估值是否合理？
        4. **市场信号解读**: 这些投资反映了什么市场趋势？
        5. **风险机遇并存**: 投资者应该关注什么？
        
        🤔 **投资分析师思考过程**:
        - 首先去除重复投资事件报道，合并相同事件的信息
        - 然后梳理独特投资事件的规模和性质
        - 接着分析投资背后的商业逻辑
        - 评估对行业格局的影响
        - 最后提出投资策略建议
        
        请提供专业的投资分析，注重数据支撑，字数2000-2500字。
         
         📝 **详细要求**:
         - 如果发现相同投资事件的多个报道，请合并信息只分析一次
         - 每个独特投资事件要单独分析，包含背景、动机、影响
         - 提供具体的投资金额、估值变化、投资方背景
         - 分析投资背后的战略布局和市场判断
         - 包含风险评估和收益预期分析
         - 对比历史投资案例，识别趋势变化
         - 提供具体的投资建议和时机判断
        """
        
        try:
            analysis = self.llm_processor.call_llm_api(enhanced_prompt, 
                f"你是{topic}行业的资深投资分析师，具备敏锐的市场洞察力", max_tokens=8000)
            
            sources = []
            for item in investment_news:
                if item.get('url', '#') != '#':
                    sources.append(f"- [{item.get('title', '未知标题')}]({item.get('url')}) - {item.get('source', '未知来源')}")
            
            if sources:
                analysis += "\n\n**投资资讯来源:**\n" + "\n".join(sources)
            
            return f"## 💰 投资与市场动向深度分析\n\n{analysis}\n\n"
            
        except Exception as e:
            print(f"❌ [错误] 生成投资分析时出错: {str(e)}")
            return f"## 💰 投资与市场动向\n\n投资分析暂时不可用。\n\n"
    
    def _process_policy_news_enhanced(self, topic, policy_news):
        """增强版政策新闻处理"""
        if not policy_news:
            return f"## 📜 政策与监管动态\n\n📊 **政策监测**: {topic}行业政策环境在当前时段保持稳定。\n\n"
        
        print(f"📜 [政策分析] 正在分析{len(policy_news)}项政策动态...")
        
        all_news_text = "\n\n".join([
            f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
            for item in policy_news
        ])
        
        enhanced_prompt = f"""
        作为{topic}行业的政策分析专家，请对以下政策动态进行智能筛选、去重和深度解读：
        
        {all_news_text}
        
        🔍 **智能筛选任务**：
        1. **去重识别**：识别相同政策的不同报道，合并信息保留最权威版本
        2. **重要性评估**：评估每项政策对{topic}行业的影响程度
        3. **多样性保证**：确保涵盖不同层级和类型的政策动态
        
        📜 **政策分析框架**:
        1. **政策内容解读**: 核心政策措施和规定是什么？
        2. **政策意图分析**: 政府希望达到什么目标？
        3. **行业影响评估**: 对{topic}行业各环节的具体影响？
        4. **企业应对策略**: 企业应该如何调整战略？
        5. **政策趋势预判**: 未来政策走向如何？
        
        🤔 **政策分析师思考过程**:
        - 首先去除重复政策报道，合并相同政策的信息
        - 然后理解独特政策的背景和目标
        - 接着分析政策的实施路径和时间节点
        - 评估对不同企业的差异化影响
        - 最后提出合规和发展建议
        
        请提供权威、客观的政策解读，字数1800-2200字。
         
         📝 **深度要求**:
         - 如果发现相同政策的多个报道，请合并信息只分析一次
         - 每项独特政策都要详细解读条文内容和实施细则
         - 分析政策出台的背景、目标和预期效果
         - 评估对不同类型企业的差异化影响
         - 提供具体的合规建议和操作指南
         - 预测政策执行过程中可能的挑战和机遇
         - 对比国际同类政策的经验和启示
        """
        
        try:
            analysis = self.llm_processor.call_llm_api(enhanced_prompt, 
                f"你是{topic}行业的政策分析专家，具备深厚的政策理解能力", max_tokens=8000)
            
            sources = []
            for item in policy_news:
                if item.get('url', '#') != '#':
                    sources.append(f"- [{item.get('title', '未知标题')}]({item.get('url')}) - {item.get('source', '未知来源')}")
            
            if sources:
                analysis += "\n\n**政策信息来源:**\n" + "\n".join(sources)
            
            return f"## 📜 政策与监管动态深度解读\n\n{analysis}\n\n"
            
        except Exception as e:
            print(f"❌ [错误] 生成政策分析时出错: {str(e)}")
            return f"## 📜 政策与监管动态\n\n政策分析暂时不可用。\n\n"
    
    def _process_industry_trends_enhanced(self, topic, trend_news, days=7):
        """增强版行业趋势处理"""
        if not trend_news:
            return f"## 📈 行业趋势深度分析\n\n📊 **趋势观察**: 基于最近{days}天的数据，{topic}行业趋势分析有限。\n\n"
        
        print(f"📈 [趋势分析] 正在综合分析{len(trend_news)}个行业趋势...")
        
        # 计算时间范围
        from datetime import datetime, timedelta
        today = datetime.now()
        start_date = today - timedelta(days=days)
        time_range = f"{start_date.strftime('%Y年%m月%d日')} 至 {today.strftime('%Y年%m月%d日')}"
        
        all_news_text = "\n\n".join([
            f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
            for item in trend_news
        ])
        
        enhanced_prompt = f"""
        作为{topic}行业的首席趋势分析师，请对以下**{time_range}**（最近{days}天）期间的行业趋势进行深度分析：
        
        {all_news_text}
        
        ⚠️ **时间范围限制**: 本分析严格聚焦于{time_range}这个时间窗口内的趋势信号，不涉及更早期的历史趋势。
        
        📈 **趋势分析框架**:
        1. **近期趋势识别**: 最近{days}天内{topic}行业出现了哪些新的发展趋势？
        2. **驱动因素分析**: 什么力量在推动这些最新趋势？
        3. **影响程度评估**: 这些新趋势对行业格局的即时和短期影响？
        4. **发展轨迹预测**: 基于近期信号，这些趋势的下一步发展方向？
        5. **机遇挑战并存**: 新趋势带来的即时机遇和风险？
        
        🤔 **趋势分析师思考过程**:
        - 首先从最新数据中识别趋势信号
        - 然后分析近期趋势之间的相互关系
        - 接着评估趋势的紧迫性和影响力
        - 最后基于最新变化预测短期发展轨迹
        
        请提供基于近期数据的前瞻性趋势分析，要有具体的数据支撑和案例说明，字数1500-2000字。
        
        📝 **分析要求**:
        - **严格聚焦时间范围**: 只分析{time_range}内的趋势信号
        - 构建基于最新数据的趋势分析框架
        - 每个趋势都要详细展开，包含最新驱动因素和发展阶段
        - 提供基于近期变化的具体预测和量化指标
        - 分析最新趋势之间的相互关系和协同效应
        - 识别潜在的新兴变化和突发因素
        - 构建基于当前状况的应对策略
        - 提供短期内的关键时间节点和发展路径
        
        🚫 **避免内容**: 
        - 不要引用{time_range}之外的历史趋势数据
        - 不要进行长期历史趋势的回顾分析
        - 专注于当前时间窗口内的具体趋势变化
        """
        
        try:
            analysis = self.llm_processor.call_llm_api(enhanced_prompt, 
                f"你是{topic}行业的资深趋势分析专家，具备卓越的前瞻性判断能力", max_tokens=8000)
            
            sources = []
            for item in trend_news:
                if item.get('url', '#') != '#':
                    sources.append(f"- [{item.get('title', '未知标题')}]({item.get('url')}) - {item.get('source', '未知来源')}")
            
            if sources:
                analysis += "\n\n**趋势数据来源:**\n" + "\n".join(sources)
            
            return f"## 📈 行业趋势深度分析\n\n{analysis}\n\n"
            
        except Exception as e:
            print(f"❌ [错误] 生成趋势分析时出错: {str(e)}")
            return f"## 📈 行业趋势深度分析\n\n趋势分析暂时不可用。\n\n"
    
    def _generate_intelligent_summary(self, topic, all_news_data, days=7):
        """生成智能总结，体现AI思考过程"""
        from datetime import datetime, timedelta
        
        # 计算时间范围
        today = datetime.now()
        start_date = today - timedelta(days=days)
        time_range = f"{start_date.strftime('%Y年%m月%d日')} 至 {today.strftime('%Y年%m月%d日')}"
        
        summary_prompt = f"""
        作为{topic}行业的AI智能分析师，我已经完成了针对**{time_range}**（最近{days}天）的全面信息收集和分析。
        现在需要提供一个体现深度思考的行业总结。
        
        ⚠️ **重要时间限制**: 本分析严格聚焦于{time_range}这个时间窗口内的信息，不涉及更早期的历史数据。
        
        🤔 **我的分析思路**:
        1. 首先识别了最近{days}天内行业的核心动态和变化
        2. 然后分析了这些近期事件和趋势之间的关联性  
        3. 接着评估了这些最新变化对行业未来的指向意义
        4. 最后形成了基于近期数据的综合性判断和建议
        
        📊 **数据基础**（最近{days}天）:
        - 重大事件: {len(all_news_data.get('breaking_news', []))}条
        - 技术创新: {len(all_news_data.get('innovation_news', []))}条
        - 投资动态: {len(all_news_data.get('investment_news', []))}条
        - 政策监管: {len(all_news_data.get('policy_news', []))}条
        - 行业趋势: {len(all_news_data.get('trend_news', []))}条
        - 观点对比: {len(all_news_data.get('perspective_analysis', []))}条
        
        请基于以上分析框架，提供一个800-1200字的智能总结，需要：
        1. **严格聚焦时间范围**: 只分析{time_range}内的信息和趋势
        2. 体现AI的完整分析思考过程和逻辑链条
        3. 突出关键洞察和判断，提供具体的数据支撑
        4. 提供基于近期变化的前瞻性建议和具体行动建议
        5. 保持客观和专业，同时体现深度思考
        6. 构建完整的战略建议框架
        7. 识别关键风险点和机遇窗口
        8. 提供不同情景下的应对策略
        
        🚫 **避免内容**: 
        - 不要引用{time_range}之外的历史数据或事件
        - 不要进行跨年度的长期趋势分析
        - 专注于当前时间窗口内的具体变化和影响
        """
        
        try:
            summary = self.llm_processor.call_llm_api(summary_prompt, 
                f"你是具备深度思考能力的{topic}行业AI分析师", max_tokens=8000)
            return f"## 🧠 AI智能分析总结\n\n{summary}\n\n"
        except Exception as e:
            print(f"❌ [错误] 生成智能总结时出错: {str(e)}")
            return f"## 🧠 AI智能分析总结\n\n{topic}行业正处于动态发展阶段，AI分析显示多个维度都有重要变化值得关注。\n\n"
    
    def _process_perspective_analysis_enhanced(self, topic, perspective_data):
        """处理观点对比分析"""
        if not perspective_data:
            return ""
        
        print(f"🔍 [观点分析] 正在分析{len(perspective_data)}条不同观点信息...")
        
        # 构建观点分析提示
        all_perspectives_text = "\n\n".join([
            f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
            for item in perspective_data
        ])
        
        enhanced_prompt = f"""
        作为{topic}行业的客观分析师，请对以下不同观点和争议性信息进行平衡分析：
        
        {all_perspectives_text}
        
        🎯 **观点对比分析框架**:
        1. **正面观点总结**: 支持性、乐观性的观点有哪些？
        2. **质疑声音汇总**: 批评、质疑、担忧的观点有哪些？
        3. **争议焦点识别**: 主要的分歧点在哪里？
        4. **不同立场分析**: 
           - 企业vs监管方
           - 投资者vs消费者
           - 国内vs国际视角
           - 学术界vs产业界
        5. **客观评估**: 基于现有证据，哪些观点更有说服力？
        6. **平衡建议**: 如何在不同观点间找到平衡？
        
        🤔 **分析师思考过程**:
        - 避免偏向任何一方，保持中立客观
        - 分析每种观点背后的利益考量和逻辑基础
        - 识别可能的信息偏差和局限性
        - 提供建设性的综合判断
        
        请提供客观、平衡的观点对比分析，字数控制在1500-2000字。
        
        📝 **对比分析要求**:
        - 每个重要观点都要客观呈现，不偏不倚
        - 分析观点背后的深层原因和动机
        - 识别不同观点的合理性和局限性
        - 提供基于事实的平衡判断
        - 避免绝对化表述，承认复杂性和不确定性
        - 为读者提供多元化思考角度
        """
        
        system_msg = f"""你是{topic}行业的资深客观分析师，具备：
        1. 中立客观的分析态度
        2. 多维度的思考能力  
        3. 平衡不同观点的技巧
        4. 深度的行业洞察力
        请展现出专业的客观分析能力。"""
        
        try:
            analysis = self.llm_processor.call_llm_api(enhanced_prompt, system_msg, max_tokens=8000)
            
            # 添加分析来源
            sources = []
            for item in perspective_data:
                if item.get('url', '#') != '#':
                    sources.append(f"- [{item.get('title', '未知标题')}]({item.get('url')}) - {item.get('source', '未知来源')}")
            
            if sources:
                analysis += "\n\n**观点来源:**\n" + "\n".join(sources)
            
            return f"## ⚖️ 多元观点对比分析\n\n{analysis}\n\n"
            
        except Exception as e:
            print(f"❌ [错误] 生成观点对比分析时出错: {str(e)}")
            return f"## ⚖️ 多元观点对比分析\n\n暂无{topic}行业的不同观点对比分析。\n\n"
    
    def _generate_references(self, all_news_data):
        """生成参考资料"""
        references = []
        
        for news_type in ["breaking_news", "innovation_news", "trend_news", "policy_news", "investment_news", "company_news"]:
            for item in all_news_data.get(news_type, []):
                title = item.get('title', '未知标题')
                url = item.get('url', '#')
                source = item.get('source', '未知来源') 
                if url != '#':
                    references.append(f"- [{title}]({url}) - {source}")
        
        unique_references = list(set(references))
        
        return f"\n## 📚 参考资料\n\n" + "\n".join(unique_references) + "\n"

# 原有函数的保留版本（为了兼容性）
def get_industry_news_comprehensive(topic, days=7, companies=None):
    """原有函数的保留版本"""
    agent = IntelligentReportAgent()
    return agent.generate_comprehensive_report_with_thinking(topic, days, companies)

def generate_news_report(topic, companies=None, days=7, output_file=None):
    """
    增强版报告生成函数，集成AI思考能力
    """
    print(f"\n🤖 启动智能报告生成系统...")
    print(f"🎯 目标: {topic}行业分析报告")
    print("=" * 60)
    
    # 使用智能代理生成报告
    agent = IntelligentReportAgent()
    report_data = agent.generate_comprehensive_report_with_thinking(topic, days, companies)
    
    # 获取报告内容
    report_content = report_data["content"]
    
    # 文件保存逻辑
    if not output_file:
        date_str = datetime.now().strftime('%Y%m%d')
        reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        safe_topic = "".join([c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in topic])
        safe_topic = safe_topic.replace(' ', '_')
        output_file = os.path.join(reports_dir, f"{safe_topic}_智能分析报告_{date_str}.md")
        print(f"📁 报告将保存至: {output_file}")
    
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    
    # 优化格式
    try:
        report_content = fix_markdown_headings(report_content)
        print("✅ 报告格式已优化")
    except Exception as e:
        print(f"⚠️ 修复Markdown格式时出错: {str(e)}")
    
    # 保存报告
    try:
        from report_utils import safe_save_report
        safe_save_report(report_content, output_file)
    except ImportError:
        print("📝 使用标准方式保存文件")
        with open(output_file, "w", encoding="utf-8-sig") as f:
            f.write(report_content)
    
    print(f"🎉 智能报告已生成: {output_file}")
    
    return report_content

# ==================== 原脚本重要函数保留区域 ====================
# 以下函数从原脚本保留，确保完整的功能支持

def process_breaking_news(llm_processor, topic, breaking_news):
    """处理行业重大新闻 - 原版保留"""
    if not breaking_news:
        return f"## 行业重大事件\n\n目前暂无{topic}行业的重大新闻。\n\n"
    
    all_news_text = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
        for item in breaking_news
    ])
    
    prompt = f"""
    请基于以下{topic}行业的最新重大新闻，提供简洁但全面的摘要，特别关注不同来源对同一事件的不同观点和解读。

    {all_news_text}
    
    请提供:
    1. 每条重大新闻的简要摘要，包括事件的关键细节
    2. 对不同来源的观点进行对比分析，突出观点差异和共识
    3. 对这些事件可能对{topic}行业产生的影响的多角度分析
    4. 相关企业、技术或市场的必要背景信息
    
    要求:
    - 保持客观，专注于事实
    - 按重要性排序
    - 特别关注可能改变行业格局的突发事件
    - 突出不同来源的观点差异，但保持中立立场
    - 对争议性话题进行多角度分析
         - 长度控制在2000-2500字
    """
    
    system = f"""你是一位权威的{topic}行业分析师，擅长从复杂信息中提取和总结最重要的行业事件与发展。
你特别注重对不同来源的观点进行对比分析，能够客观地呈现各方观点，并指出其中的共识与分歧。
你的分析应该保持中立，让读者能够全面了解事件的各个方面。"""
    
    try:
        breaking_news_summary = llm_processor.call_llm_api(prompt, system)
        
        news_sources = []
        for item in breaking_news:
            title = item.get('title', '未知标题')
            url = item.get('url', '#')
            source = item.get('source', '未知来源')
            if url != '#':
                news_sources.append(f"- [{title}]({url}) - {source}")
        
        if news_sources:
            breaking_news_summary += "\n\n**来源:**\n" + "\n".join(news_sources)
            
        return f"## 行业重大事件\n\n{breaking_news_summary}\n\n"
    except Exception as e:
        print(f"生成行业重大事件摘要时出错: {str(e)}")
        return f"## 行业重大事件\n\n暂无{topic}行业重大事件摘要。\n\n"

def process_innovation_news(llm_processor, topic, innovation_news):
    """处理技术创新新闻 - 原版保留"""
    if not innovation_news:
        return f"## 技术创新与新产品\n\n目前暂无{topic}行业的技术创新新闻。\n\n"
    
    all_news_text = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
        for item in innovation_news
    ])
    
    prompt = f"""
    请基于以下{topic}行业的最新技术创新和产品发布信息，提供综合分析，特别关注不同来源对同一技术或产品的不同评价和观点。

    {all_news_text}
    
    请提供:
    1. 主要技术突破和创新点的摘要
    2. 不同来源对同一技术/产品的评价对比分析
    3. 这些创新如何影响{topic}行业的发展方向的多角度解读
    4. 可能的市场反应和消费者采纳情况的不同预测
    5. 技术可行性和商业前景的争议点分析
    
    要求:
    - 专注于技术细节和创新点
    - 解释复杂概念时使用通俗易懂的语言
    - 分析创新的实际应用价值
    - 对比不同来源的观点，突出共识与分歧
    - 对争议性技术进行多角度分析
         - 长度控制在1800-2200字
    """
    
    system = f"""你是一位专精于{topic}领域技术的分析师，擅长评估技术创新的潜力和影响。
你特别注重对不同来源的技术评价进行对比分析，能够客观地呈现各方观点。
你的分析应该保持中立，让读者能够全面了解技术创新的各个方面，包括其优势和局限性。"""
    
    try:
        innovation_summary = llm_processor.call_llm_api(prompt, system)
        
        news_sources = []
        for item in innovation_news:
            title = item.get('title', '未知标题')
            url = item.get('url', '#')
            source = item.get('source', '未知来源')
            if url != '#':
                news_sources.append(f"- [{title}]({url}) - {source}")
        
        if news_sources:
            innovation_summary += "\n\n**来源:**\n" + "\n".join(news_sources)
            
        return f"## 技术创新与新产品\n\n{innovation_summary}\n\n"
    except Exception as e:
        print(f"生成技术创新摘要时出错: {str(e)}")
        return f"## 技术创新与新产品\n\n暂无{topic}行业技术创新摘要。\n\n"

def process_investment_news(llm_processor, topic, investment_news):
    """处理投资新闻 - 原版保留"""
    if not investment_news:
        return f"## 投资与市场动向\n\n目前暂无{topic}行业的投资相关新闻。\n\n"
    
    all_news_text = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n"
        f"时间: {item.get('date', '未知日期')}\n"
        f"内容: {item.get('content', '无内容')[:500]}...\n"
        f"来源: {item.get('source', '未知')}"
        for item in investment_news
    ])
    
    prompt = f"""
    请基于以下{topic}行业的最新投资、融资和市场变动信息，进行深度分析和解读。
    注意：请严格限制在提供的新闻时间范围内进行分析，不要引用或分析范围之外的历史数据。

    === 投资新闻数据 ===
    {all_news_text}
    
    请按以下框架进行详细分析：

    1. 最新投融资动态分析（占比35%）
    2. 当期投资热点分析（占比25%）
    3. 最新估值特征（占比20%）
    4. 风险提示（占比10%）
    5. 近期投资建议（占比10%）

    要求：
    1. 时效性：严格基于提供的新闻时间范围
    2. 准确性：只分析确定的信息，不做过度推测
    3. 完整性：确保分析框架完整
    4. 长度要求：1500-2000字
    """
    
    system = f"""你是一位专注于{topic}行业的资深投资分析师。"""
    
    try:
        investment_summary = llm_processor.call_llm_api(prompt, system, max_tokens=8000)
        
        news_sources = []
        for item in investment_news:
            title = item.get('title', '未知标题')
            url = item.get('url', '#')
            source = item.get('source', '未知来源')
            if url != '#':
                news_sources.append(f"- [{title} ({source}) - {url}")
        
        if news_sources:
            investment_summary += "\n\n**参考新闻来源:**\n" + "\n".join(sorted(news_sources))
            
        return f"## 投资与市场动向\n\n{investment_summary}\n\n"
    except Exception as e:
        print(f"生成投资分析摘要时出错: {str(e)}")
        return f"## 投资与市场动向\n\n暂无{topic}行业投资分析摘要。\n\n"

def process_industry_trends(llm_processor, topic, trend_news):
    """处理行业趋势新闻 - 原版保留"""
    if not trend_news:
        return f"## 行业趋势概览\n\n目前暂无{topic}行业的趋势分析。\n\n"
    
    all_news_text = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')[:500]}...\n来源: {item.get('source', '未知')}"
        for item in trend_news
    ])
    
    trend_prompt = f"""
    请基于以下{topic}行业的最新趋势相关新闻，分析并总结行业整体趋势和发展方向。

    {all_news_text}
    
    请提供详细的行业趋势分析，内容需要包括：
    1. {topic}行业的整体发展趋势和主要特征
    2. 市场规模、增长率和主要驱动因素的多角度分析
    3. 技术发展路线和创新焦点
    4. 值得关注的新技术、新产品或新模式
    5. 行业面临的挑战、机遇和潜在风险
    6. 区域发展差异和国际竞争格局
    7. 产业链上下游发展情况
    8. 对未来3-5年的预测和展望
    
    要求:
    - 使用专业、客观的语言
    - 提供具体数据和事实支持
    - 分析要深入且有洞察力
    - 使用小标题组织内容
    - 长度约1000-1200字
    """
    
    trend_system = f"""你是一位权威的{topic}行业趋势分析专家，拥有丰富的行业经验和深刻的洞察力。"""
    
    try:
        industry_trend = llm_processor.call_llm_api(trend_prompt, trend_system)
        
        news_sources = []
        for item in trend_news:
            title = item.get('title', '未知标题')
            url = item.get('url', '#')
            source = item.get('source', '未知来源')
            if url != '#':
                news_sources.append(f"- [{title}]({url}) - {source}")
        
        if news_sources:
            industry_trend += "\n\n**来源:**\n" + "\n".join(news_sources)
            
        return f"## 行业趋势深度分析\n\n{industry_trend}\n\n"
    except Exception as e:
        print(f"生成行业趋势分析时出错: {str(e)}")
        return f"## 行业趋势概览\n\n暂无{topic}行业趋势分析。\n\n"

def process_company_news(llm_processor, topic, company, news_items):
    """处理单个公司的新闻 - 原版保留"""
    if not news_items:
        return f"### {company}\n\n暂无{company}相关的最新动态。\n\n"
    
    news_text = "\n\n".join([
        f"标题: {item.get('title', '无标题')}\n内容: {item.get('content', '无内容')}\n链接: {item.get('url', '#')}"
        for item in news_items
    ])
    
    prompt = f"""
    请分析以下关于{company}公司的最新新闻报道，并撰写一份总结。
    
    {news_text}
    
    总结要求:
    1. 使用专业、客观的语言
    2. 保留关键事实和数据
    3. 按时间或重要性进行结构化组织
    4. 突出与{topic}行业相关的信息
    5. 长度控制在300-500字以内
    """
    
    system_message = f"你是一位专业的{topic}行业分析师。"
    
    try:
        summary = llm_processor.call_llm_api(prompt, system_message)
        
        news_sources = []
        for item in news_items:
            title = item.get('title', '未知标题')
            url = item.get('url', '#')
            source = item.get('source', '未知来源')
            if url != '#':
                news_sources.append(f"- [{title}]({url}) - {source}")
        
        if news_sources:
            summary += "\n\n**来源:**\n" + "\n".join(news_sources)
            
        return f"### {company}\n\n{summary}"
    except Exception as e:
        print(f"为 {company} 生成摘要时出错: {str(e)}")
        basic_content = "\n\n".join([f"- {item.get('title', '无标题')}" for item in news_items])
        return f"### {company}\n\n{basic_content}"

def process_policy_news(llm_processor, topic, policy_news):
    """处理政策监管动态 - 原版保留"""
    if not policy_news:
        return f"## 政策与监管动态\n\n目前暂无{topic}行业的政策相关新闻。\n\n"
    
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
    - 长度控制在1200-1500字
    """
    
    system = f"你是一位专精于{topic}行业政策分析的专家。"
    
    try:
        policy_summary = llm_processor.call_llm_api(prompt, system, max_tokens=8000)
        
        news_sources = []
        for item in policy_news:
            title = item.get('title', '未知标题')
            url = item.get('url', '#')
            source = item.get('source', '未知来源')
            if url != '#':
                news_sources.append(f"- [{title}]({url}) - {source}")
        
        if news_sources:
            policy_summary += "\n\n**来源:**\n" + "\n".join(news_sources)
            
        return f"## 政策与监管动态\n\n{policy_summary}\n\n"
    except Exception as e:
        print(f"生成政策分析摘要时出错: {str(e)}")
        return f"## 政策与监管动态\n\n暂无{topic}行业政策分析摘要。\n\n"

def generate_comprehensive_trend_summary(llm_processor, topic, all_news_data):
    """生成简短的行业趋势概况总结 - 原版保留"""
    
    prompt = f"""
    请针对上述已分析的{topic}行业各个方面，提供一个简短的总体概括和趋势总结。
    
    要求:
    1. 这是对已有内容的概括总结
    2. 长度控制在300-400字以内
    3. 使用简洁、专业的语言
    4. 突出核心趋势和对企业的建议
    """
    
    system = f"""你是一位{topic}行业资深分析师。"""
    
    try:
        summary = llm_processor.call_llm_api(prompt, system, max_tokens=4000)
        return f"## 行业趋势总结\n\n{summary}\n\n"
    except Exception as e:
        print(f"生成行业趋势总结时出错: {str(e)}")
        return f"## 行业趋势总结\n\n{topic}行业正处于快速发展阶段。\n\n"

if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='智能行业分析报告生成器')
    parser.add_argument('--topic', type=str, required=True, help='报告的主题')
    parser.add_argument('--companies', type=str, nargs='*', 
                      help='要特别关注的公司（可选）')
    parser.add_argument('--days', type=int, default=7, help='搜索内容的天数范围')
    parser.add_argument('--output', type=str, help='输出文件名或路径')
    
    parser.epilog = """
    🤖 智能报告生成器说明:
    
    本工具采用AI代理的五步分析法 + 多渠道搜索引擎：
    
    🔍 搜索渠道集成：
    - Brave Web Search API (隐私友好的搜索，已启用)  
    - Tavily Search API (AI优化的搜索)
    - Google Custom Search API (暂时注释，需要配置)
    - 自动去重和结果优化
    
    🧠 第一步：智能查询生成
    - 深度分析用户需求
    - 生成多维度搜索策略
    - 类似专业研究员的思考过程
    
    📊 第二步：多渠道信息搜集  
    - 同时使用多个搜索引擎
    - 提取高质量信息并去重
    - 确保信息相关性和权威性
    
    🤔 第三步：反思与知识缺口分析
    - 分析信息完整性
    - 识别知识空白点
    - 判断是否需要补充搜索
    
    🎯 第四步：迭代优化搜索
    - 生成针对性查询
    - 多渠道填补知识缺口
    - 最多迭代3轮确保质量
    
    📝 第五步：综合报告生成
    - 整合所有收集信息
    - 体现AI思考过程
    - 生成深度分析报告
    
    ⚙️ 环境配置:
    需要在.env文件中配置API密钥：
    - BRAVE_SEARCH_API_KEY (Brave搜索，已预配置)
    - TAVILY_API_KEY (Tavily搜索)
    - GOOGLE_SEARCH_API_KEY (Google搜索)
    - GOOGLE_SEARCH_CX (Google自定义搜索引擎ID)
    
    💡 使用示例:
    python generate_news_report_enhanced.py --topic "人工智能" --days 10 --output "AI智能分析报告.md"
    """
    
    args = parser.parse_args()
    
    print("🚀 启动智能报告生成...")
    generate_news_report(args.topic, args.companies, args.days, args.output) 