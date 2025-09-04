import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import threading

# 导入现有的收集器
from collectors.tavily_collector import TavilyCollector
from collectors.brave_search_collector import BraveSearchCollector
from collectors.google_search_collector import GoogleSearchCollector
from collectors.arxiv_collector import ArxivCollector
from collectors.academic_collector import AcademicCollector
from collectors.news_collector import NewsCollector


@dataclass
class Document:
    """
    统一的文档数据结构
    标准化不同数据源的返回格式
    """
    title: str
    content: str
    url: str
    source: str
    source_type: str  # 'web', 'academic', 'news', 'arxiv'
    publish_date: Optional[str] = None
    authors: List[str] = None
    venue: Optional[str] = None  # 学术期刊/会议名称
    score: Optional[float] = None  # 相关性评分
    language: Optional[str] = None
    
    def __post_init__(self):
        if self.authors is None:
            self.authors = []
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return asdict(self)
    
    @property
    def domain(self) -> str:
        """提取域名用于去重"""
        try:
            return urlparse(self.url).netloc.lower()
        except:
            return ""


class SearchMcp:
    """
    搜索MCP (Model Context Protocol)
    
    用途：并行化地从多个Web搜索引擎和学术数据库中获取、聚合和去重信息。
    
    职责：
    - 管理到多个数据源API的连接（Tavily, Brave, Google, Arxiv, Semantic Scholar等）
    - 接收查询列表，并行执行所有搜索
    - 将不同来源的结果标准化为统一的Document对象表
    - 基于URL进行结果去重
    
    输入：queries: list[str], sources: list[str], max_results_per_query: int = 5
    输出：list[Document]
    
    实现要点：使用asyncio和aiohttp为每个数据源实现一个独立的Collector类，
            SearchMcp负责调度这些Collector。
    """
    
    def __init__(self):
        """初始化SearchMcp，设置所有可用的收集器"""
        self.collectors = {}
        self.results_lock = threading.Lock()
        
        # 初始化所有收集器
        self._initialize_collectors()
        
        # 支持的数据源类型
        self.source_types = {
            'web': ['tavily', 'brave', 'google'],
            'academic': ['arxiv', 'semantic_scholar', 'ieee', 'springer', 'core'],
            'news': ['news_api', 'google_news', 'brave_news', 'rss']
        }
        
        print(f"✅ SearchMcp初始化完成，可用收集器: {list(self.collectors.keys())}")
    
    def _initialize_collectors(self):
        """初始化所有收集器"""
        # Web搜索收集器
        try:
            tavily = TavilyCollector()
            if tavily.has_api_key:
                self.collectors['tavily'] = tavily
                print("✅ Tavily收集器已启用")
        except Exception as e:
            print(f"⚠️ Tavily收集器初始化失败: {str(e)}")
        
        try:
            brave = BraveSearchCollector()
            if brave.has_api_key:
                self.collectors['brave'] = brave
                print("✅ Brave收集器已启用")
        except Exception as e:
            print(f"⚠️ Brave收集器初始化失败: {str(e)}")
        
        try:
            google = GoogleSearchCollector()
            if google.has_api_key:
                self.collectors['google'] = google
                print("✅ Google收集器已启用")
        except Exception as e:
            print(f"⚠️ Google收集器初始化失败: {str(e)}")
        
        # 学术搜索收集器
        try:
            arxiv = ArxivCollector()
            self.collectors['arxiv'] = arxiv
            print("✅ ArXiv收集器已启用")
        except Exception as e:
            print(f"⚠️ ArXiv收集器初始化失败: {str(e)}")
        
        try:
            academic = AcademicCollector()
            self.collectors['academic'] = academic
            print("✅ Academic收集器已启用")
        except Exception as e:
            print(f"⚠️ Academic收集器初始化失败: {str(e)}")
        
        # 新闻收集器
        try:
            news = NewsCollector()
            self.collectors['news'] = news
            print("✅ News收集器已启用")
        except Exception as e:
            print(f"⚠️ News收集器初始化失败: {str(e)}")
    
    def parallel_search(self, 
                       queries: List[str], 
                       sources: List[str] = None, 
                       max_results_per_query: int = 5,
                       days_back: int = 7,
                       max_workers: int = 6) -> List[Document]:
        """
        并行搜索多个查询和数据源
        
        Args:
            queries: 搜索查询列表
            sources: 指定的数据源列表，如果为None则使用所有可用源
            max_results_per_query: 每个查询的最大结果数
            days_back: 搜索多少天内的内容
            max_workers: 最大并行工作线程数
            
        Returns:
            List[Document]: 去重后的搜索结果列表
        """
        if not queries:
            return []
        
        # 如果没有指定数据源，使用所有可用的
        if sources is None:
            sources = list(self.collectors.keys())
        else:
            # 过滤只保留可用的数据源
            sources = [s for s in sources if s in self.collectors]
        
        if not sources:
            print("❌ 没有可用的数据源")
            return []
        
        print(f"🚀 开始并行搜索 {len(queries)} 个查询，使用 {len(sources)} 个数据源")
        print(f"📝 查询: {queries[:3]}{'...' if len(queries) > 3 else ''}")
        print(f"🔍 数据源: {sources}")
        
        all_results = []
        seen_urls = set()
        
        start_time = time.time()
        
        # 使用线程池并行执行搜索
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 为每个查询和数据源组合创建任务
            future_to_info = {}
            
            for query in queries:
                for source in sources:
                    if source in self.collectors:
                        future = executor.submit(
                            self._execute_single_search,
                            query, source, max_results_per_query, days_back
                        )
                        future_to_info[future] = (query, source)
            
            # 收集结果
            completed_tasks = 0
            total_tasks = len(future_to_info)
            
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
                    
                    print(f"  ✅ [{completed_tasks}/{total_tasks}] {source}({query}): {len(results)}条结果, {new_count}条新增")
                    
                except Exception as e:
                    print(f"  ❌ [{completed_tasks}/{total_tasks}] {source}({query}) 搜索失败: {str(e)}")
        
        # 按相关性和时间排序
        all_results.sort(key=lambda doc: (
            doc.score or 0,  # 相关性评分
            self._parse_date(doc.publish_date) if doc.publish_date else datetime.min
        ), reverse=True)
        
        total_time = time.time() - start_time
        print(f"📊 搜索完成: 获得 {len(all_results)} 条去重结果，耗时 {total_time:.1f}秒")
        
        return all_results
    
    def _execute_single_search(self, query: str, source: str, max_results: int, days_back: int) -> List[Document]:
        """执行单个搜索任务"""
        collector = self.collectors.get(source)
        if not collector:
            return []
        
        try:
            # 根据不同的收集器调用相应的搜索方法
            raw_results = []
            
            if source == 'tavily':
                raw_results = collector.search(query, max_results=max_results)
                
            elif source == 'brave':
                raw_results = collector.search(query, count=max_results)
                
            elif source == 'google':
                raw_results = collector.search(query, days_back=days_back, max_results=max_results)
                
            elif source == 'arxiv':
                raw_results = collector.search(query, days_back=days_back)
                
            elif source == 'academic':
                # Academic收集器有多个方法，这里使用Semantic Scholar
                raw_results = collector.search_semantic_scholar(query, days_back=days_back)
                
            elif source == 'news':
                raw_results = collector.search_news_api(query, days_back=days_back)
            
            # 标准化结果为Document格式
            documents = self._standardize_results(raw_results, source)
            
            return documents[:max_results]  # 限制结果数量
            
        except Exception as e:
            print(f"搜索执行失败 {source}({query}): {str(e)}")
            return []
    
    def _standardize_results(self, raw_results: List[Dict], source: str) -> List[Document]:
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
                print(f"标准化结果失败: {str(e)}")
                continue
        
        return documents
    
    def _determine_source_type(self, source: str, result: Dict) -> str:
        """确定数据源类型"""
        if source in ['arxiv', 'academic']:
            return 'academic'
        elif source == 'news' or 'news' in source:
            return 'news'
        else:
            return 'web'
    
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
    
    def search_by_category(self, 
                          queries: List[str], 
                          category: str = 'web',
                          max_results_per_query: int = 5,
                          days_back: int = 7,
                          max_workers: int = 4) -> List[Document]:
        """
        按类别搜索
        
        Args:
            queries: 搜索查询列表
            category: 搜索类别 ('web', 'academic', 'news')
            max_results_per_query: 每个查询的最大结果数
            days_back: 搜索多少天内的内容
            max_workers: 最大并行工作线程数
            
        Returns:
            List[Document]: 搜索结果列表
        """
        if category not in self.source_types:
            raise ValueError(f"不支持的搜索类别: {category}")
        
        # 获取该类别下的可用数据源
        sources = [s for s in self.source_types[category] if s in self.collectors]
        
        if not sources:
            print(f"❌ 类别 {category} 下没有可用的数据源")
            return []
        
        return self.parallel_search(
            queries=queries,
            sources=sources,
            max_results_per_query=max_results_per_query,
            days_back=days_back,
            max_workers=max_workers
        )
    
    def get_available_sources(self) -> Dict[str, List[str]]:
        """获取所有可用的数据源"""
        available = {}
        for category, sources in self.source_types.items():
            available[category] = [s for s in sources if s in self.collectors]
        return available
    
    def search_with_fallback(self, 
                           queries: List[str],
                           preferred_sources: List[str] = None,
                           fallback_sources: List[str] = None,
                           max_results_per_query: int = 5,
                           days_back: int = 7) -> List[Document]:
        """
        带降级的搜索，如果首选数据源失败，自动使用备选数据源
        
        Args:
            queries: 搜索查询列表
            preferred_sources: 首选数据源
            fallback_sources: 备选数据源
            max_results_per_query: 每个查询的最大结果数
            days_back: 搜索多少天内的内容
            
        Returns:
            List[Document]: 搜索结果列表
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
            print("🔄 首选数据源结果不足，启用备选数据源...")
            
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