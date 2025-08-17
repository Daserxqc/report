import datetime
import json
import requests
import time
from tqdm import tqdm
import config
from urllib.parse import quote_plus
from collectors.llm_processor import LLMProcessor

class AcademicCollector:
    """
    从多个学术来源收集研究论文
    """
    def __init__(self):
        self.api_keys = {
            'semanticscholar': getattr(config, 'SEMANTICSCHOLAR_API_KEY', None),
            'google_scholar': getattr(config, 'GOOGLE_SCHOLAR_API_KEY', None),
            'ieee': getattr(config, 'IEEE_API_KEY', None),
            'springer': getattr(config, 'SPRINGER_API_KEY', None),
            'core': getattr(config, 'CORE_API_KEY', None),
        }
        
        # 确认哪些API可用
        self.available_apis = {k: v is not None for k, v in self.api_keys.items()}
        
        # API密钥状态跟踪
        self.api_status = {k: True for k in self.available_apis if self.available_apis[k]}
        
        # 初始化LLM处理器用于翻译
        try:
            self.llm_processor = LLMProcessor()
            self.has_llm = True
        except Exception as e:
            print(f"初始化LLM处理器失败: {str(e)}")
            self.has_llm = False
            
        # 常见学术领域中英文对照字典，用于直接翻译常见术语
        self.topic_translations = {
            "人工智能": "artificial intelligence",
            "机器学习": "machine learning",
            "深度学习": "deep learning",
            "自然语言处理": "natural language processing",
            "计算机视觉": "computer vision",
            "区块链": "blockchain",
            "元宇宙": "metaverse",
            "虚拟现实": "virtual reality",
            "增强现实": "augmented reality",
            "量子计算": "quantum computing",
            "物联网": "internet of things",
            "大数据": "big data",
            "云计算": "cloud computing",
            "边缘计算": "edge computing",
            "5G": "5G",
            "6G": "6G",
            "半导体": "semiconductor",
            "芯片": "chip technology",
            "数据科学": "data science",
            "强化学习": "reinforcement learning",
            "生成式对抗网络": "generative adversarial networks",
            "自动驾驶": "autonomous driving",
            "脑机接口": "brain-computer interface",
            "智能机器人": "intelligent robotics",
            "生物信息学": "bioinformatics",
            "基因编辑": "gene editing",
            "生物技术": "biotechnology",
            "新能源": "new energy",
            "可再生能源": "renewable energy",
            "网络安全": "cybersecurity",
            "金融科技": "fintech"
        }
        
        # print(f"学术收集器已初始化，可用API: {[k for k, v in self.available_apis.items() if v]}")  # MCP需要静默

    def _translate_to_english(self, text):
        """
        将非英文文本翻译为英文，先检查常见术语字典，再使用LLM翻译
        
        Args:
            text (str): 要翻译的文本
            
        Returns:
            str: 翻译后的英文文本
        """
        # 如果不是中文，直接返回
        if not any('\u4e00' <= char <= '\u9fff' for char in text):
            return text
            
        # 检查是否在预定义术语中
        if text in self.topic_translations:
            translated = self.topic_translations[text]
            print(f"直接翻译术语: '{text}' → '{translated}'")
            return translated
            
        # 使用LLM处理器进行翻译
        if self.has_llm:
            try:
                translated_text = self.llm_processor.translate_text(text, "English")
                print(f"已将搜索词从 '{text}' 翻译为 '{translated_text}'")
                return translated_text
            except Exception as e:
                print(f"LLM翻译失败: {str(e)}")
                
        # 如果LLM翻译失败，使用简单词汇替换
        for zh, en in self.topic_translations.items():
            if zh in text:
                text = text.replace(zh, en)
                
        print(f"使用简单替换翻译: '{text}'")
        return text
    
    def search_semantic_scholar(self, query, days_back=7):
        """
        从Semantic Scholar搜索论文
        
        Args:
            query (str): 搜索关键词
            days_back (int): 搜索多少天内的论文
            
        Returns:
            list: 论文信息列表
        """
        if not self.available_apis['semanticscholar']:
            print("Semantic Scholar API未配置")
            return []
        
        try:
            # 计算日期范围
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=days_back)
            start_date_str = start_date.strftime('%Y-%m-%d')
            
            # 构建API请求
            api_url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                'query': query,
                'limit': 20,
                'fields': 'title,authors,abstract,url,year,venue',
                'publicationDateOrYear': f">={start_date_str}"
            }
            
            headers = {}
            if self.api_keys['semanticscholar']:
                headers['x-api-key'] = self.api_keys['semanticscholar']
                
            print(f"正在Semantic Scholar上搜索: {query}")
            response = requests.get(api_url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for paper in data.get('data', []):
                # 提取作者姓名
                authors = [author.get('name', 'Unknown') for author in paper.get('authors', [])]
                
                paper_info = {
                    'title': paper.get('title', 'Untitled'),
                    'authors': authors,
                    'summary': paper.get('abstract', 'No abstract available'),
                    'published': paper.get('year', datetime.datetime.now().year),
                    'url': paper.get('url', '#'),
                    'source': 'Semantic Scholar',
                    'venue': paper.get('venue', 'Unknown venue')
                }
                results.append(paper_info)
                
            print(f"在Semantic Scholar上找到 {len(results)} 篇论文")
            return results
            
        except Exception as e:
            print(f"Semantic Scholar API错误: {str(e)}")
            return []
    
    def search_springer(self, query, days_back=7):
        """
        从Springer搜索论文
        
        Args:
            query (str): 搜索关键词
            days_back (int): 搜索多少天内的论文
            
        Returns:
            list: 论文信息列表
        """
        if not self.available_apis['springer']:
            print("Springer API未配置")
            return []
            
        try:
            # 计算日期范围
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=days_back)
            start_date_str = start_date.strftime('%Y-%m-%d')
            
            # 构建API请求
            api_url = "http://api.springernature.com/metadata/json"
            params = {
                'q': f'title:"{query}" AND onlinedate>={start_date_str}',
                'api_key': self.api_keys['springer'],
                's': 1,
                'p': 20
            }
            
            print(f"正在Springer上搜索: {query}")
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for paper in data.get('records', []):
                # 提取作者
                creators = paper.get('creators', [])
                authors = [creator.get('creator', 'Unknown') for creator in creators]
                
                paper_info = {
                    'title': paper.get('title', 'Untitled'),
                    'authors': authors,
                    'summary': paper.get('abstract', 'No abstract available'),
                    'published': paper.get('onlineDate', datetime.datetime.now().strftime('%Y-%m-%d')),
                    'url': paper.get('url', [{'value': '#'}])[0].get('value', '#'),
                    'source': 'Springer',
                    'doi': paper.get('doi', 'No DOI')
                }
                results.append(paper_info)
                
            print(f"在Springer上找到 {len(results)} 篇论文")
            return results
            
        except Exception as e:
            print(f"Springer API错误: {str(e)}")
            return []
            
    def search_ieee(self, query, days_back=7):
        """
        从IEEE Xplore搜索论文
        
        Args:
            query (str): 搜索关键词
            days_back (int): 搜索多少天内的论文
            
        Returns:
            list: 论文信息列表
        """
        if not self.available_apis['ieee']:
            print("IEEE Xplore API未配置")
            return []
            
        # 检查API状态，如果之前已知API密钥无效，直接跳过
        if not self.api_status.get('ieee', True):
            print("IEEE Xplore API密钥已被标记为无效，跳过搜索")
            return []
            
        try:
            # 确保查询词是英文
            english_query = self._translate_to_english(query)
            
            # 构建API请求 - 使用正确的参数格式
            api_url = "http://ieeexploreapi.ieee.org/api/v1/search/articles"
            params = {
                'querytext': english_query,
                'format': 'json',
                'apikey': self.api_keys['ieee'],
                'max_records': 25,
                'sort_order': 'desc',
                'sort_field': 'publication_date'
            }
            
            # 可选参数 - 根据需要添加日期过滤
            # 注意：IEEE API似乎不支持精确的日期范围过滤，所以这里使用年份过滤
            current_year = datetime.datetime.now().year
            if days_back > 365:  # 如果搜索范围超过一年，则包括前一年的论文
                params['start_year'] = current_year - 1
            else:
                params['start_year'] = current_year
            
            print(f"正在IEEE Xplore上搜索: {english_query}")
            response = requests.get(api_url, params=params)
            
            # 检查是否返回403 Forbidden，可能表示API密钥不活跃
            if response.status_code == 403:
                self.api_status['ieee'] = False
                print(f"IEEE Xplore API返回403错误，API密钥可能已停用或不活跃")
                print(f"HTTP状态码: {response.status_code}")
                print(f"响应内容: {response.text[:200]}...")
                return []
                
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            # 检查是否有文章返回
            if 'articles' not in data or not data['articles']:
                print("IEEE Xplore没有返回任何文章")
                return results
                
            for paper in data.get('articles', []):
                # 提取作者
                authors = paper.get('authors', {}).get('authors', [])
                author_names = [author.get('full_name', 'Unknown') for author in authors]
                
                # 提取摘要，IEEE API有时返回的摘要在不同字段
                abstract = paper.get('abstract', paper.get('summary', '无摘要'))
                
                # 构建论文URL - 优先使用DOI链接
                paper_url = f"https://doi.org/{paper.get('doi')}" if paper.get('doi') else paper.get('html_url', '#')
                
                paper_info = {
                    'title': paper.get('title', 'Untitled'),
                    'authors': author_names,
                    'summary': abstract,
                    'published': paper.get('publication_date', datetime.datetime.now().strftime('%Y-%m-%d')),
                    'url': paper_url,
                    'source': 'IEEE Xplore',
                    'doi': paper.get('doi', 'No DOI')
                }
                results.append(paper_info)
                
            print(f"在IEEE Xplore上找到 {len(results)} 篇论文")
            return results
            
        except Exception as e:
            print(f"IEEE Xplore API错误: {str(e)}")
            # 记录更详细的错误信息以便调试
            if 'response' in locals() and response is not None:
                print(f"HTTP状态码: {response.status_code}")
                print(f"响应内容: {response.text[:200]}...")  # 只打印前200个字符
                # 如果是403错误，标记API无效
                if response.status_code == 403:
                    self.api_status['ieee'] = False
                    print("IEEE API密钥已被标记为无效，后续请求将跳过")
            return []
            
    def search_core(self, query, days_back=7, max_results=None):
        """
        从CORE API搜索学术论文
        
        Args:
            query (str): 搜索关键词
            days_back (int): 搜索多少天内的论文
            max_results (int): 最大结果数量
            
        Returns:
            list: 论文信息列表
        """
        print("\n==== CORE API调用开始 ====")
        
        # 详细检查API密钥是否有效
        if not self.api_keys['core']:
            print("错误: CORE API密钥未设置 - 请确保环境变量CORE_API_KEY已正确配置")
            self.available_apis['core'] = False
            return []
            
        print(f"CORE API密钥存在: {self.api_keys['core'][:5]}...{self.api_keys['core'][-5:]}")
        
        if not self.available_apis['core']:
            print("CORE API被标记为不可用")
            return []
            
        # 检查API状态，如果之前已知API密钥无效，直接跳过
        if not self.api_status.get('core', True):
            print("CORE API密钥已被标记为无效，跳过搜索")
            return []
            
        # 确保查询词是英文
        english_query = self._translate_to_english(query)
        print(f"搜索词: '{query}' -> '{english_query}'")
            
        # 设置最大结果数
        if max_results is None:
            max_results = getattr(config, "CORE_MAX_RESULTS", 20)
        print(f"最大结果数: {max_results}")
            
        # 构建API请求头部
        headers = {
            "Authorization": f"Bearer {self.api_keys['core']}"
        }
        
        # 根据CORE API v3的文档，使用works端点进行搜索
        api_url = getattr(config, "CORE_API_URL", "https://api.core.ac.uk/v3")
        endpoint = f"{api_url}/search/works"
        print(f"CORE API端点: {endpoint}")
        
        # 构建查询参数
        # 根据CORE API文档，使用正确的查询格式
        # 按相关性排序，并按年份过滤
        current_year = datetime.datetime.now().year
        min_year = current_year - (days_back // 365) - 1  # 将天数转换为大致年数
        
        year_filter = f"yearPublished>={min_year}"
        
        params = {
            "q": english_query,
            "limit": max_results,
            "offset": 0,
            "filter": year_filter
        }
        
        print(f"请求参数: {params}")
        
        try:
            print(f"开始发送请求...")
            response = requests.get(endpoint, headers=headers, params=params, timeout=30)
            print(f"请求已发送，状态码: {response.status_code}")
            
            # 处理403和401错误，这些通常表示API密钥问题
            if response.status_code in (401, 403):
                self.api_status['core'] = False
                print(f"CORE API身份验证错误: HTTP {response.status_code}")
                print(f"响应内容: {response.text[:500]}...")  
                return []
                
            # 详细记录错误信息以便调试
            if response.status_code != 200:
                print(f"CORE API返回错误: HTTP {response.status_code}")
                print(f"响应内容: {response.text[:500]}...")  
                return []
                
            response.raise_for_status()
            print("成功获取响应，解析数据...")
            
            data = response.json()
            
            # 如果没有结果，提前返回
            if "results" not in data:
                print(f"响应中没有'results'字段，返回数据结构: {list(data.keys())}")
                return []
                
            if not data["results"]:
                print("CORE API没有返回任何结果")
                return []
                
            print(f"获取到 {len(data['results'])} 条结果")
                
            # 处理结果
            results = []
            current_time = datetime.datetime.now()
            
            for work in data.get("results", []):
                # 尝试获取发布日期 - CORE API返回的日期可能有多种格式
                published_date_str = current_time.strftime('%Y-%m-%d')
                
                # 尝试不同的日期字段
                if "publishedDate" in work:
                    published_date_str = work["publishedDate"]
                elif "publishedYear" in work or "yearPublished" in work:
                    published_year = work.get("publishedYear") or work.get("yearPublished")
                    if published_year:
                        published_date_str = f"{published_year}-01-01"
                
                # 提取作者 - CORE返回的作者可能有不同格式
                authors = []
                for author in work.get("authors", []):
                    if isinstance(author, dict) and "name" in author:
                        authors.append(author["name"])
                    elif isinstance(author, str):
                        authors.append(author)
                
                # 获取正确的URL - CORE提供多种可能的URL
                paper_url = None
                # 1. 首先尝试下载URL
                if "downloadUrl" in work and work["downloadUrl"]:
                    paper_url = work["downloadUrl"]
                # 2. 其次尝试源文本URL列表中的第一个
                elif "sourceFulltextUrls" in work and work["sourceFulltextUrls"]:
                    paper_url = work["sourceFulltextUrls"][0]
                # 3. 然后尝试DOI
                elif "doi" in work and work["doi"]:
                    paper_url = f"https://doi.org/{work['doi']}"
                # 4. 最后使用CORE自己的链接
                else:
                    paper_url = f"https://core.ac.uk/works/{work.get('id')}"
                
                # 构建论文信息
                paper_info = {
                    "title": work.get("title", "无标题"),
                    "authors": authors,
                    "summary": work.get("abstract", "无摘要"),
                    "published": published_date_str,
                    "url": paper_url,
                    "source": "CORE",
                    "doi": work.get("doi", "无DOI")
                }
                results.append(paper_info)
                
            print(f"成功处理 {len(results)} 篇论文")
            print("==== CORE API调用结束 ====\n")
            return results
            
        except requests.exceptions.Timeout:
            print("CORE API请求超时")
            return []
        except requests.exceptions.ConnectionError:
            print("CORE API连接错误，请检查网络连接")
            return []
        except Exception as e:
            print(f"CORE API错误: {str(e)}")
            # 如果有响应对象，记录更详细的错误信息
            if 'response' in locals() and response is not None:
                print(f"HTTP状态码: {response.status_code}")
                print(f"响应内容: {response.text[:500]}...")  
                # 如果是401或403错误，标记API无效
                if response.status_code in (401, 403):
                    self.api_status['core'] = False
                    print("CORE API密钥已被标记为无效，后续请求将跳过")
            
            # 打印完整的异常堆栈跟踪
            import traceback
            print(traceback.format_exc())
            
            print("==== CORE API调用结束 ====\n")
            return []
    
    def search_crossref(self, query, days_back=7):
        """
        从CrossRef搜索论文 (不需要API密钥)
        
        Args:
            query (str): 搜索关键词
            days_back (int): 搜索多少天内的论文
            
        Returns:
            list: 论文信息列表
        """
        try:
            # 计算日期范围
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=days_back)
            start_date_str = start_date.strftime('%Y-%m-%d')
            
            # CrossRef API
            api_url = "https://api.crossref.org/works"
            params = {
                'query': query,
                'filter': f'from-pub-date:{start_date_str}',
                'rows': 20,
                'sort': 'published',
                'order': 'desc'
            }
            
            print(f"正在CrossRef上搜索: {query}")
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for paper in data.get('message', {}).get('items', []):
                # 提取作者
                authors = []
                for author in paper.get('author', []):
                    name_parts = []
                    if 'given' in author:
                        name_parts.append(author['given'])
                    if 'family' in author:
                        name_parts.append(author['family'])
                    authors.append(' '.join(name_parts) if name_parts else 'Unknown')
                
                # 提取发布日期
                published = datetime.datetime.now().strftime('%Y-%m-%d')
                if 'published' in paper and 'date-parts' in paper['published']:
                    date_parts = paper['published']['date-parts'][0]
                    if len(date_parts) >= 3:
                        published = f"{date_parts[0]}-{date_parts[1]:02d}-{date_parts[2]:02d}"
                    elif len(date_parts) >= 2:
                        published = f"{date_parts[0]}-{date_parts[1]:02d}-01"
                    elif len(date_parts) == 1:
                        published = f"{date_parts[0]}-01-01"
                
                paper_info = {
                    'title': paper.get('title', ['Untitled'])[0] if paper.get('title') else 'Untitled',
                    'authors': authors,
                    'summary': paper.get('abstract', 'No abstract available'),
                    'published': published,
                    'url': paper.get('URL', '#'),
                    'source': 'CrossRef',
                    'doi': paper.get('DOI', 'No DOI')
                }
                results.append(paper_info)
                
            print(f"在CrossRef上找到 {len(results)} 篇论文")
            return results
            
        except Exception as e:
            print(f"CrossRef API错误: {str(e)}")
            return []
            
    def get_papers_by_topic(self, topic, subtopics=None, days_back=7):
        """
        从多个来源获取与主题相关的论文
        
        Args:
            topic (str): 主题
            subtopics (list): 子主题列表
            days_back (int): 搜索多少天内的论文
            
        Returns:
            list: 论文列表
        """
        print(f"从多个学术来源搜索{topic}相关论文...")
        
        # 将主题翻译为英文
        english_topic = self._translate_to_english(topic)
        all_results = []
        
        # 从各个来源获取论文 - 将CORE放在前面，以确保它会被调用
        all_sources = [
            ('CORE', self.search_core),  # 先调用CORE
            ('CrossRef', self.search_crossref),  # CrossRef不需要API密钥，也放前面
            ('IEEE Xplore', self.search_ieee),
            ('Semantic Scholar', self.search_semantic_scholar),
            ('Springer', self.search_springer),
        ]
        
        # 打印出可用的API配置状态
        print(f"当前API状态: {', '.join([f'{k}={v}' for k, v in self.api_status.items()])}")
        
        # 对每个来源进行搜索
        for source_name, search_func in all_sources:
            try:
                print(f"开始从{source_name}获取数据...")
                source_results = search_func(english_topic, days_back)
                
                # 添加唯一结果
                existing_urls = {paper['url'] for paper in all_results}
                for paper in source_results:
                    if paper['url'] not in existing_urls:
                        all_results.append(paper)
                        existing_urls.add(paper['url'])
                        
                print(f"从{source_name}添加了{len(source_results)}篇不重复论文")
                
                # 防止API速率限制
                time.sleep(1)
            except Exception as e:
                print(f"从{source_name}获取论文时出错: {str(e)}")
                import traceback
                print(traceback.format_exc())  # 打印完整的异常堆栈跟踪
                
        # 如果有子主题，也搜索子主题
        if subtopics:
            for subtopic in subtopics:
                # 将子主题翻译为英文
                english_subtopic = self._translate_to_english(subtopic)
                combined_query = f"{english_topic} {english_subtopic}"
                
                # 对每个来源进行搜索
                for source_name, search_func in all_sources:
                    try:
                        source_results = search_func(combined_query, days_back)
                        
                        # 添加唯一结果
                        existing_urls = {paper['url'] for paper in all_results}
                        added = 0
                        for paper in source_results:
                            if paper['url'] not in existing_urls:
                                all_results.append(paper)
                                existing_urls.add(paper['url'])
                                added += 1
                                
                        if added > 0:
                            print(f"子主题'{subtopic}'从{source_name}添加了{added}篇不重复论文")
                            
                        # 防止API速率限制
                        time.sleep(1)
                    except Exception as e:
                        print(f"搜索子主题'{subtopic}'从{source_name}获取论文时出错: {str(e)}")
                        
        print(f"总共收集到 {len(all_results)} 篇学术论文")
        return all_results 