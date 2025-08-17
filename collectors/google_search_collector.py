import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import config
from collectors.llm_processor import LLMProcessor
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GoogleSearchCollector:
    """
    Google Custom Search API收集器
    用于从Google搜索获取资料和数据
    """
    
    def __init__(self, api_key=None, cx=None):
        """
        初始化Google搜索收集器
        
        Args:
            api_key (str): Google Custom Search API密钥
            cx (str): Google Custom Search Engine ID
        """
        self.api_key = api_key if api_key else getattr(config, 'GOOGLE_SEARCH_API_KEY', None)
        self.cx = cx if cx else getattr(config, 'GOOGLE_SEARCH_CX', None)
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.has_api_key = bool(self.api_key and self.cx)
        
        # 初始化会话，配置重试和SSL
        self.session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
            respect_retry_after_header=True
        )
        
        # 配置HTTP适配器
        adapter = HTTPAdapter(max_retries=retry_strategy)
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
            print("Google Search API密钥或CX未配置，将无法执行搜索")
        else:
            pass  # print("✅ Google搜索收集器已初始化")  # MCP需要静默
    
    def search(self, query: str, days_back: int = 7, max_results: int = 10, 
               site_search: str = None, file_type: str = None) -> List[Dict]:
        """
        执行Google搜索
        
        Args:
            query (str): 搜索查询
            days_back (int): 搜索多少天内的内容
            max_results (int): 最大结果数量
            site_search (str): 限制在特定网站搜索
            file_type (str): 限制文件类型 (pdf, doc, ppt等)
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        if not self.has_api_key:
            print("Google Search API未配置，无法执行搜索")
            return []
        
        results = []
        num_pages = (max_results // 10) + (1 if max_results % 10 > 0 else 0)
        
        for page in range(num_pages):
            start_index = page * 10 + 1
            page_results = min(10, max_results - len(results))
            
            if page_results <= 0:
                break
                
            try:
                # 构建搜索参数
                params = {
                    'key': self.api_key,
                    'cx': self.cx,
                    'q': query,
                    'start': start_index,
                    'num': page_results,
                    'dateRestrict': f'd{days_back}' if days_back > 0 else None,
                    'safe': 'active',  # 安全搜索
                    'lr': 'lang_zh-CN|lang_en',  # 支持中英文
                }
                
                # 添加可选参数
                if site_search:
                    params['siteSearch'] = site_search
                if file_type:
                    params['fileType'] = file_type
                
                # 移除None值
                params = {k: v for k, v in params.items() if v is not None}
                
                print(f"Google搜索第{page + 1}页: {query}")
                response = self.session.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if 'items' not in data:
                    print(f"第{page + 1}页没有搜索结果")
                    break
                
                # 处理搜索结果
                for item in data['items']:
                    result = {
                        'title': item.get('title', ''),
                        'content': item.get('snippet', ''),
                        'url': item.get('link', ''),
                        'source': self._extract_domain(item.get('link', '')),
                        'published_date': self._extract_date(item),
                        'search_engine': 'Google',
                        'query': query
                    }
                    
                    # 添加额外信息
                    if 'pagemap' in item:
                        pagemap = item['pagemap']
                        if 'metatags' in pagemap:
                            metatags = pagemap['metatags'][0] if pagemap['metatags'] else {}
                            result['description'] = metatags.get('og:description', result['content'])
                            result['image'] = metatags.get('og:image', '')
                    
                    results.append(result)
                
                # API速率限制：避免过快请求
                time.sleep(0.1)
                
            except requests.exceptions.RequestException as e:
                print(f"Google搜索API请求错误: {str(e)}")
                # 如果是SSL错误，尝试不验证SSL
                if "SSL" in str(e) or "ssl" in str(e).lower():
                    try:
                        print("尝试跳过SSL验证重新请求...")
                        response = self.session.get(self.base_url, params=params, timeout=30, verify=False)
                        response.raise_for_status()
                        data = response.json()
                        
                        if 'items' not in data:
                            print(f"第{page + 1}页没有搜索结果")
                            break
                        
                        # 处理搜索结果
                        for item in data['items']:
                            result = {
                                'title': item.get('title', ''),
                                'content': item.get('snippet', ''),
                                'url': item.get('link', ''),
                                'source': self._extract_domain(item.get('link', '')),
                                'published_date': self._extract_date(item),
                                'search_engine': 'Google',
                                'query': query
                            }
                            
                            # 添加额外信息
                            if 'pagemap' in item:
                                pagemap = item['pagemap']
                                if 'metatags' in pagemap:
                                    metatags = pagemap['metatags'][0] if pagemap['metatags'] else {}
                                    result['description'] = metatags.get('og:description', result['content'])
                                    result['image'] = metatags.get('og:image', '')
                            
                            results.append(result)
                        
                        print(f"✅ Google搜索SSL重试成功: 第{page + 1}页")
                        time.sleep(0.1)
                        continue
                        
                    except Exception as ssl_retry_error:
                        print(f"SSL重试也失败: {str(ssl_retry_error)}")
                        break
                else:
                    break
            except Exception as e:
                print(f"处理Google搜索结果时出错: {str(e)}")
                break
        
        print(f"Google搜索完成: {query}, 共获得{len(results)}条结果")
        return results
    
    def search_news(self, topic: str, days_back: int = 7, max_results: int = 10) -> List[Dict]:
        """
        搜索新闻内容
        
        Args:
            topic (str): 搜索主题
            days_back (int): 搜索多少天内的新闻
            max_results (int): 最大结果数量
            
        Returns:
            List[Dict]: 新闻搜索结果
        """
        # 构建新闻相关的搜索查询
        news_queries = [
            f"{topic} 新闻 最新",
            f"{topic} news latest",
            f"{topic} 动态 发展",
            f"{topic} breakthrough announcement"
        ]
        
        all_results = []
        results_per_query = max_results // len(news_queries) + 1
        
        for query in news_queries:
            try:
                # 优先搜索新闻网站
                results = self.search(
                    query=query,
                    days_back=days_back,
                    max_results=results_per_query,
                    site_search=None  # 可以添加特定新闻网站
                )
                
                # 为结果添加新闻标签
                for result in results:
                    result['content_type'] = 'news'
                    result['topic'] = topic
                
                # 去重添加
                existing_urls = {r['url'] for r in all_results}
                for result in results:
                    if result['url'] not in existing_urls:
                        all_results.append(result)
                        existing_urls.add(result['url'])
                
            except Exception as e:
                print(f"搜索新闻时出错 ({query}): {str(e)}")
                continue
        
        # 限制最终结果数量
        return all_results[:max_results]
    
    def search_research_papers(self, topic: str, days_back: int = 30, max_results: int = 10) -> List[Dict]:
        """
        搜索学术研究论文
        
        Args:
            topic (str): 研究主题
            days_back (int): 搜索多少天内的论文
            max_results (int): 最大结果数量
            
        Returns:
            List[Dict]: 研究论文搜索结果
        """
        # 构建学术搜索查询
        academic_queries = [
            f"{topic} research paper filetype:pdf",
            f"{topic} study analysis",
            f"{topic} academic paper",
            f"{topic} 研究 论文"
        ]
        
        all_results = []
        results_per_query = max_results // len(academic_queries) + 1
        
        for query in academic_queries:
            try:
                # 搜索学术网站和PDF文件
                results = self.search(
                    query=query,
                    days_back=days_back,
                    max_results=results_per_query,
                    file_type='pdf' if 'filetype:pdf' in query else None
                )
                
                # 为结果添加学术标签
                for result in results:
                    result['content_type'] = 'academic'
                    result['topic'] = topic
                
                # 去重添加
                existing_urls = {r['url'] for r in all_results}
                for result in results:
                    if result['url'] not in existing_urls:
                        all_results.append(result)
                        existing_urls.add(result['url'])
                
            except Exception as e:
                print(f"搜索学术论文时出错 ({query}): {str(e)}")
                continue
        
        return all_results[:max_results]
    
    def search_industry_reports(self, topic: str, days_back: int = 90, max_results: int = 10) -> List[Dict]:
        """
        搜索行业报告
        
        Args:
            topic (str): 行业主题
            days_back (int): 搜索多少天内的报告
            max_results (int): 最大结果数量
            
        Returns:
            List[Dict]: 行业报告搜索结果
        """
        # 构建行业报告搜索查询
        report_queries = [
            f"{topic} industry report 2024",
            f"{topic} market analysis report",
            f"{topic} 行业报告 市场分析",
            f"{topic} white paper filetype:pdf",
            f"{topic} industry outlook trends"
        ]
        
        all_results = []
        results_per_query = max_results // len(report_queries) + 1
        
        for query in report_queries:
            try:
                results = self.search(
                    query=query,
                    days_back=days_back,
                    max_results=results_per_query
                )
                
                # 为结果添加报告标签
                for result in results:
                    result['content_type'] = 'industry_report'
                    result['topic'] = topic
                
                # 去重添加
                existing_urls = {r['url'] for r in all_results}
                for result in results:
                    if result['url'] not in existing_urls:
                        all_results.append(result)
                        existing_urls.add(result['url'])
                
            except Exception as e:
                print(f"搜索行业报告时出错 ({query}): {str(e)}")
                continue
        
        return all_results[:max_results]
    
    def get_comprehensive_research(self, topic: str, days_back: int = 7) -> Dict:
        """
        获取主题的综合研究资料
        
        Args:
            topic (str): 研究主题
            days_back (int): 搜索天数范围
            
        Returns:
            Dict: 包含各类型内容的字典
        """
        print(f"开始Google搜索综合研究: {topic}")
        
        if not self.has_api_key:
            return {
                'news': [],
                'academic': [],
                'industry_reports': [],
                'general': [],
                'total_count': 0
            }
        
        # 并行搜索不同类型的内容
        results = {
            'news': self.search_news(topic, days_back=days_back, max_results=8),
            'academic': self.search_research_papers(topic, days_back=days_back*4, max_results=6),
            'industry_reports': self.search_industry_reports(topic, days_back=days_back*12, max_results=5),
            'general': self.search(topic, days_back=days_back, max_results=10)
        }
        
        # 添加总数统计
        total_count = sum(len(v) for v in results.values())
        results['total_count'] = total_count
        
        print(f"Google搜索完成: {topic}, 总共获得{total_count}条结果")
        print(f"  - 新闻: {len(results['news'])}条")
        print(f"  - 学术: {len(results['academic'])}条") 
        print(f"  - 行业报告: {len(results['industry_reports'])}条")
        print(f"  - 通用: {len(results['general'])}条")
        
        return results
    
    def _extract_domain(self, url: str) -> str:
        """从URL提取域名"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "未知来源"
    
    def _extract_date(self, item: Dict) -> str:
        """从搜索结果项中提取日期"""
        # Google搜索结果通常不包含明确的发布日期
        # 可以尝试从pagemap或其他元数据中提取
        try:
            if 'pagemap' in item and 'metatags' in item['pagemap']:
                metatags = item['pagemap']['metatags'][0] if item['pagemap']['metatags'] else {}
                
                # 尝试多个可能的日期字段
                date_fields = ['article:published_time', 'datePublished', 'publishedDate', 'date']
                for field in date_fields:
                    if field in metatags and metatags[field]:
                        return metatags[field][:10]  # 只返回日期部分
            
            # 如果没有找到具体日期，返回今天的日期
            return datetime.now().strftime('%Y-%m-%d')
        except:
            return datetime.now().strftime('%Y-%m-%d')
    
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
        
        print(f"  🔍 [Google] 开始严格时间过滤，要求最近{days_limit}天内的内容（截止日期：{cutoff_date.strftime('%Y-%m-%d')}）")
        print(f"  ⚠️ [Google] 注意：只接受有明确发布日期的内容，忽略'最新'、'今日'等关键词")
        
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
                    print(f"    ✅ [Google] 保留: {title[:30]}... ({filter_reason})")
                else:
                    print(f"    ✅ [Google] 保留: {title} ({filter_reason})")
            else:
                if len(title) > 30:
                    print(f"    ❌ [Google] 过滤: {title[:30]}... ({filter_reason})")
                else:
                    print(f"    ❌ [Google] 过滤: {title} ({filter_reason})")
        
        original_count = len(items)
        filtered_count = len(filtered_items)
        
        if filtered_count < original_count:
            print(f"  ⏰ [Google] 严格时间过滤结果: {original_count} → {filtered_count} 条（排除了{original_count - filtered_count}条无可靠时间信息的内容）")
        else:
            print(f"  ⏰ [Google] 严格时间过滤结果: 保留全部{filtered_count}条内容")
            
        return filtered_items
    
    def get_site_specific_search(self, topic: str, sites: List[str], days_back: int = 7) -> List[Dict]:
        """
        在特定网站中搜索内容
        
        Args:
            topic (str): 搜索主题
            sites (List[str]): 网站列表
            days_back (int): 搜索天数范围
            
        Returns:
            List[Dict]: 搜索结果
        """
        all_results = []
        
        for site in sites:
            try:
                results = self.search(
                    query=topic,
                    days_back=days_back,
                    max_results=5,
                    site_search=site
                )
                
                # 为结果添加网站信息
                for result in results:
                    result['target_site'] = site
                
                all_results.extend(results)
                
            except Exception as e:
                print(f"在{site}搜索时出错: {str(e)}")
                continue
        
        return all_results 