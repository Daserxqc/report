from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class ArticleAnalyzer:
    """文章分析器，支持并行处理文章分析"""
    
    def __init__(self, llm_processor, max_workers=4):
        self.llm_processor = llm_processor
        self.max_workers = max_workers
        self.lock = threading.Lock()
    
    def analyze_single_article(self, item: Dict, topic: str) -> str:
        """分析单篇文章"""
        try:
            if item["is_academic"]:
                analysis_prompt = f"""
                请对以下{topic}领域的学术论文进行深度分析，突出其创新点、方法论和潜在影响。
                
                标题: {item['title']}
                作者: {', '.join(item['authors'])}
                摘要: {item['summary']}
                来源: {item['source']}
                相关性: {item.get('relevance_score', '未评分')}
                论文类型: {item.get('research_type', '未分类')}
                
                分析要求:
                1. 首先确认该论文是否真正研究{topic}的核心问题，还是仅将其应用于其他领域
                2. 提炼研究的核心创新点或突破，特别关注对{topic}领域理论或方法的直接贡献
                3. 评估研究方法的有效性和新颖性
                4. 讨论研究结果对{topic}领域发展的意义和潜在影响
                5. 使用专业、客观的语言
                6. 长度控制在400-600字
                
                格式要求:
                1. 使用简洁的结构:
                   - 用1段简要介绍论文的主要内容和核心创新点
                   - 使用"**主要贡献**"作为小标题，列出1-2个核心要点
                   - 使用"**领域价值**"作为小标题，简述对领域的影响
                2. 关键术语、方法名称、重要数据请使用加粗标注
                3. 必须使用中文输出除标题外的所有内容，技术术语可在中文后附上英文原名
                4. 保持格式简洁明了，避免过多的空行和复杂结构
                """
                
                analysis_system = f"你是一位{topic}领域的资深研究员，擅长分析和评价最新的学术论文。请提供专业、简洁且中肯的分析，严格控制字数在400-600字内。所有输出必须使用中文。采用简洁明了的格式，突出核心要点。"
            else:
                analysis_prompt = f"""
                请对以下{topic}领域的研究见解进行分析和评估，提取关键信息并讨论其在领域中的意义。
                
                标题: {item['title']}
                内容概要: {item['summary']}
                来源: {item['source']}
                
                分析要求:
                1. 提取文章中的关键研究发现或见解
                2. 评估这些发现的可靠性和重要性
                3. 讨论这些见解与当前{topic}领域发展的关系
                4. 使用专业、客观的语言
                5. 长度控制在300-400字
                
                格式要求:
                1. 使用简洁的结构:
                   - 用1段简要介绍文章的主要内容和核心发现
                   - 使用"**关键见解**"作为小标题，列出1-2个要点
                   - 使用"**价值评估**"作为小标题，简述价值和影响
                2. 关键术语、方法名称、重要数据请使用加粗标注
                3. 必须使用中文输出除标题外的所有内容，技术术语可在中文后附上英文原名
                4. 保持格式简洁明了，避免过多的空行和复杂结构
                """
                
                analysis_system = f"你是一位{topic}领域的专业分析师，擅长从各种来源中提取有价值的研究见解并进行专业评估。请提供简洁明了的分析，严格控制字数在300-400字内。所有输出必须使用中文。采用简洁的格式突出核心要点。"
            
            analysis = self.llm_processor.call_llm_api(analysis_prompt, analysis_system)
            
            article_section = f"""
## {item['title']}

**{'作者: ' + ', '.join(item['authors']) + ' | ' if item['is_academic'] else ''}发布日期: {item['published']} | 来源: {item['source']}**

{analysis}

**链接**: [{item['url']}]({item['url']})
"""
            return article_section
        except Exception as e:
            with self.lock:
                print(f"分析文章 '{item['title']}' 时出错: {str(e)}")
            # 返回基本内容
            return f"""
## {item['title']}

**{'作者: ' + ', '.join(item['authors']) + ' | ' if item['is_academic'] else ''}发布日期: {item['published']} | 来源: {item['source']}**

{item['summary']}

**链接**: [{item['url']}]({item['url']})
"""
    
    def analyze_articles_parallel(self, analysis_items: List[Dict], topic: str) -> List[str]:
        """并行分析文章列表"""
        print(f"开始并行分析 {len(analysis_items)} 篇文章...")
        
        article_analyses = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有文章分析任务
            future_to_item = {
                executor.submit(self.analyze_single_article, item, topic): item 
                for item in analysis_items
            }
            
            # 收集结果，保持原始顺序
            completed_analyses = {}
            for future in as_completed(future_to_item):
                try:
                    item = future_to_item[future]
                    analysis_result = future.result()
                    # 使用文章在原列表中的索引来保持顺序
                    original_index = analysis_items.index(item)
                    completed_analyses[original_index] = analysis_result
                except Exception as e:
                    item = future_to_item[future]
                    with self.lock:
                        print(f"文章分析任务失败: {item.get('title', '未知标题')} - {str(e)}")
                    # 添加基本分析
                    original_index = analysis_items.index(item)
                    completed_analyses[original_index] = f"""
## {item['title']}

**{'作者: ' + ', '.join(item['authors']) + ' | ' if item['is_academic'] else ''}发布日期: {item['published']} | 来源: {item['source']}**

{item['summary']}

**链接**: [{item['url']}]({item['url']})
"""
        
        # 按原始顺序重新组织结果
        for i in range(len(analysis_items)):
            if i in completed_analyses:
                article_analyses.append(completed_analyses[i])
            else:
                # 如果某篇文章没有分析结果，添加基本信息
                item = analysis_items[i]
                article_analyses.append(f"""
## {item['title']}

**{'作者: ' + ', '.join(item['authors']) + ' | ' if item['is_academic'] else ''}发布日期: {item['published']} | 来源: {item['source']}**

{item['summary']}

**链接**: [{item['url']}]({item['url']})
""")
        
        print(f"文章分析完成，共处理 {len(article_analyses)} 篇文章")
        return article_analyses 