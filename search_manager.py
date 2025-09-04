#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索管理模块
统一管理所有搜索相关功能，包括多引擎并行搜索
"""

import json
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from collectors.web_content_collector import WebContentCollector

from config_manager import config_manager, apis, search_config


@dataclass
class SearchResult:
    """搜索结果数据结构"""
    title: str
    content: str
    url: str
    source: str
    category: str = ""
    published_date: str = ""
    relevance_score: float = 0.0


class SearchEngineManager:
    """搜索引擎管理器"""
    
    def __init__(self):
        self.search_available = False
        self.multi_search_available = False
        self.orchestrator = None
        self.multi_collectors = {}
        self.parallel_data_collector = None
        
        self._initialize_search_components()
        self._initialize_multi_collectors()
    
    def _initialize_search_components(self):
        """初始化搜索组件"""
        try:
            # 使用动态导入来避免模块路径问题
            import sys
            import importlib.util
            
            search_mcp_path = config_manager.paths.search_mcp_path
            config_file = search_mcp_path / 'search_mcp' / 'config.py'
            generators_file = search_mcp_path / 'search_mcp' / 'generators.py'
            
            print(f"🔍 尝试从路径导入: {search_mcp_path}")
            print(f"🔍 search_mcp目录存在: {search_mcp_path.exists()}")
            print(f"🔍 config.py文件存在: {config_file.exists()}")
            print(f"🔍 generators.py文件存在: {generators_file.exists()}")
            
            # 添加search_mcp路径到sys.path以支持相对导入
            search_mcp_src = str(search_mcp_path)
            if search_mcp_src not in sys.path:
                sys.path.insert(0, search_mcp_src)
            
            # 动态导入config模块
            config_spec = importlib.util.spec_from_file_location("search_mcp.config", config_file)
            config_module = importlib.util.module_from_spec(config_spec)
            sys.modules['search_mcp.config'] = config_module  # 注册到sys.modules
            config_spec.loader.exec_module(config_module)
            SearchConfig = config_module.SearchConfig
            
            # 导入models和logger模块以支持generators的依赖
            models_file = search_mcp_path / 'search_mcp' / 'models.py'
            logger_file = search_mcp_path / 'search_mcp' / 'logger.py'
            
            models_spec = importlib.util.spec_from_file_location("search_mcp.models", models_file)
            models_module = importlib.util.module_from_spec(models_spec)
            sys.modules['search_mcp.models'] = models_module
            models_spec.loader.exec_module(models_module)
            
            logger_spec = importlib.util.spec_from_file_location("search_mcp.logger", logger_file)
            logger_module = importlib.util.module_from_spec(logger_spec)
            sys.modules['search_mcp.logger'] = logger_module
            logger_spec.loader.exec_module(logger_module)
            
            # 动态导入generators模块
            generators_spec = importlib.util.spec_from_file_location("search_mcp.generators", generators_file)
            generators_module = importlib.util.module_from_spec(generators_spec)
            sys.modules['search_mcp.generators'] = generators_module  # 注册到sys.modules
            generators_spec.loader.exec_module(generators_module)
            SearchOrchestrator = generators_module.SearchOrchestrator
            
            config = SearchConfig()
            print(f"🔍 配置创建成功，API密钥状态: {config.get_api_keys()}")
            
            self.orchestrator = SearchOrchestrator(config)
            self.search_available = True
            print(f"✅ 搜索组件初始化成功，可用数据源: {config.get_enabled_sources()}")
            
        except Exception as e:
            print(f"⚠️ 搜索组件初始化失败: {e}")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   搜索组件路径: {config_manager.paths.search_mcp_path}")
            import traceback
            traceback.print_exc()
            
            self.orchestrator = None
            self.search_available = False
    
    def _initialize_multi_collectors(self):
        """初始化多搜索引擎收集器"""
        try:
            from collectors.tavily_collector import TavilyCollector
            from collectors.google_search_collector import GoogleSearchCollector
            from collectors.brave_search_collector import BraveSearchCollector
            
            # 初始化Tavily收集器（默认启用）
            self.multi_collectors = {
                'tavily': TavilyCollector(),
            }
            
            # 尝试初始化Google搜索收集器
            try:
                google_collector = GoogleSearchCollector()
                if google_collector.has_api_key:
                    self.multi_collectors['google'] = google_collector
                    print("✅ Google搜索收集器已启用")
                else:
                    print("⚠️ Google搜索收集器未配置API密钥，已跳过")
            except Exception as e:
                print(f"⚠️ Google搜索收集器不可用: {str(e)}")
            
            # 尝试初始化Brave搜索收集器
            try:
                brave_collector = BraveSearchCollector()
                if brave_collector.has_api_key:
                    self.multi_collectors['brave'] = brave_collector
                    print("✅ Brave搜索收集器已启用")
                else:
                    print("⚠️ Brave搜索收集器未配置API密钥，已跳过")
            except Exception as e:
                print(f"⚠️ Brave搜索收集器不可用: {str(e)}")
            
            self.multi_search_available = True
            print(f"🔍 已启用 {len(self.multi_collectors)} 个搜索渠道: {', '.join(self.multi_collectors.keys())}")
            
            # 初始化并行数据收集器
            if self.multi_search_available:
                self.parallel_data_collector = ParallelDataCollector(self.multi_collectors)
                print("🚀 并行数据收集器已初始化")
            
        except Exception as e:
            self.multi_collectors = {}
            self.multi_search_available = False
            self.parallel_data_collector = None
            print(f"⚠️ 多搜索引擎收集器初始化失败: {str(e)}")
    
    def reinitialize_search(self):
        """重新初始化搜索服务"""
        if not self.search_available:
            try:
                from search_mcp.config import SearchConfig
                from search_mcp.generators import SearchOrchestrator
                
                config = SearchConfig()
                self.orchestrator = SearchOrchestrator(config)
                self.search_available = True
                print(f"🔄 搜索服务重新初始化成功，可用数据源: {config.get_enabled_sources()}")
                return True
                
            except Exception as e:
                print(f"❌ 搜索服务重新初始化失败: {str(e)}")
                return False
        return True
    
    def get_available_engines(self) -> List[str]:
        """获取可用的搜索引擎列表"""
        engines = []
        if self.search_available and self.orchestrator:
            engines.append('search_mcp')
        if self.multi_search_available:
            engines.extend(list(self.multi_collectors.keys()))
        return engines
    
    def get_status(self) -> Dict[str, Any]:
        """获取搜索管理器状态"""
        return {
            'search_available': self.search_available,
            'multi_search_available': self.multi_search_available,
            'enabled_collectors': list(self.multi_collectors.keys()),
            'parallel_collector_available': self.parallel_data_collector is not None,
            'api_status': apis.validate_search_apis()
        }


class ParallelDataCollector:
    """并行数据收集器"""
    
    def __init__(self, collectors_dict):
        self.collectors = collectors_dict
        print(f"🚀 并行数据收集器初始化，支持 {len(collectors_dict)} 个搜索引擎")
    
    def parallel_comprehensive_search(self, topic, days=7, max_workers=3):
        """并行综合搜索"""
        print(f"🎯 开始对'{topic}'进行多引擎并行综合搜索，时间范围：最近{days}天")
        
        # 使用AI生成分类查询
        categorized_queries = query_generator.generate_intelligent_queries(topic, days)
        
        merged_data = {
            "breaking_news": [],
            "innovation_news": [],
            "investment_news": [],
            "policy_news": [],
            "trend_news": [],
            "company_news": []
        }
        
        seen_urls = set()
        results_lock = threading.Lock()
        
        def execute_collector_search(collector_name, collector):
            """执行单个收集器的搜索"""
            try:
                print(f"  🔍 [{collector_name}] 开始搜索...")
                collector_data = {category: [] for category in merged_data.keys()}

                for query_item in categorized_queries:
                    query = query_item["query"]
                    category = query_item["category"]
                    
                    if category not in collector_data:
                        continue

                    try:
                        if collector_name == 'tavily':
                            results = collector.search(query, max_results=3)
                        elif collector_name == 'google':
                            results = collector.search(query, max_results=3)
                        elif collector_name == 'brave':
                            results = collector.search(query, count=3)
                        else:
                            continue
                        
                        if results:
                            for result in results:
                                if isinstance(result, dict):
                                    result['category'] = category
                                    result['search_source'] = collector_name
                                    collector_data[category].append(result)

                    except Exception as e:
                        print(f"    ⚠️ [{collector_name}] 查询 '{query}' 失败: {str(e)}")
                
                print(f"  ✅ [{collector_name}] 搜索完成")
                return collector_name, collector_data
                
            except Exception as e:
                print(f"  ❌ [{collector_name}] 搜索失败: {str(e)}")
                return collector_name, {}
        
        # 并行执行所有收集器
        with ThreadPoolExecutor(max_workers=min(len(self.collectors), max_workers)) as executor:
            future_to_collector = {
                executor.submit(execute_collector_search, name, collector): name
                for name, collector in self.collectors.items()
            }
            
            for future in as_completed(future_to_collector):
                collector_name = future_to_collector[future]
                try:
                    returned_name, collector_data = future.result()
                    
                    # 线程安全的数据合并
                    with results_lock:
                        self._merge_collector_data(merged_data, collector_data, seen_urls, returned_name)
                        
                except Exception as e:
                    print(f"  ❌ [{collector_name}] 处理结果失败: {str(e)}")
        
        # 计算总数
        total_count = sum(len(merged_data[category]) for category in merged_data.keys())
        merged_data["total_count"] = total_count
        
        print(f"🎯 多引擎并行综合搜索完成，总计 {total_count} 条结果")

        # Enrich results with full content
        print("🌐 开始抓取网页全文内容...")
        web_collector = WebContentCollector()
        
        all_results_to_enrich = []
        for category in merged_data:
            if category != "total_count" and isinstance(merged_data[category], list):
                all_results_to_enrich.extend(merged_data[category])
        
        if all_results_to_enrich:
            enriched_results = web_collector.enrich_search_results(all_results_to_enrich)
            
            # Re-organize enriched results back into categories
            enriched_merged_data = {key: [] for key in merged_data if key != "total_count"}
            
            for result in enriched_results:
                category = result.get('category')
                if category and category in enriched_merged_data:
                    enriched_merged_data[category].append(result)
            
            # Update merged_data with enriched content
            for category in enriched_merged_data:
                merged_data[category] = enriched_merged_data[category]
                
            print(f"✅ 网页全文内容抓取完成，共处理 {len(enriched_results)} 条结果")

        return merged_data
    
    def parallel_targeted_search(self, queries, topic, max_workers=4):
        """并行针对性搜索"""
        print(f"🎯 开始对{len(queries)}个查询进行多引擎并行针对性搜索")
        
        additional_data = {
            'perspective_analysis': [],
            'investment_news': [],
            'policy_news': [],
            'innovation_news': [],
            'trend_news': [],
            'breaking_news': []
        }
        
        seen_urls = set()
        results_lock = threading.Lock()
        
        def execute_single_query(query):
            """执行单个查询的搜索"""
            try:
                print(f"  🔍 执行查询: {query[:50]}...")
                query_results = []
                
                # 对每个收集器执行查询
                for collector_name, collector in self.collectors.items():
                    try:
                        if collector_name == 'tavily':
                            results = collector.search(query, max_results=3, days=7)
                        elif collector_name == 'google':
                            results = collector.search(query, max_results=3)
                        elif collector_name == 'brave':
                            results = collector.search(query, count=3)
                        else:
                            continue
                        
                        if results:
                            for result in results:
                                if isinstance(result, dict):
                                    result['search_source'] = collector_name
                                    result['query'] = query
                                    query_results.append(result)
                    
                    except Exception as e:
                        print(f"    ⚠️ [{collector_name}] 查询失败: {str(e)}")
                
                print(f"  ✅ 查询完成，获得 {len(query_results)} 条结果")
                return query, query_results
                
            except Exception as e:
                print(f"  ❌ 查询执行失败: {str(e)}")
                return query, []
        
        # 并行执行所有查询
        with ThreadPoolExecutor(max_workers=min(len(queries), max_workers)) as executor:
            future_to_query = {
                executor.submit(execute_single_query, query): query
                for query in queries
            }
            
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    returned_query, query_results = future.result()
                    
                    # 线程安全的数据分类和合并
                    with results_lock:
                        for result in query_results:
                            category = self._categorize_search_result(returned_query, topic)
                            if category in additional_data:
                                url = result.get('url', '')
                                if url and url not in seen_urls:
                                    seen_urls.add(url)
                                    additional_data[category].append(result)
                        
                except Exception as e:
                    print(f"  ❌ [{query}] 处理结果失败: {str(e)}")
        
        total_count = sum(len(v) for v in additional_data.values())
        print(f"🎯 多引擎并行针对性搜索完成，总计 {total_count} 条结果")
        return additional_data
    
    
    def _categorize_search_result(self, query, topic):
        """对搜索结果进行分类"""
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['breaking', '突发', '重大', 'major', 'urgent']):
            return 'breaking_news'
        elif any(keyword in query_lower for keyword in ['investment', '投资', '融资', 'funding', 'acquisition']):
            return 'investment_news'
        elif any(keyword in query_lower for keyword in ['policy', '政策', '监管', 'regulation', 'compliance']):
            return 'policy_news'
        elif any(keyword in query_lower for keyword in ['innovation', '创新', '技术', 'technology', 'breakthrough']):
            return 'innovation_news'
        elif any(keyword in query_lower for keyword in ['trend', '趋势', '发展', 'development', 'outlook']):
            return 'trend_news'
        else:
            return 'perspective_analysis'
    
    def _merge_collector_data(self, merged_data, collector_data, seen_urls, collector_name):
        """合并收集器数据"""
        added_count = 0
        
        for category, items in collector_data.items():
            if category in merged_data and items:
                for item in items:
                    url = item.get('url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        merged_data[category].append(item)
                        added_count += 1
        
        print(f"  📊 [{collector_name}] 新增 {added_count} 条去重数据")


class SearchQueryGenerator:
    """搜索查询生成器"""
    
    @staticmethod
    def generate_intelligent_queries(topic: str, days: int = 7, context: str = "") -> List[Dict[str, str]]:
        """生成智能搜索查询"""
        try:
            from collectors.llm_processor import LLMProcessor
            llm = LLMProcessor()
            
            today = datetime.now()
            intelligent_prompt = f"""
            你是一个专业的{topic}行业研究分析师。请为"{topic}"领域生成8-10个高质量的搜索查询，用于收集最近{days}天的重要信息。

            要求：
            1. 查询应涵盖以下5个核心维度，并为每个查询指定对应的类别：
               - 重大新闻事件 (breaking_news)
               - 技术创新突破 (innovation_news) 
               - 投资融资动态 (investment_news)
               - 政策监管变化 (policy_news)
               - 行业发展趋势 (trend_news)

            2. 查询特点：
               - 包含时间限定词（最近、{today.year}年、{days}天内等）
               - 结合中英文关键词提高覆盖率
               - 针对{topic}领域的专业术语
               - 关注突发性、重要性、影响力大的事件

            3. 输出格式：
               返回一个JSON对象，其中包含一个名为 "queries" 的数组。数组中的每个对象都应包含 "query" 和 "category" 两个字段。
               
            示例输出：
            {{
                "queries": [
                    {{
                        "query": "{topic} 重大突破 {today.year}年 最新 breakthrough major development",
                        "category": "innovation_news"
                    }},
                    {{
                        "query": "{topic} 投资 融资 并购 {today.year}年 最近{days}天 investment funding acquisition",
                        "category": "investment_news"
                    }}
                ]
            }}

            上下文信息：{context}
            
            请生成查询：
            """
            
            response = llm.call_llm_api(
                prompt=intelligent_prompt,
                system_message=f"你是{topic}领域的专业分析师，擅长生成高质量的搜索查询。",
                max_tokens=1500,
                temperature=0.7
            )
            
            if response:
                import re
                json_match = re.search(r'\{\s*"queries":\s*\[.*?\]\s*\}', response, re.DOTALL)
                if json_match:
                    queries_json = json_match.group()
                    queries_data = json.loads(queries_json)
                    queries = queries_data.get("queries", [])
                    if queries:
                        print(f"🤖 [AI查询生成] 成功生成{len(queries)}个智能查询")
                        return queries
        
        except Exception as e:
            print(f"⚠️ [AI查询生成失败] {str(e)}")
        
        # 备用预设查询策略
        print(f"🔍 [备用策略] 使用预设{topic}查询模板")
        today = datetime.now()
        fallback_queries = [
            {{"query": f"{topic} 重大事件 突发 {today.year}年 最新 breaking news major event", "category": "breaking_news"}},
            {{"query": f"{topic} 技术创新 突破 {today.year}年 最近{days}天 innovation breakthrough technology", "category": "innovation_news"}},
            {{"query": f"{topic} 投资 融资 并购 {today.year}年 最新 investment funding acquisition merger", "category": "investment_news"}},
            {{"query": f"{topic} 政策 监管 法规 {today.year}年 最新 policy regulation compliance", "category": "policy_news"}},
            {{"query": f"{topic} 发展趋势 前景 {today.year}年 最新 trend development future outlook", "category": "trend_news"}},
            {{"query": f"{topic} 行业震动 重磅消息 {today.year}年 最近{days}天 industry shock major news", "category": "breaking_news"}},
            {{"query": f"{topic} 市场变化 动态 {today.year}年 最新 market change dynamics", "category": "trend_news"}},
            {{"query": f"{topic} 竞争格局 领先企业 {today.year}年 最新 competition landscape leading companies", "category": "company_news"}}
        ]
        
        return fallback_queries


# 全局搜索管理器实例
search_manager = SearchEngineManager()

# 便捷访问
parallel_collector = search_manager.parallel_data_collector
query_generator = SearchQueryGenerator()

if __name__ == "__main__":
    # 打印搜索管理器状态
    status = search_manager.get_status()
    print("\n🔍 搜索管理器状态报告:")
    print(f"   🔍 基础搜索: {'✅' if status['search_available'] else '❌'}")
    print(f"   🚀 多引擎搜索: {'✅' if status['multi_search_available'] else '❌'}")
    print(f"   📦 启用收集器: {', '.join(status['enabled_collectors']) if status['enabled_collectors'] else '无'}")
    print(f"   ⚡ 并行收集器: {'✅' if status['parallel_collector_available'] else '❌'}")
else:
    print("✅ 搜索管理器初始化完成")