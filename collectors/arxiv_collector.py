import arxiv
import datetime
from dateutil import parser
from tqdm import tqdm
import config
from collectors.llm_processor import LLMProcessor  # 使用LLM替代googletrans

class ArxivCollector:
    def __init__(self):
        self.client = arxiv.Client()
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
        
    def search(self, query, days_back=7):
        """
        Search arXiv for papers related to a query published in the last n days
        
        Args:
            query (str): The search query
            days_back (int): How many days back to search
            
        Returns:
            list: List of dictionaries containing paper information
        """
        # 将查询翻译为英文
        english_query = self._translate_to_english(query)
        
        # Calculate date range - 修复日期问题
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days_back)
        
        # Format the query with date range
        date_query = f"submittedDate:[{start_date.strftime('%Y%m%d')} TO {end_date.strftime('%Y%m%d')}]"
        full_query = f"{english_query} AND {date_query}"
        
        # 使用arxiv.SortCriterion枚举值代替字符串
        if config.ARXIV_SORT_BY == "submittedDate":
            sort_by = arxiv.SortCriterion.SubmittedDate
        elif config.ARXIV_SORT_BY == "relevance":
            sort_by = arxiv.SortCriterion.Relevance
        elif config.ARXIV_SORT_BY == "lastUpdatedDate":
            sort_by = arxiv.SortCriterion.LastUpdatedDate
        else:
            # 默认使用提交日期排序
            sort_by = arxiv.SortCriterion.SubmittedDate
            
        # 使用arxiv.SortOrder枚举值代替字符串
        if config.ARXIV_SORT_ORDER.lower() == "descending":
            sort_order = arxiv.SortOrder.Descending
        else:
            sort_order = arxiv.SortOrder.Ascending
        
        # Create search
        search = arxiv.Search(
            query=full_query,
            max_results=config.ARXIV_MAX_RESULTS,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        results = []
        print(f"正在arXiv上搜索: {full_query}")
        
        # Process results
        for result in tqdm(self.client.results(search)):
            paper_info = {
                'title': result.title,
                'authors': [author.name for author in result.authors],
                'summary': result.summary.replace('\n', ' '),
                'published': result.published.strftime('%Y-%m-%d'),
                'url': result.entry_id,
                'pdf_url': result.pdf_url,
                'categories': result.categories,
                'source': 'arxiv'
            }
            results.append(paper_info)
            
        print(f"在arXiv上找到 {len(results)} 篇论文")
        return results
        
    def get_papers_by_topic(self, topic, subtopics=None, days_back=7):
        """
        Get papers related to a topic and optional subtopics
        
        Args:
            topic (str): The main topic
            subtopics (list): List of subtopics to search for
            days_back (int): How many days back to search
            
        Returns:
            list: List of papers
        """
        # 将主题翻译为英文
        english_topic = self._translate_to_english(topic)
        results = self.search(english_topic, days_back)
        
        # 尝试使用学术专业英文术语进行补充搜索
        try:
            # 使用LLM生成更专业的学术搜索词
            if self.has_llm and len(results) < 3:
                academic_prompt = f"将以下主题转换为3-5个英文学术领域专业搜索词，每个词用逗号分隔，不要加其他解释: {topic}"
                academic_terms = self.llm_processor.call_llm_api(academic_prompt)
                if academic_terms:
                    # 处理返回结果，移除数字标记等
                    academic_terms = academic_terms.strip().replace('\n', ', ').replace('.', '')
                    # 移除非英文字符和解释性文本
                    import re
                    academic_terms = re.sub(r'[^a-zA-Z0-9, -]', '', academic_terms)
                    # 分割术语并去重
                    terms = [term.strip() for term in academic_terms.split(',') if term.strip()]
                    terms = list(set(terms))
                    
                    print(f"使用生成的学术术语进行补充搜索: {terms}")
                    for term in terms[:3]:  # 最多使用前3个术语
                        term_results = self.search(term, days_back)
                        
                        # 添加唯一结果
                        existing_urls = {paper['url'] for paper in results}
                        for paper in term_results:
                            if paper['url'] not in existing_urls:
                                results.append(paper)
                                existing_urls.add(paper['url'])
        except Exception as e:
            print(f"生成学术搜索词时出错: {str(e)}")
        
        # Search for each subtopic if provided
        if subtopics:
            for subtopic in subtopics:
                # 将子主题翻译为英文
                english_subtopic = self._translate_to_english(subtopic)
                query = f"{english_topic} AND {english_subtopic}"
                subtopic_results = self.search(query, days_back)
                
                # Add unique papers to results
                existing_urls = {paper['url'] for paper in results}
                for paper in subtopic_results:
                    if paper['url'] not in existing_urls:
                        results.append(paper)
                        existing_urls.add(paper['url'])
        
        return results 