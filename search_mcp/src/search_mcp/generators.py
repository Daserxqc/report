"""
Search MCP 核心搜索生成器

参考绘本生成模块的架构，创建各种搜索Agent类
"""

import asyncio
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union, Any, Tuple
from pathlib import Path
import sys
import json

# 导入配置和模型
from .config import SearchConfig
from .models import Document, SearchResult, SearchMetrics, CollectorInfo
from .logger import SearchLogger

# 添加父目录到路径以导入现有收集器
parent_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(parent_dir))

# 导入现有的收集器
try:
    from collectors.tavily_collector import TavilyCollector
    from collectors.brave_search_collector import BraveSearchCollector  
    from collectors.google_search_collector import GoogleSearchCollector
    from collectors.arxiv_collector import ArxivCollector
    from collectors.academic_collector import AcademicCollector
    from collectors.news_collector import NewsCollector
except ImportError as e:
    print(f"⚠️ 导入收集器失败: {e}")
    # 创建空类以防导入失败
    class TavilyCollector: pass
    class BraveSearchCollector: pass
    class GoogleSearchCollector: pass
    class ArxivCollector: pass
    class AcademicCollector: pass
    class NewsCollector: pass


class BaseSearchAgent:
    """
    封装搜索相关操作的基础Agent类
    所有具体的搜索Agent都继承自此类
    """
    
    def __init__(self, config: SearchConfig):
        """
        初始化基础搜索Agent
        
        Args:
            config (SearchConfig): 搜索配置实例
        """
        self.config = config
        self.logger = SearchLogger(config.to_dict())
        self.results_lock = threading.Lock()
        
    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """解析日期字符串为datetime对象"""
        if not date_str:
            return datetime.min
        
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except:
                return datetime.min
    
    def _extract_publish_date(self, result: Dict) -> Optional[str]:
        """提取发布日期"""
        date_fields = ['publish_date', 'published', 'date', 'year', 'publication_date']
        
        for field in date_fields:
            if field in result and result[field]:
                date_value = result[field]
                
                # 如果是年份整数
                if isinstance(date_value, int):
                    return f"{date_value}-01-01"
                
                # 如果是字符串，尝试解析
                if isinstance(date_value, str):
                    try:
                        # 尝试解析ISO格式日期
                        parsed_date = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                        return parsed_date.strftime('%Y-%m-%d')
                    except:
                        return date_value
        
        return None
    
    def _determine_source_type(self, source: str, result: Dict) -> str:
        """确定数据源类型"""
        if source in ['arxiv', 'academic']:
            return 'academic'
        elif source == 'news' or 'news' in source:
            return 'news'
        else:
            return 'web'


class CollectorInitializationAgent(BaseSearchAgent):
    """负责初始化和管理各种数据收集器的Agent"""
    
    def __init__(self, config: SearchConfig):
        super().__init__(config)
        self.collectors = {}
        self.source_types = {
            'web': ['tavily', 'brave', 'google'],
            'academic': ['arxiv', 'academic', 'semantic_scholar', 'ieee', 'springer', 'core'],
            'news': ['news_api', 'google_news', 'brave_news', 'rss']
        }
        self.initialize_all_collectors()
    
    def initialize_all_collectors(self):
        """初始化所有可用的收集器"""
        self.logger.logger.info("🔧 开始初始化数据收集器...")
        
        # Web搜索收集器
        self._init_web_collectors()
        
        # 学术搜索收集器  
        self._init_academic_collectors()
        
        # 新闻收集器
        self._init_news_collectors()
        
        self.logger.logger.info(f"✅ 收集器初始化完成，可用收集器: {list(self.collectors.keys())}")
    
    def _init_web_collectors(self):
        """初始化Web搜索收集器"""
        # Tavily收集器
        if self.config.has_api_key('tavily'):
            try:
                tavily = TavilyCollector()
                if hasattr(tavily, 'has_api_key') and tavily.has_api_key:
                    self.collectors['tavily'] = tavily
                    self.logger.logger.info("✅ Tavily收集器已启用")
            except Exception as e:
                self.logger.logger.error(f"⚠️ Tavily收集器初始化失败: {str(e)}")
        
        # Brave收集器
        if self.config.has_api_key('brave'):
            try:
                brave = BraveSearchCollector()
                if hasattr(brave, 'has_api_key') and brave.has_api_key:
                    self.collectors['brave'] = brave
                    self.logger.logger.info("✅ Brave收集器已启用")
            except Exception as e:
                self.logger.logger.error(f"⚠️ Brave收集器初始化失败: {str(e)}")
        
        # Google收集器
        if self.config.has_api_key('google') and getattr(self.config, 'GOOGLE_SEARCH_ENABLED', True):
            try:
                google = GoogleSearchCollector()
                if hasattr(google, 'has_api_key') and google.has_api_key:
                    self.collectors['google'] = google
                    self.logger.logger.info("✅ Google收集器已启用")
            except Exception as e:
                self.logger.logger.error(f"⚠️ Google收集器初始化失败: {str(e)}")
        else:
            self.logger.logger.info("⚠️ Google收集器已禁用")
    
    def _init_academic_collectors(self):
        """初始化学术搜索收集器"""
        # ArXiv收集器（无需API密钥）
        try:
            arxiv = ArxivCollector()
            self.collectors['arxiv'] = arxiv
            self.logger.logger.info("✅ ArXiv收集器已启用")
        except Exception as e:
            self.logger.logger.error(f"⚠️ ArXiv收集器初始化失败: {str(e)}")
        
        # Academic收集器（无需API密钥）
        try:
            academic = AcademicCollector()
            self.collectors['academic'] = academic
            self.logger.logger.info("✅ Academic收集器已启用")
        except Exception as e:
            self.logger.logger.error(f"⚠️ Academic收集器初始化失败: {str(e)}")
    
    def _init_news_collectors(self):
        """初始化新闻收集器"""
        if self.config.has_api_key('news'):
            try:
                news = NewsCollector()
                self.collectors['news'] = news
                self.logger.logger.info("✅ News收集器已启用")
            except Exception as e:
                self.logger.logger.error(f"⚠️ News收集器初始化失败: {str(e)}")
    
    def get_available_sources(self) -> Dict[str, List[str]]:
        """获取所有可用的数据源"""
        available = {}
        for category, sources in self.source_types.items():
            available[category] = [s for s in sources if s in self.collectors]
        return available
    
    def get_collector_info(self) -> List[CollectorInfo]:
        """获取所有收集器的信息"""
        info_list = []
        all_sources = ['tavily', 'brave', 'google', 'arxiv', 'academic', 'news']
        
        for source in all_sources:
            is_available = source in self.collectors
            api_key_required = source not in ['arxiv', 'academic']
            has_api_key = self.config.has_api_key(source)
            
            # 确定数据源类型
            source_type = 'web'
            if source in ['arxiv', 'academic']:
                source_type = 'academic'
            elif source == 'news':
                source_type = 'news'
            
            info = CollectorInfo(
                name=source,
                source_type=source_type,
                is_available=is_available,
                api_key_required=api_key_required,
                has_api_key=has_api_key,
                description=f"{source.title()}搜索收集器"
            )
            
            info_list.append(info)
        
        return info_list


class SearchExecutionAgent(BaseSearchAgent):
    """负责执行具体搜索操作的Agent"""
    
    def __init__(self, config: SearchConfig, collectors: Dict):
        super().__init__(config)
        self.collectors = collectors
    
    def execute_single_search(self, query: str, source: str, max_results: int, days_back: int) -> List[Document]:
        """执行单个搜索任务"""
        collector = self.collectors.get(source)
        if not collector:
            return []
        
        try:
            # 根据不同的收集器调用相应的搜索方法
            raw_results = []
            
            if source == 'tavily':
                if hasattr(collector, 'search'):
                    raw_results = collector.search(query, max_results=max_results)
                
            elif source == 'brave':
                if hasattr(collector, 'search'):
                    raw_results = collector.search(query, count=max_results)
                
            elif source == 'google':
                if hasattr(collector, 'search'):
                    raw_results = collector.search(query, days_back=days_back, max_results=max_results)
                
            elif source == 'arxiv':
                if hasattr(collector, 'search'):
                    raw_results = collector.search(query, days_back=days_back)
                
            elif source == 'academic':
                # Academic收集器有多个方法，这里使用Semantic Scholar
                if hasattr(collector, 'search_semantic_scholar'):
                    raw_results = collector.search_semantic_scholar(query, days_back=days_back)
                
            elif source == 'news':
                if hasattr(collector, 'search_news_api'):
                    raw_results = collector.search_news_api(query, days_back=days_back)
            
            # 标准化结果为Document格式
            documents = self.standardize_results(raw_results, source)
            
            return documents[:max_results]  # 限制结果数量
            
        except Exception as e:
            self.logger.logger.error(f"搜索执行失败 {source}({query}): {str(e)}")
            return []
    
    def standardize_results(self, raw_results: List[Dict], source: str) -> List[Document]:
        """将原始搜索结果标准化为Document格式"""
        documents = []
        
        for result in raw_results:
            try:
                # 确定数据源类型
                source_type = self._determine_source_type(source, result)
                
                # 提取标准字段
                title = result.get('title', 'Untitled')
                
                # 内容字段可能有多种名称
                content = (result.get('content') or 
                          result.get('summary') or 
                          result.get('abstract') or 
                          result.get('snippet') or 
                          result.get('description') or '')
                
                url = result.get('url', '#')
                
                # 作者处理
                authors = []
                if 'authors' in result:
                    if isinstance(result['authors'], list):
                        authors = result['authors']
                    elif isinstance(result['authors'], str):
                        authors = [result['authors']]
                
                # 发布日期处理
                publish_date = self._extract_publish_date(result)
                
                # 期刊/会议名称
                venue = result.get('venue') or result.get('source')
                
                # 创建Document对象
                doc = Document(
                    title=title,
                    content=content,
                    url=url,
                    source=source,
                    source_type=source_type,
                    publish_date=publish_date,
                    authors=authors,
                    venue=venue,
                    score=result.get('score'),
                    language=result.get('language')
                )
                
                documents.append(doc)
                
            except Exception as e:
                self.logger.logger.error(f"标准化结果失败: {str(e)}")
                continue
        
        return documents


class ParallelSearchAgent(BaseSearchAgent):
    """负责并行搜索执行和结果聚合的Agent"""
    
    def __init__(self, config: SearchConfig, collectors: Dict, execution_agent: SearchExecutionAgent):
        super().__init__(config)
        self.collectors = collectors
        self.execution_agent = execution_agent
    
    def parallel_search(self, 
                       queries: List[str], 
                       sources: List[str] = None, 
                       max_results_per_query: int = 5,
                       days_back: int = 7,
                       max_workers: int = 6) -> List[Document]:
        """
        并行搜索多个查询和数据源
        """
        start_time = time.time()
        
        if not queries:
            return []
        
        # 如果没有指定数据源，使用所有可用的
        if sources is None:
            sources = list(self.collectors.keys())
        else:
            # 过滤只保留可用的数据源
            sources = [s for s in sources if s in self.collectors]
        
        if not sources:
            self.logger.logger.error("❌ 没有可用的数据源")
            return []
        
        # 记录搜索开始
        self.logger.log_search_start(queries, sources, {
            'max_results_per_query': max_results_per_query,
            'days_back': days_back,
            'max_workers': max_workers
        })
        
        all_results = []
        seen_urls = set()
        
        # 使用线程池并行执行搜索
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 为每个查询和数据源组合创建任务
            future_to_info = {}
            
            for query in queries:
                for source in sources:
                    if source in self.collectors:
                        future = executor.submit(
                            self.execution_agent.execute_single_search,
                            query, source, max_results_per_query, days_back
                        )
                        future_to_info[future] = (query, source)
            
            # 收集结果
            completed_tasks = 0
            total_tasks = len(future_to_info)
            errors = []
            
            for future in as_completed(future_to_info):
                query, source = future_to_info[future]
                completed_tasks += 1
                
                try:
                    results = future.result()
                    
                    # 去重并合并结果
                    new_count = 0
                    for doc in results:
                        if doc.url not in seen_urls:
                            seen_urls.add(doc.url)
                            all_results.append(doc)
                            new_count += 1
                    
                    # 记录单个源的结果
                    self.logger.log_source_result(source, query, len(results), True)
                    self.logger.logger.info(f"  ✅ [{completed_tasks}/{total_tasks}] {source}({query}): {len(results)}条结果, {new_count}条新增")
                    
                except Exception as e:
                    error_msg = f"{source}({query}) 搜索失败: {str(e)}"
                    errors.append(error_msg)
                    self.logger.log_source_result(source, query, 0, False, str(e))
                    self.logger.logger.error(f"  ❌ [{completed_tasks}/{total_tasks}] {error_msg}")
        
        # 按相关性和时间排序
        all_results.sort(key=lambda doc: (
            doc.score or 0,  # 相关性评分
            self._parse_date(doc.publish_date) if doc.publish_date else datetime.min
        ), reverse=True)
        
        total_time = time.time() - start_time
        
        # 记录搜索完成
        self.logger.log_search_complete(len(all_results), total_time, sources, errors)
        
        return all_results
    
    def search_by_category(self, 
                          queries: List[str], 
                          category: str = 'web',
                          max_results_per_query: int = 5,
                          days_back: int = 7,
                          max_workers: int = 4) -> List[Document]:
        """
        按类别搜索
        """
        source_types = {
            'web': ['tavily', 'brave', 'google'],
            'academic': ['arxiv', 'academic', 'semantic_scholar', 'ieee', 'springer', 'core'],
            'news': ['news_api', 'google_news', 'brave_news', 'rss']
        }
        
        if category not in source_types:
            raise ValueError(f"不支持的搜索类别: {category}")
        
        # 获取该类别下的可用数据源
        sources = [s for s in source_types[category] if s in self.collectors]
        
        if not sources:
            self.logger.logger.error(f"❌ 类别 {category} 下没有可用的数据源")
            return []
        
        return self.parallel_search(
            queries=queries,
            sources=sources,
            max_results_per_query=max_results_per_query,
            days_back=days_back,
            max_workers=max_workers
        )
    
    def search_with_fallback(self, 
                           queries: List[str],
                           preferred_sources: List[str] = None,
                           fallback_sources: List[str] = None,
                           max_results_per_query: int = 5,
                           days_back: int = 7) -> List[Document]:
        """
        带降级的搜索，如果首选数据源失败，自动使用备选数据源
        """
        # 设置默认的首选和备选数据源
        if preferred_sources is None:
            preferred_sources = ['tavily', 'brave']
        
        if fallback_sources is None:
            fallback_sources = ['google', 'arxiv', 'academic']
        
        # 首先尝试首选数据源
        results = self.parallel_search(
            queries=queries,
            sources=preferred_sources,
            max_results_per_query=max_results_per_query,
            days_back=days_back
        )
        
        # 如果结果不够，使用备选数据源补充
        if len(results) < len(queries) * max_results_per_query // 2:
            self.logger.logger.info("🔄 首选数据源结果不足，启用备选数据源...")
            
            fallback_results = self.parallel_search(
                queries=queries,
                sources=fallback_sources,
                max_results_per_query=max_results_per_query,
                days_back=days_back
            )
            
            # 合并结果并去重
            seen_urls = {doc.url for doc in results}
            for doc in fallback_results:
                if doc.url not in seen_urls:
                    results.append(doc)
                    seen_urls.add(doc.url)
        
        return results


class SearchOrchestrator:
    """
    搜索服务的总调度中心（Orchestrator）
    负责协调各个SearchAgent，管理整个端到端的搜索流程
    """
    
    def __init__(self, config: SearchConfig):
        """
        初始化搜索编排器，创建所需的Agent实例
        
        Args:
            config (SearchConfig): 搜索配置实例
        """
        self.config = config
        self.logger = SearchLogger(config.to_dict())
        
        # 初始化各个Agent
        self.collector_agent = CollectorInitializationAgent(config)
        self.execution_agent = SearchExecutionAgent(config, self.collector_agent.collectors)
        self.parallel_agent = ParallelSearchAgent(config, self.collector_agent.collectors, self.execution_agent)
        
        self.logger.logger.info("🚀 SearchOrchestrator初始化完成")
    
    def parallel_search(self, 
                       queries: List[str], 
                       sources: List[str] = None, 
                       max_results_per_query: int = 5,
                       days_back: int = 7,
                       max_workers: int = 6) -> List[Document]:
        """
        执行并行搜索
        """
        return self.parallel_agent.parallel_search(
            queries=queries,
            sources=sources,
            max_results_per_query=max_results_per_query,
            days_back=days_back,
            max_workers=max_workers
        )
    
    def search_by_category(self, 
                          queries: List[str], 
                          category: str = 'web',
                          max_results_per_query: int = 5,
                          days_back: int = 7,
                          max_workers: int = 4) -> List[Document]:
        """
        按类别搜索
        """
        return self.parallel_agent.search_by_category(
            queries=queries,
            category=category,
            max_results_per_query=max_results_per_query,
            days_back=days_back,
            max_workers=max_workers
        )
    
    def search_with_fallback(self, 
                           queries: List[str],
                           preferred_sources: List[str] = None,
                           fallback_sources: List[str] = None,
                           max_results_per_query: int = 5,
                           days_back: int = 7) -> List[Document]:
        """
        带降级的搜索
        """
        return self.parallel_agent.search_with_fallback(
            queries=queries,
            preferred_sources=preferred_sources,
            fallback_sources=fallback_sources,
            max_results_per_query=max_results_per_query,
            days_back=days_back
        )
    
    def get_available_sources(self) -> Dict[str, List[str]]:
        """获取所有可用的数据源"""
        return self.collector_agent.get_available_sources()
    
    def get_collector_info(self) -> List[CollectorInfo]:
        """获取所有收集器的信息"""
        return self.collector_agent.get_collector_info()
    
    def get_search_metrics(self, search_results: List[Document], execution_time: float, 
                          queries: List[str], sources_used: List[str]) -> SearchMetrics:
        """生成搜索性能指标"""
        errors = []  # 这里可以收集执行过程中的错误
        
        metrics = SearchMetrics(
            total_queries=len(queries),
            successful_queries=len(queries),  # 简化处理，实际应该统计成功的查询数
            failed_queries=0,
            total_results=len(search_results),
            execution_time=execution_time,
            average_time_per_query=execution_time / len(queries) if queries else 0,
            sources_used=sources_used,
            errors=errors
        )
        
        return metrics


# For backward compatibility - 为了保持向后兼容性
SearchGenerator = SearchOrchestrator 