import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import config
from collectors.llm_processor import LLMProcessor
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


class BraveSearchCollector:
    """
    Brave Web Search API收集器
    使用Brave独立搜索引擎获取网络搜索结果
    根据官方文档优化的版本
    """
    
    def __init__(self, api_key=None):
        """
        初始化Brave搜索收集器
        
        Args:
            api_key (str): Brave Web Search API密钥
        """
        self.api_key = api_key if api_key else getattr(config, 'BRAVE_SEARCH_API_KEY', None)
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.local_search_url = "https://api.search.brave.com/res/v1/local/search"
        self.has_api_key = bool(self.api_key)
        
        # 初始化会话，配置重试和连接池
        self.session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,  # 总共重试3次
            status_forcelist=[429, 500, 502, 503, 504],  # 对这些状态码重试
            backoff_factor=1,  # 重试间隔：1s, 2s, 4s
            respect_retry_after_header=True
        )
        
        # 配置HTTP适配器
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # 连接池大小
            pool_maxsize=20,     # 连接池最大连接数
            pool_block=False     # 非阻塞连接池
        )
        
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # 初始化LLM处理器用于内容处理
        try:
            self.llm_processor = LLMProcessor()
            self.has_llm = True
        except Exception as e:
            print(f"初始化LLM处理器失败: {str(e)}")
            self.has_llm = False
        
        if not self.has_api_key:
            print("Brave Search API密钥未配置，将无法执行搜索")
        else:
            pass  # print("✅ Brave搜索收集器已初始化")  # MCP需要静默
    
    def _get_headers(self):
        """
        根据官方文档构建请求头
        
        Returns:
            dict: 请求头字典
        """
        return {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'X-Subscription-Token': self.api_key,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def search(self, query: str, count: int = 10, offset: int = 0, 
               freshness: str = None, country: str = None, 
               language: str = None, safesearch: str = 'moderate',
               location_data: dict = None, user_agent: str = None) -> List[Dict]:
        """
        执行Brave网络搜索 - 根据官方文档优化
        
        Args:
            query (str): 搜索查询
            count (int): 返回结果数量 (1-20)
            offset (int): 结果偏移量
            freshness (str): 时间过滤 ('pd' - 过去一天, 'pw' - 过去一周, 'pm' - 过去一个月, 'py' - 过去一年)
            country (str): 国家代码 (如 'US', 'CN')
            language (str): 语言代码 (如 'en', 'zh')
            safesearch (str): 安全搜索级别 ('off', 'moderate', 'strict')
            location_data (dict): 地理位置数据
            user_agent (str): 自定义用户代理
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        if not self.has_api_key:
            print("❌ Brave Search API未配置，无法执行搜索")
            return []
        
        # 构建请求参数 - 按照官方文档
        params = {
            'q': query,
            'count': min(count, 20),  # API限制每次最多20个结果
            'safesearch': safesearch
        }
        
        # 添加可选参数
        if offset > 0:
            params['offset'] = offset
        if freshness:
            params['freshness'] = freshness
        if country:
            params['country'] = country
        
        try:
            print(f"Brave搜索: {query}")
            
            # 使用配置好的session进行请求
            response = self.session.get(
                self.base_url, 
                params=params, 
                headers=self._get_headers(),
                timeout=(10, 30)  # 连接超时=10s，读取超时=30s
            )
            
            response.raise_for_status()
            data = response.json()
            
            # 处理搜索结果
            results = []
            web_results = data.get('web', {}).get('results', [])
            
            for item in web_results:
                result = {
                    'title': item.get('title', ''),
                    'content': item.get('description', ''),
                    'url': item.get('url', ''),
                    'source': self._extract_domain(item.get('url', '')),
                    'published_date': item.get('age', ''),
                    'search_engine': 'Brave',
                    'query': query,
                    'language': item.get('language', ''),
                    'family_friendly': item.get('family_friendly', True)
                }
                
                # 添加额外信息
                if 'extra_snippets' in item:
                    result['extra_snippets'] = item['extra_snippets']
                
                results.append(result)
            
            # API速率限制
            time.sleep(0.2)  # 增加间隔避免过快请求
            
            print(f"✅ Brave搜索成功: {query}, 获得{len(results)}条结果")
            return results
            
        except requests.exceptions.ConnectTimeout:
            print(f"❌ Brave搜索连接超时: {query}")
            return []
        except requests.exceptions.ReadTimeout:
            print(f"❌ Brave搜索读取超时: {query}")
            return []
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Brave搜索连接错误: {query} - {str(e)}")
            return []
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 422:
                print(f"⚠️ Brave搜索参数错误，尝试简化查询: {query}")
                return self._fallback_search(query, count)
            elif e.response.status_code == 429:
                print(f"⚠️ Brave搜索API限流，等待后重试: {query}")
                time.sleep(2)
                return []
            else:
                print(f"❌ Brave搜索HTTP错误 {e.response.status_code}: {query}")
                return []
        except Exception as e:
            print(f"❌ Brave搜索未知错误: {query} - {str(e)}")
            return []
    
    def _fallback_search(self, query: str, count: int) -> List[Dict]:
        """
        参数错误时的降级搜索
        """
        try:
            # 使用最简参数
            simple_params = {
                'q': query,
                'count': min(count, 10)
            }
            
            response = self.session.get(
                self.base_url,
                params=simple_params,
                headers=self._get_headers(),
                timeout=(10, 30)
            )
            
            response.raise_for_status()
            data = response.json()
            
            results = []
            web_results = data.get('web', {}).get('results', [])
            
            for item in web_results:
                result = {
                    'title': item.get('title', ''),
                    'content': item.get('description', ''),
                    'url': item.get('url', ''),
                    'source': self._extract_domain(item.get('url', '')),
                    'published_date': item.get('age', ''),
                    'search_engine': 'Brave',
                    'query': query
                }
                results.append(result)
            
            print(f"✅ Brave降级搜索成功: {query}, 获得{len(results)}条结果")
            return results
            
        except Exception as e:
            print(f"❌ Brave降级搜索也失败: {query} - {str(e)}")
            return []
    
    def search_news(self, topic: str, days_back: int = 7, max_results: int = 10) -> List[Dict]:
        """
        搜索新闻内容 - 优化版
        """
        if not self.has_api_key:
            return []
        
        news_queries = [
            f"{topic} news latest {days_back} days",
            f"{topic} 最新新闻 {days_back}天",
            f"{topic} breaking news recent",
            f"{topic} industry news 2025"
        ]
        
        all_results = []
        seen_urls = set()
        
        for query in news_queries:
            try:
                results = self.search(
                    query, 
                    count=max_results//len(news_queries) + 2,
                    freshness='pw' if days_back <= 7 else 'pm'
                )
                
                for result in results:
                    if result['url'] not in seen_urls:
                        seen_urls.add(result['url'])
                        all_results.append(result)
                
                if len(all_results) >= max_results:
                    break
                    
                time.sleep(0.3)  # 增加间隔
                
            except Exception as e:
                print(f"搜索新闻时出错: {query} - {str(e)}")
                continue
        
        return all_results[:max_results]
    
    def search_research_content(self, topic: str, days_back: int = 30, max_results: int = 10) -> List[Dict]:
        """
        搜索研究内容 - 优化版
        """
        if not self.has_api_key:
            return []
        
        research_queries = [
            f"{topic} research 2025 latest study",
            f"{topic} 研究报告 2025年",
            f"{topic} analysis report {days_back} days",
            f"{topic} white paper recent"
        ]
        
        all_results = []
        seen_urls = set()
        
        for query in research_queries:
            try:
                results = self.search(
                    query, 
                    count=max_results//len(research_queries) + 2,
                    freshness='pm' if days_back <= 30 else None
                )
                
                for result in results:
                    if result['url'] not in seen_urls:
                        seen_urls.add(result['url'])
                        all_results.append(result)
                
                if len(all_results) >= max_results:
                    break
                    
                time.sleep(0.3)
                
            except Exception as e:
                print(f"搜索研究内容时出错: {query} - {str(e)}")
                continue
        
        return all_results[:max_results]
    
    def search_industry_insights(self, topic: str, days_back: int = 90, max_results: int = 10) -> List[Dict]:
        """
        搜索行业洞察 - 优化版
        """
        if not self.has_api_key:
            return []
        
        insight_queries = [
            f"{topic} industry trends 2025",
            f"{topic} market analysis recent",
            f"{topic} 行业趋势 2025",
            f"{topic} business intelligence report"
        ]
        
        all_results = []
        seen_urls = set()
        
        for query in insight_queries:
            try:
                results = self.search(
                    query, 
                    count=max_results//len(insight_queries) + 2
                )
                
                for result in results:
                    if result['url'] not in seen_urls:
                        seen_urls.add(result['url'])
                        all_results.append(result)
                
                if len(all_results) >= max_results:
                    break
                    
                time.sleep(0.3)
                
            except Exception as e:
                print(f"搜索行业洞察时出错: {query} - {str(e)}")
                continue
        
        return all_results[:max_results]
    
    def get_comprehensive_research(self, topic: str, days_back: int = 7) -> Dict:
        """
        综合研究方法 - 优化版
        """
        print(f"开始Brave搜索综合研究: {topic}")
        
        research_data = {
            "breaking_news": [],
            "innovation_news": [],
            "investment_news": [],
            "policy_news": [],
            "trend_news": [],
            "company_news": [],
            "total_count": 0
        }
        
        # 定义不同类型的搜索查询
        search_categories = {
            "breaking_news": [
                f"{topic} 新闻 最新",
                f"{topic} news latest",
                f"{topic} breaking news",
                f"{topic} 最新动态",
                f"{topic} research study"
            ],
            "innovation_news": [
                f"{topic} 技术创新 2025",
                f"{topic} innovation 2025",
                f"{topic} new technology",
                f"{topic} breakthrough research"
            ],
            "investment_news": [
                f"{topic} 投资 融资 2025",
                f"{topic} investment funding 2025",
                f"{topic} venture capital",
                f"{topic} IPO acquisition"
            ],
            "policy_news": [
                f"{topic} 政策 法规 2025",
                f"{topic} policy regulation 2025",
                f"{topic} government policy",
                f"{topic} compliance standards"
            ],
            "trend_news": [
                f"{topic} 趋势 发展 2025",
                f"{topic} trends 2025",
                f"{topic} market analysis",
                f"{topic} future outlook"
            ]
        }
        
        # 为每个类别搜索
        for category, queries in search_categories.items():
            category_results = []
            seen_urls = set()
            
            for query in queries:
                try:
                    results = self.search(
                        query, 
                        count=3,  # 每个查询获取少量结果避免重复
                        freshness='pw' if days_back <= 7 else 'pm'
                    )
                    
                    for result in results:
                        if result['url'] not in seen_urls:
                            seen_urls.add(result['url'])
                            category_results.append(result)
                    
                    time.sleep(0.4)  # 适当延迟避免限流
                    
                except Exception as e:
                    print(f"{category}搜索出错: {query} - {str(e)}")
                    continue
            
            research_data[category] = category_results[:10]  # 每类最多10条
            print(f"{category}: 获得{len(research_data[category])}条结果")
        
        # 计算总数
        research_data["total_count"] = sum(
            len(research_data[key]) for key in research_data.keys() 
            if key != "total_count"
        )
        
        print(f"Brave综合搜索完成，总计{research_data['total_count']}条结果")
        return research_data
    
    def local_search(self, query: str, location: str = None, count: int = 10, 
                    offset: int = 0, country: str = None) -> List[Dict]:
        """
        本地搜索 - 暂时禁用，因为需要特殊权限
        """
        print("本地搜索需要Pro计划，暂时禁用")
        return []
    
    def _extract_domain(self, url: str) -> str:
        """
        从URL中提取域名
        
        Args:
            url (str): 完整URL
            
        Returns:
            str: 域名
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or url
        except:
            return url
    
    def _filter_by_date(self, items, days_limit):
        """
        根据时间限制过滤内容项 - 只依赖可靠的时间信息
        
        Args:
            items (list): 内容项列表
            days_limit (int): 天数限制
            
        Returns:
            list: 过滤后的内容项列表
        """
        if not items or days_limit <= 0:
            return items
            
        filtered_items = []
        cutoff_date = datetime.now() - timedelta(days=days_limit)
        current_year = datetime.now().year
        
        print(f"  🔍 [Brave] 开始严格时间过滤，要求最近{days_limit}天内的内容（截止日期：{cutoff_date.strftime('%Y-%m-%d')}）")
        print(f"  ⚠️ [Brave] 注意：只接受有明确发布日期的内容，忽略'最新'、'今日'等关键词")
        
        for item in items:
            should_include = False
            filter_reason = ""
            
            title = item.get('title', '')
            content = item.get('content', '')
            combined_text = f"{title} {content}".lower()
            
            # 1. 首先检查是否包含明显的旧年份标识
            old_year_patterns = ['2024年', '2023年', '2022年', '2021年', '2020年']
            has_old_year = any(pattern in combined_text for pattern in old_year_patterns)
            
            if has_old_year:
                filter_reason = "包含旧年份标识"
                should_include = False
            else:
                # 2. 检查是否有可靠的发布日期信息
                published_date = item.get("published_date")
                
                if published_date and published_date != "未知日期":
                    try:
                        # 尝试解析发布日期
                        pub_date = None
                        
                        if isinstance(published_date, str):
                            # 尝试多种日期格式
                            date_formats = [
                                "%Y-%m-%d",
                                "%Y-%m-%d %H:%M:%S",
                                "%Y-%m-%dT%H:%M:%S",
                                "%Y-%m-%dT%H:%M:%S.%fZ",
                                "%Y-%m-%dT%H:%M:%SZ",
                                "%Y/%m/%d",
                                "%d/%m/%Y",
                                "%m/%d/%Y"
                            ]
                            
                            for fmt in date_formats:
                                try:
                                    pub_date = datetime.strptime(published_date, fmt)
                                    break
                                except ValueError:
                                    continue
                        
                        if pub_date:
                            # 有明确的发布日期，检查是否在时间范围内
                            if pub_date >= cutoff_date:
                                should_include = True
                                filter_reason = f"发布日期符合要求（{pub_date.strftime('%Y-%m-%d')}）"
                            else:
                                should_include = False
                                filter_reason = f"发布日期过早（{pub_date.strftime('%Y-%m-%d')}）"
                        else:
                            # 无法解析发布日期
                            should_include = False
                            filter_reason = "无法解析发布日期格式"
                            
                    except Exception as e:
                        should_include = False
                        filter_reason = f"发布日期解析失败: {str(e)}"
                        
                else:
                    # 3. 没有发布日期的情况 - 智能处理模糊日期
                    
                    # 检查是否包含模糊的日期格式（如"3月27日"、"12月15日"等）
                    import re
                    ambiguous_date_patterns = [
                        r'(\d{1,2})月(\d{1,2})日',  # 3月27日
                        r'(\d{1,2})/(\d{1,2})(?!\d)',  # 3/27 (但不是 3/27/2025)
                        r'(\d{1,2})-(\d{1,2})(?!\d)',  # 3-27 (但不是 3-27-2025)
                    ]
                    
                    ambiguous_date_match = None
                    for pattern in ambiguous_date_patterns:
                        match = re.search(pattern, combined_text)
                        if match:
                            ambiguous_date_match = match
                            break
                    
                    if ambiguous_date_match:
                        # 找到模糊日期，尝试智能判断
                        try:
                            month = int(ambiguous_date_match.group(1))
                            day = int(ambiguous_date_match.group(2))
                            
                            # 假设是当前年份，构造日期
                            current_date = datetime.now()
                            try:
                                assumed_date = datetime(current_date.year, month, day)
                                
                                # 检查这个日期是否在合理范围内
                                days_diff = (current_date - assumed_date).days
                                
                                if days_diff < 0:
                                    # 日期在未来，可能是去年的日期
                                    assumed_date = datetime(current_date.year - 1, month, day)
                                    days_diff = (current_date - assumed_date).days
                                
                                if days_diff <= days_limit:
                                    # 在时间范围内
                                    should_include = True
                                    filter_reason = f"模糊日期推测为{assumed_date.strftime('%Y-%m-%d')}，在时间范围内"
                                else:
                                    # 超出时间范围
                                    should_include = False
                                    filter_reason = f"模糊日期推测为{assumed_date.strftime('%Y-%m-%d')}，超出{days_limit}天范围"
                                    
                            except ValueError:
                                # 无效日期（如2月30日）
                                should_include = False
                                filter_reason = f"模糊日期{month}月{day}日无效"
                                
                        except (ValueError, IndexError):
                            # 解析失败
                            should_include = False
                            filter_reason = "模糊日期解析失败"
                    else:
                        # 没有模糊日期，检查是否包含当前年份的明确标识
                        current_year_patterns = [
                            f'{current_year}年',
                            f'年{current_year}',
                            f'{current_year}-',
                            f'{current_year}/'
                        ]
                        
                        has_current_year = any(pattern in combined_text for pattern in current_year_patterns)
                        
                        if has_current_year:
                            # 包含当前年份，但仍然要求是短期内的内容
                            if days_limit <= 30:
                                # 对于30天以内的要求，即使有当前年份也不够
                                should_include = False
                                filter_reason = f"包含{current_year}年但无具体日期（严格模式）"
                            else:
                                # 对于较长期的要求，可以接受
                                should_include = True
                                filter_reason = f"包含{current_year}年标识"
                        else:
                            # 既没有发布日期，也没有年份信息
                            should_include = False
                            filter_reason = "无发布日期且无年份信息"
            
            if should_include:
                filtered_items.append(item)
                if len(title) > 30:
                    print(f"    ✅ [Brave] 保留: {title[:30]}... ({filter_reason})")
                else:
                    print(f"    ✅ [Brave] 保留: {title} ({filter_reason})")
            else:
                if len(title) > 30:
                    print(f"    ❌ [Brave] 过滤: {title[:30]}... ({filter_reason})")
                else:
                    print(f"    ❌ [Brave] 过滤: {title} ({filter_reason})")
        
        original_count = len(items)
        filtered_count = len(filtered_items)
        
        if filtered_count < original_count:
            print(f"  ⏰ [Brave] 严格时间过滤结果: {original_count} → {filtered_count} 条（排除了{original_count - filtered_count}条无可靠时间信息的内容）")
        else:
            print(f"  ⏰ [Brave] 严格时间过滤结果: 保留全部{filtered_count}条内容")
            
        return filtered_items
    
    def get_site_specific_search(self, topic: str, sites: List[str], days_back: int = 7) -> List[Dict]:
        """
        站点特定搜索 - 优化版
        """
        all_results = []
        
        for site in sites:
            try:
                site_query = f"site:{site} {topic} recent {days_back} days"
                results = self.search(
                    site_query, 
                    count=5,
                    freshness='pw' if days_back <= 7 else 'pm'
                )
                all_results.extend(results)
                time.sleep(0.5)  # 增加间隔
            except Exception as e:
                print(f"站点搜索出错 {site}: {str(e)}")
                continue
        
        return all_results
    
    def __del__(self):
        """
        清理资源
        """
        if hasattr(self, 'session'):
            self.session.close() 