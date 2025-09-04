from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import re

from .paper_relevance_analyzer import PaperRelevanceAnalyzer
from .article_analyzer import ArticleAnalyzer
from .research_direction_analyzer import ResearchDirectionAnalyzer


class ParallelLLMProcessor:
    """并行LLM处理协调器，整合所有分析模块"""
    
    def __init__(self, llm_processor, config=None):
        self.llm_processor = llm_processor
        
        # 默认配置
        default_config = {
            'relevance_analyzer': {'max_workers': 3},
            'article_analyzer': {'max_workers': 4},
            'direction_analyzer': {'max_workers': 2}
        }
        
        self.config = {**default_config, **(config or {})}
        
        # 初始化各个分析器
        self.relevance_analyzer = PaperRelevanceAnalyzer(
            llm_processor, 
            max_workers=self.config['relevance_analyzer']['max_workers']
        )
        
        self.article_analyzer = ArticleAnalyzer(
            llm_processor, 
            max_workers=self.config['article_analyzer']['max_workers']
        )
        
        self.direction_analyzer = ResearchDirectionAnalyzer(
            llm_processor, 
            max_workers=self.config['direction_analyzer']['max_workers']
        )
    
    def process_research_data_parallel(self, research_items: List[Dict], topic: str) -> Dict[str, Any]:
        """
        并行处理研究数据的完整流程
        
        Args:
            research_items: 研究项目列表
            topic: 研究主题
            
        Returns:
            包含所有分析结果的字典
        """
        print(f"\n=== 开始并行处理 {len(research_items)} 项研究数据 ===")
        
        # 阶段1: 论文相关性分析 (如果需要)
        print("阶段1: 论文相关性分析...")
        if len(research_items) > 10:
            research_items = self.relevance_analyzer.preprocess_research_items(research_items, topic)
        
        # 准备数据用于后续分析
        research_text_with_refs, url_map = self._prepare_research_text(research_items)
        url_reference_list = self._create_url_reference_list(url_map)
        
        # 选择要分析的文章
        analysis_items = self._select_analysis_items(research_items)
        
        # 阶段2: 并行执行研究方向分析、趋势分析和文章分析
        print("阶段2: 并行执行高级分析...")
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # 提交三个主要任务
            future_directions_trends = executor.submit(
                self.direction_analyzer.analyze_directions_and_trends_parallel,
                research_text_with_refs, url_reference_list, topic
            )
            
            future_articles = executor.submit(
                self.article_analyzer.analyze_articles_parallel,
                analysis_items, topic
            )
            
            # 如果需要生成搜索关键词，也可以并行执行
            future_keywords = executor.submit(
                self._generate_search_keywords, topic
            )
            
            # 收集结果
            for future in as_completed([future_directions_trends, future_articles, future_keywords]):
                try:
                    if future == future_directions_trends:
                        research_directions, future_outlook = future.result()
                        results['research_directions'] = research_directions
                        results['future_outlook'] = future_outlook
                        print("✅ 研究方向和趋势分析完成")
                        
                    elif future == future_articles:
                        article_analyses = future.result()
                        results['article_analyses'] = article_analyses
                        print("✅ 文章分析完成")
                        
                    elif future == future_keywords:
                        search_keywords = future.result()
                        results['search_keywords'] = search_keywords
                        print("✅ 搜索关键词生成完成")
                        
                except Exception as e:
                    print(f"并行任务执行失败: {str(e)}")
                    # 设置默认值
                    if future == future_directions_trends:
                        results['research_directions'] = f"{topic}领域的主要研究方向无法自动识别。"
                        results['future_outlook'] = "暂无未来展望分析。"
                    elif future == future_articles:
                        results['article_analyses'] = []
                    elif future == future_keywords:
                        results['search_keywords'] = []
        
        # 阶段3: 后处理和链接替换
        print("阶段3: 后处理和内容整合...")
        
        # 替换文章引用为真实链接
        if 'research_directions' in results:
            results['research_directions'] = self._replace_article_references(
                results['research_directions'], url_map, research_items
            )
        
        if 'future_outlook' in results:
            results['future_outlook'] = self._replace_article_references(
                results['future_outlook'], url_map, research_items
            )
        
        # 添加元数据
        results['processed_items_count'] = len(research_items)
        results['analysis_items_count'] = len(analysis_items)
        results['url_map'] = url_map
        
        print(f"=== 并行处理完成，处理了 {len(research_items)} 项研究数据 ===\n")
        
        return results
    
    def _prepare_research_text(self, research_items: List[Dict]) -> Tuple[str, Dict]:
        """准备研究文本和URL映射"""
        research_text_with_refs = ""
        url_map = {}
        
        for idx, item in enumerate(research_items, 1):
            research_text_with_refs += f"[文章{idx}] 标题: {item['title']}\n摘要: {item['summary']}\n作者: {', '.join(item['authors'])}\n发布日期: {item['published']}\n来源: {item['source']}\nURL: {item['url']}\n\n"
            url_map[idx] = item['url']
        
        return research_text_with_refs, url_map
    
    def _create_url_reference_list(self, url_map: Dict) -> str:
        """创建URL参考列表"""
        return "\n".join([f"[文章{idx}]: {url}" for idx, url in url_map.items()])
    
    def _select_analysis_items(self, research_items: List[Dict]) -> List[Dict]:
        """选择要进行详细分析的文章"""
        # 分类文章
        academic_papers = [item for item in research_items if item.get("is_academic", False)]
        insight_articles = [item for item in research_items if item.get("is_insight", False)]
        
        # 优先选择核心论文
        core_papers = [paper for paper in academic_papers if paper.get("research_type") == "核心"]
        other_papers = [paper for paper in academic_papers if paper.get("research_type") != "核心"]
        
        # 选择最多30篇进行分析
        analysis_items = core_papers[:30]
        
        if len(analysis_items) < 30:
            other_papers.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            analysis_items.extend(other_papers[:30-len(analysis_items)])
        
        if len(analysis_items) < 25 and insight_articles:
            insight_articles.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            analysis_items.extend(insight_articles[:8])
        
        print(f"选择了 {len(analysis_items)} 篇文章进行详细分析")
        return analysis_items
    
    def _generate_search_keywords(self, topic: str) -> List[str]:
        """生成搜索关键词"""
        if not self.llm_processor:
            return ["latest research", "review paper", "research advances", "recent developments", "state of the art"]
        
        try:
            prompt = f"""
            为了搜索有关"{topic}"的最新学术研究信息，请生成5个精确的英文搜索关键词或短语。
            这些关键词应该是学术性的，能够用于找到高质量的研究论文和技术报告。
            关键词应该涵盖该领域的最新趋势、方法、技术和应用。
            仅返回关键词列表，每行一个关键词，不要添加额外解释。
            """
            
            search_keywords_text = self.llm_processor.call_llm_api(prompt)
            search_keywords = [k.strip() for k in search_keywords_text.split('\n') if k.strip()]
            
            # 清理关键词，移除数字前缀
            import re
            cleaned_keywords = []
            for keyword in search_keywords:
                cleaned = re.sub(r'^\d+\.\s*', '', keyword).strip()
                if cleaned:
                    cleaned_keywords.append(cleaned)
            
            return cleaned_keywords[:8]  # 最多返回8个关键词
            
        except Exception as e:
            print(f"生成搜索关键词时出错: {str(e)}")
            return ["latest research", "review paper", "research advances", "recent developments", "state of the art"]
    
    def _replace_article_references(self, text: str, url_map: Dict, research_items: List[Dict]) -> str:
        """替换文章引用为真实链接"""
        def replace_refs(match):
            article_num = int(match.group(1))
            if article_num in url_map:
                article_title = research_items[article_num-1]['title'] if article_num <= len(research_items) else f"文章{article_num}"
                url = url_map[article_num]
                return f"[{article_title}]({url})"
            else:
                return match.group(0)
        
        return re.sub(r'\[文章(\d+)\]', replace_refs, text) 