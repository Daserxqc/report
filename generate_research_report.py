import os
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
import sys
from fix_md_headings import fix_markdown_headings

from collectors.arxiv_collector import ArxivCollector
from collectors.tavily_collector import TavilyCollector
# 添加对学术收集器的导入，如果文件存在
try:
    from collectors.academic_collector import AcademicCollector
    has_academic_collector = True
except ImportError:
    has_academic_collector = False
from generators.report_generator import ReportGenerator
import config

def preprocess_research_items(research_items, topic, llm_processor):
    """
    预处理学术论文，评估与主题的相关性，并筛选出最相关的论文
    
    Args:
        research_items: 搜索到的论文列表
        topic: 主题
        llm_processor: LLM处理器
        
    Returns:
        筛选和评分后的论文列表
    """
    # 如果没有LLM处理器或论文数量少于阈值，不做筛选
    if not llm_processor or len(research_items) <= 5:
        return research_items
        
    print(f"正在评估{len(research_items)}篇论文与'{topic}'的相关性...")
    
    # 获取英文主题（如果原主题是中文）
    english_topic = topic
    if any('\u4e00' <= char <= '\u9fff' for char in topic):
        try:
            english_topic = llm_processor.translate_text(topic, "English")
        except:
            pass
    
    # 批处理评估，减少API调用次数
    batch_size = 5  # 每批处理的论文数
    processed_items = []
    
    for i in range(0, len(research_items), batch_size):
        batch = research_items[i:i+batch_size]
        batch_text = ""
        
        for idx, item in enumerate(batch):
            title = item.get('title', '无标题')
            summary = item.get('summary', '无摘要')
            batch_text += f"论文{idx+1}:\n标题: {title}\n摘要: {summary}\n\n"
        
        # 构建评估提示词
        system_prompt = f"""你是一位专业的{topic}领域研究专家，擅长识别真正相关的研究工作。
你的任务是评估每篇论文是否直接研究{topic}/{english_topic}领域的核心问题，而不仅仅是在其他领域中应用或浅层提及这个主题。
请特别注意区分:
1. 核心研究: 直接研究{topic}的基础理论、方法、算法、架构等
2. 应用研究: 将{topic}应用于其他领域的研究
3. 浅层提及: 仅在背景或参考中提及{topic}"""

        prompt = f"""请评估以下{len(batch)}篇论文是否真正属于{topic}/{english_topic}领域的核心研究，而非仅仅应用或提及。
对于每篇论文，给出:
1. 相关性分数(0-10，10为最高)
2. 分类(核心/应用/提及)
3. 一句话解释理由

{batch_text}

请以JSON格式回答，使用如下结构:
{{
  "评估": [
    {{
      "论文编号": 1,
      "相关性": 8,
      "分类": "核心",
      "理由": "该论文直接研究新型神经网络架构..."
    }},
    ...
  ]
}}"""

        try:
            response = llm_processor.call_llm_api(prompt, system_prompt)
            
            # 解析JSON响应
            import json
            import re
            
            # 寻找JSON部分
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)
                try:
                    evaluation = json.loads(json_str)
                    
                    # 处理每篇论文的评估结果
                    for eval_item in evaluation.get("评估", []):
                        paper_idx = eval_item.get("论文编号", 0) - 1
                        if 0 <= paper_idx < len(batch):
                            # 添加评估结果到论文数据
                            batch[paper_idx]["relevance_score"] = eval_item.get("相关性", 0)
                            batch[paper_idx]["research_type"] = eval_item.get("分类", "未知")
                            batch[paper_idx]["relevance_reason"] = eval_item.get("理由", "")
                    
                    # 添加处理后的批次到结果列表
                    processed_items.extend(batch)
                except json.JSONDecodeError:
                    print(f"无法解析评估结果JSON，跳过此批次")
                    processed_items.extend(batch)  # 添加未处理的批次
            else:
                print(f"评估结果不包含有效JSON，跳过此批次")
                processed_items.extend(batch)  # 添加未处理的批次
                
        except Exception as e:
            print(f"评估批次出错: {str(e)}")
            processed_items.extend(batch)  # 添加未处理的批次
    
    # 按相关性分数排序，分数相同时核心研究优先
    def sort_key(item):
        score = item.get("relevance_score", 0)
        type_score = {"核心": 2, "应用": 1, "提及": 0, "未知": 0}
        return (score, type_score.get(item.get("research_type", "未知"), 0))
    
    processed_items.sort(key=sort_key, reverse=True)
    
    # 输出评估结果统计
    core_count = sum(1 for item in processed_items if item.get("research_type") == "核心")
    app_count = sum(1 for item in processed_items if item.get("research_type") == "应用")
    mention_count = sum(1 for item in processed_items if item.get("research_type") == "提及")
    
    print(f"论文相关性评估结果: 核心研究 {core_count} 篇, 应用研究 {app_count} 篇, 浅层提及 {mention_count} 篇")
    
    # 保留所有核心研究和高分应用研究
    filtered_items = [
        item for item in processed_items 
        if item.get("research_type") == "核心" or 
           (item.get("research_type") == "应用" and item.get("relevance_score", 0) >= 7)
    ]
    
    # 如果筛选后论文过少，则放宽标准
    if len(filtered_items) < 5:
        filtered_items = [
            item for item in processed_items 
            if item.get("relevance_score", 0) >= 5
        ]
    
    print(f"筛选后保留 {len(filtered_items)} 篇最相关论文")
    return filtered_items

def get_research_data(topic, subtopics=None, days=7):
    """
    获取研究数据并进行深度处理
    
    Args:
        topic (str): 主题
        subtopics (list): 子主题列表
        days (int): 天数范围
        
    Returns:
        dict: 包含处理后的研究内容和来源的字典
    """
    print(f"\n=== 收集{topic}领域的最新研究方向 ===")
    print(f"子主题: {subtopics if subtopics else '无'}")
    print(f"时间范围: {days}天")
    
    # 收集学术文章 - 首先从arXiv获取
    print("从arxiv获取学术论文...")
    arxiv_collector = ArxivCollector()
    academic_articles = arxiv_collector.get_papers_by_topic(topic, subtopics, days)
    print(f"从arXiv找到 {len(academic_articles)} 篇学术论文")
    
    # 如果有AcademicCollector，尝试从其他学术源获取论文
    additional_articles = []
    if has_academic_collector:
        try:
            print("从其他学术数据源获取补充论文...")
            academic_collector = AcademicCollector()
            
            # # 尝试从IEEE获取论文
            # ieee_articles = academic_collector.search_ieee(topic, days)
            # print(f"从IEEE Xplore找到 {len(ieee_articles)} 篇论文")
            # additional_articles.extend(ieee_articles)
            
            # 尝试从CrossRef获取论文
            crossref_articles = academic_collector.search_crossref(topic, days)
            print(f"从CrossRef找到 {len(crossref_articles)} 篇论文")
            additional_articles.extend(crossref_articles)
            
            # 尝试从CORE获取论文
            core_articles = academic_collector.search_core(topic, days)
            print(f"从CORE找到 {len(core_articles)} 篇论文")
            additional_articles.extend(core_articles)
            
            # 去重添加到学术文章列表中
            existing_urls = {paper['url'] for paper in academic_articles}
            for paper in additional_articles:
                if paper['url'] not in existing_urls:
                    academic_articles.append(paper)
                    existing_urls.add(paper['url'])
                    
            print(f"总共收集到 {len(academic_articles)} 篇学术论文")
        except Exception as e:
            print(f"从其他学术源获取论文时出错: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    # 初始化tavily收集器和LLM处理器
    tavily_collector = TavilyCollector()
    llm_processor = tavily_collector._get_llm_processor()
    
    # 如果学术文章不足，补充研究见解
    research_insights = []
    if len(academic_articles) < 5:
        print("学术文章数量不足，补充搜索研究见解...")
        
        # 使用LLM生成更精准的搜索关键词
        if llm_processor:
            try:
                # 生成英文学术搜索关键词
                prompt = f"""
                为了搜索有关"{topic}"的最新学术研究信息，请生成5个精确的英文搜索关键词或短语。
                这些关键词应该是学术性的，能够用于找到高质量的研究论文和技术报告。
                关键词应该涵盖该领域的最新趋势、方法、技术和应用。
                仅返回关键词列表，每行一个关键词，不要添加额外解释。
                """
                
                search_keywords = llm_processor.call_llm_api(prompt)
                # 处理返回的关键词，移除数字前缀和额外空白
                import re
                search_keywords = re.sub(r'^\d+\.\s*', '', search_keywords, flags=re.MULTILINE)
                search_topics = [k.strip() for k in search_keywords.split('\n') if k.strip()]
                
                print(f"生成的学术搜索关键词: {search_topics}")
            except Exception as e:
                print(f"生成搜索关键词时出错: {str(e)}")
                # 使用默认关键词
                search_topics = ["latest research", "review paper", "research advances", "recent developments", "state of the art"]
        else:
            # 如果没有LLM处理器，使用默认搜索主题
            search_topics = ["latest research", "review paper", "research advances", "recent developments", "state of the art"]
            
        # 如果提供了子主题，也加入搜索
        if subtopics:
            for subtopic in subtopics:
                # 将子主题翻译为英文搜索关键词
                if hasattr(arxiv_collector, "_translate_to_english"):
                    english_subtopic = arxiv_collector._translate_to_english(subtopic)
                    search_topics.append(f"{english_subtopic} research")
        
        # 使用生成的关键词进行搜索
        for search_term in search_topics[:5]:  # 限制使用前5个关键词
            try:
                # 确保搜索词是纯英文，以提高搜索质量
                if hasattr(arxiv_collector, "_translate_to_english"):
                    english_topic = arxiv_collector._translate_to_english(topic)
                else:
                    english_topic = topic
                    
                query = f"{english_topic} {search_term} academic research"
                print(f"搜索: {query}")
                
                results = tavily_collector.search(query, max_results=3)
                for result in results:
                    # 确保内容不重复
                    if any(r.get('url') == result.get('url') for r in research_insights):
                        continue
                    # 标记为研究见解来源
                    result['is_research_insight'] = True
                    research_insights.append(result)
            except Exception as e:
                print(f"搜索'{search_term}'时出错: {str(e)}")
    
    print(f"从网络搜索获取了 {len(research_insights)} 条研究见解")
    
    # 合并所有研究数据
    all_research_data = academic_articles + research_insights
    
    # 添加相关性预处理步骤
    if llm_processor:
        # 对学术论文进行相关性评估和筛选
        print("对学术论文进行相关性预处理...")
        academic_articles = preprocess_research_items(academic_articles, topic, llm_processor)
        
        # 如果需要，也可以对研究见解进行筛选
        if research_insights:
            print("对研究见解进行相关性预处理...")
            research_insights = preprocess_research_items(research_insights, topic, llm_processor)
            
        # 更新合并后的数据
        all_research_data = academic_articles + research_insights
    
    if not all_research_data:
        print("未找到任何相关研究数据，返回空结果")
        return {
            "content": f"# {topic}研究方向\n\n未找到相关研究数据。",
            "sources": [],
            "date": datetime.now().strftime('%Y-%m-%d')
        }
    
    # 如果LLM处理器不可用，返回基本结果
    if not llm_processor:
        print("警告: LLM处理器未初始化，无法进行高级内容处理")
        basic_content = f"# {topic}研究方向\n\n"
        sources = []
        
        # 先处理学术文章
        if academic_articles:
            basic_content += "## 学术论文\n\n"
            for i, article in enumerate(academic_articles):
                title = article.get('title', '无标题')
                content = article.get('summary', article.get('content', '无内容'))
                url = article.get('url', '#')
                authors = ', '.join(article.get('authors', ['未知'])) if isinstance(article.get('authors', []), list) else '未知'
                published = article.get('published', datetime.now().strftime('%Y-%m-%d'))
                source = article.get('source', '未知来源')
                
                basic_content += f"### {i+1}. {title}\n\n"
                basic_content += f"**作者**: {authors} | **日期**: {published} | **来源**: {source}\n\n"
                basic_content += f"{content}\n\n"
                basic_content += f"**链接**: [{url}]({url})\n\n"
                
                sources.append({
                    "title": title,
                    "url": url
                })
        
        # 再处理研究见解
        if research_insights:
            basic_content += "## 研究见解\n\n"
            for i, article in enumerate(research_insights):
                title = article.get('title', '无标题')
                content = article.get('content', '无内容')
                url = article.get('url', '#')
                source = article.get('source', '网络搜索')
                
                basic_content += f"### {i+1}. {title}\n\n"
                basic_content += f"**来源**: {source}\n\n"
                basic_content += f"{content}\n\n"
                basic_content += f"**链接**: [{url}]({url})\n\n"
                
                sources.append({
                    "title": title,
                    "url": url
                })
        
        return {
            "content": basic_content,
            "sources": sources,
            "date": datetime.now().strftime('%Y-%m-%d')
        }
    
    # 使用LLM处理数据，生成高质量研究报告
    print("使用大模型处理和组织研究数据...")
    
    # 1. 提取和规范化研究数据
    research_items = []
    for article in all_research_data:
        item = {
            "title": article.get('title', '无标题'),
            "authors": article.get('authors', ['未知']) if isinstance(article.get('authors', []), list) else ['未知'],
            "summary": article.get('summary', article.get('content', '无内容')),
            "url": article.get('url', '#'),
            "published": article.get('published', datetime.now().strftime('%Y-%m-%d')),
            "source": article.get('source', '未知来源'),
            "is_academic": 'arxiv' in article.get('source', '').lower() or 
                         'ieee' in article.get('source', '').lower() or 
                         'crossref' in article.get('source', '').lower(),
            "is_insight": article.get('is_research_insight', False)
        }
        research_items.append(item)
    
    # 2. 使用LLM识别和分类主要研究方向
    research_text = "\n\n".join([
        f"标题: {item['title']}\n摘要: {item['summary']}\n作者: {', '.join(item['authors'])}\n发布日期: {item['published']}\n来源: {item['source']}"
        for item in research_items
    ])
    
    # 识别研究方向
    directions_prompt = f"""
    请分析以下{topic}领域的研究文章，识别出3-5个主要研究方向或子领域，并为每个方向提供简短描述。
    
    {research_text}
    
    在分析时，请注意:
    1. 专注于{topic}的核心研究方向，忽略仅将其应用于其他领域的研究
    2. 确保每个研究方向都是{topic}领域自身的发展路径，而非其他学科借用{topic}方法
    3. 分析每个方向有多少篇论文支持，优先选择多篇论文共同体现的方向
    4. 考虑方向的重要性、创新性和未来发展潜力
    
    输出要求:
    1. 明确列出3-5个主要研究方向
    2. 每个方向提供3-5句话描述其核心关注点和重要性
    3. 按研究活跃度或前沿程度排序
    4. 对所有研究方向的来源进行标注，提供来源的链接
    5. 采用统一的markdown格式输出:
       - 研究方向名称使用**加粗**文本
       - 使用有序列表(1., 2., 3.)标注每个方向
       - 每个研究方向的子项使用无序列表(• 或-)
       - 对重要概念进行适当强调
       - 在每个研究方向之间添加两行以上空行，确保足够的间距
       - 在要点描述之间也添加适当空行
    6. 必须使用中文输出所有内容，包括研究方向名称也应翻译成中文（可附英文原名）
    7. 对每个要点或关键发现，必须添加真实的论文来源链接，格式为[链接](真实URL)。必须引用原文提供的真实完整URL，绝不能使用'https://arxiv.org/abs/'这样的不完整URL或虚构URL
    """
    
    directions_system = f"""你是一位专业的{topic}领域研究专家，擅长分析和总结研究趋势。
请基于提供的研究文章，提取{topic}领域的主要研究方向。

重要提示:
1. 只关注真正属于{topic}核心领域的研究，忽略只是应用或浅层提及的内容
2. 区分主要研究方向与边缘应用场景
3. 确保识别的方向有足够的科研支持，不是个别论文的偶然主题
4. 确保方向之间有足够的差异性，避免重复
5. 遵循统一的格式规范:
   - 每个研究方向使用编号和**加粗标题**
   - 关键点使用• 或-列表呈现
   - 保持一致的格式和结构
   - 确保足够的空行和间距，使内容易于阅读
   - 在每个要点后添加空行
6. 所有输出内容必须使用中文，如有必要可在中文名称后附上英文原名
7. 必须使用提供的研究文章中的真实URL作为引用链接，绝对不要使用虚构的URL或通用URL模板。确保每个URL都是完整且实际存在的链接。"""
    
    try:
        research_directions = llm_processor.call_llm_api(directions_prompt, directions_system)
    except Exception as e:
        print(f"识别研究方向时出错: {str(e)}")
        research_directions = f"{topic}领域的主要研究方向无法自动识别。"
    
    # 3. 为每个研究文章生成详细分析，优先分析学术论文
    # 首先对研究项目按类型和相关性排序
    academic_papers = [item for item in research_items if item["is_academic"]]
    insight_articles = [item for item in research_items if item["is_insight"]]
    
    # 修改为最多3-4篇文章进行详细分析，优先选择核心学术论文
    # 首先按照研究类型排序
    core_papers = [paper for paper in academic_papers if paper.get("research_type") == "核心"]
    other_papers = [paper for paper in academic_papers if paper.get("research_type") != "核心"]
    
    # 优先选择核心论文，最多选择4篇
    analysis_items = core_papers[:4]
    
    # 如果核心论文不足4篇，添加其他高相关性论文直到达到4篇
    if len(analysis_items) < 4:
        # 按相关性分数对其他论文排序
        other_papers.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        analysis_items.extend(other_papers[:4-len(analysis_items)])
    
    # 如果学术论文总数不足4篇，可以添加1篇研究见解
    if len(analysis_items) < 3 and insight_articles:
        # 按相关性排序研究见解
        insight_articles.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        analysis_items.extend(insight_articles[:1])
    
    print(f"选择了 {len(analysis_items)} 篇论文进行详细分析")
    
    article_analyses = []
    for item in analysis_items:
        try:
            # 根据文章类型调整分析提示
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
                6. 长度控制在300-500字
                
                格式要求:
                1. 使用以下统一的章节结构:
                   - 先用1-2段简要介绍论文的主要内容和领域相关性
                   - 然后使用"**核心创新点**"作为小标题，列出2-3个要点，每个要点用• 或-列表标记
                   - 使用"**方法论评估**"作为小标题，分析方法的优势
                   - 使用"**领域影响**"作为小标题，总结影响
                2. 关键术语、方法名称、重要数据请使用加粗或斜体标注
                3. 保持整体格式的一致性
                4. 必须使用中文输出除标题外的所有内容，技术术语可在中文后附上英文原名
                5. 增加适当空行和间距:
                   - 段落之间空一行
                   - 小标题前空一行
                   - 列表项之间适当留白
                   - 不同章节之间有明确分隔
                """
                
                analysis_system = f"你是一位{topic}领域的资深研究员，擅长分析和评价最新的学术论文。请提供专业、深入且中肯的分析，并严格遵循格式要求，保持一致的结构和样式。所有输出必须使用中文。注重排版的清晰和美观，保持足够的空间和间距。"
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
                5. 长度控制在250-400字
                
                格式要求:
                1. 使用以下统一的章节结构:
                   - 先用1-2段简要介绍文章的主要内容和领域相关性
                   - 然后使用"**核心见解**"作为小标题，列出2-3个要点，每个要点用• 或-列表标记
                   - 使用"**价值评估**"作为小标题，分析内容的价值
                   - 使用"**领域影响**"作为小标题，总结影响
                2. 关键术语、方法名称、重要数据请使用加粗或斜体标注
                3. 保持整体格式的一致性
                4. 必须使用中文输出除标题外的所有内容，技术术语可在中文后附上英文原名
                5. 增加适当空行和间距:
                   - 段落之间空一行
                   - 小标题前空一行
                   - 列表项之间适当留白
                   - 不同章节之间有明确分隔
                """
                
                analysis_system = f"你是一位{topic}领域的专业分析师，擅长从各种来源中提取有价值的研究见解并进行专业评估。请严格遵循格式要求，保持一致的结构和样式。所有输出必须使用中文。注重排版的清晰和美观，保持足够的空间和间距。"
            
            analysis = llm_processor.call_llm_api(analysis_prompt, analysis_system)
            
            article_section = f"""
## {item['title']}

**{'作者: ' + ', '.join(item['authors']) + ' | ' if item['is_academic'] else ''}发布日期: {item['published']} | 来源: {item['source']}**

{analysis}

**链接**: [{item['url']}]({item['url']})
"""
            article_analyses.append(article_section)
        except Exception as e:
            print(f"分析文章 '{item['title']}' 时出错: {str(e)}")
            # 添加基本内容
            article_analyses.append(f"""
## {item['title']}

**{'作者: ' + ', '.join(item['authors']) + ' | ' if item['is_academic'] else ''}发布日期: {item['published']} | 来源: {item['source']}**

{item['summary']}

**链接**: [{item['url']}]({item['url']})
""")
    
    # 4. 生成整体趋势和未来展望分析
    future_prompt = f"""
    基于以下{topic}领域的最新研究文章，请分析该领域的核心发展趋势和未来研究方向。
    
    {research_text}
    
    请提供:
    1. {topic}领域核心技术和方法的发展趋势，而非应用领域的扩展
    2. 未来3-5年在{topic}基础理论和核心方法上可能出现的突破性进展
    3. {topic}领域本身(而非其应用)面临的主要挑战和机遇
    4. 对该领域研究者的建议，聚焦如何推动{topic}的基础发展
    
    要求:
    - 使用专业、客观的语言
    - 有理有据，避免无根据的猜测
    - 长度控制在700-900字
    - 必须使用中文输出除标题外的所有内容，技术术语可在中文后附上英文原名
    - 使用清晰的段落划分，每个观点之间空一行
    - 重要观点可以使用**加粗**或*斜体*强调
    - 分点表述时使用编号或项目符号，并保持一致的格式
    - 必须使用提供的研究文章中的真实完整URL作为引用链接，格式为[链接](真实URL)。绝不能使用不完整URL或虚构URL。
    """
    
    future_system = f"""你是一位权威的{topic}领域趋势分析专家，擅长分析研究动态并预测未来发展。
请基于最新文献提供深入的趋势分析，专注于该领域的核心发展方向，而非应用场景。
区分{topic}领域自身的发展趋势与其在其他领域的应用趋势。
注重排版的清晰和美观，保持适当的空行和间距，使内容更易于阅读。
最重要的是：必须使用真实完整的文献URL进行引用，绝不能使用'https://arxiv.org/abs/'这样的不完整URL或虚构URL。每个链接必须直接引用原始文献的实际网址。"""
    
    try:
        future_outlook = llm_processor.call_llm_api(future_prompt, future_system)
    except Exception as e:
        print(f"生成未来展望时出错: {str(e)}")
        future_outlook = "暂无未来展望分析。"
    
    # 5. 组合所有内容
    final_content = f"""
# {topic}研究方向

## 领域概述与主要研究方向

{research_directions}

## 未来展望与发展趋势

{future_outlook}

# 主要研究论文分析

本节选取该领域最具代表性和创新性的3-4篇核心论文进行深入分析。

{'\n\n'.join(article_analyses)}
"""
    
    # 6. 添加参考资料 - 修改这部分来包含所有被引用的资料
    sources = [{"title": item['title'], "url": item['url'], "authors": item['authors'], "source": item['source']} for item in research_items]
    
    if sources:
        reference_section = "\n\n## 参考资料\n\n"
        
        # 收集所有独特的来源，确保没有重复
        unique_sources = {}
        for source in sources:
            if source["url"] not in unique_sources:
                unique_sources[source["url"]] = source
        
        # 分别列出学术论文和研究见解
        academic_sources = [s for s in unique_sources.values() if s["source"] in ["arxiv", "IEEE Xplore", "CrossRef", "CORE"] or 
                          "arxiv" in s["source"].lower() or 
                          "ieee" in s["source"].lower() or 
                          "crossref" in s["source"].lower() or 
                          "core" in s["source"].lower()]
        
        insight_sources = [s for s in unique_sources.values() if s not in academic_sources]
        
        # 添加学术论文
        if academic_sources:
            reference_section += "### 学术论文\n\n"
            for i, source in enumerate(academic_sources):
                authors_text = ', '.join(source['authors']) if isinstance(source['authors'], list) else source['authors']
                reference_section += f"{i+1}. [{source['title']}]({source['url']}) - {authors_text}\n"
                
        # 添加研究见解
        if insight_sources:
            reference_section += "\n### 研究见解\n\n"
            for i, source in enumerate(insight_sources):
                reference_section += f"{i+1}. [{source['title']}]({source['url']}) - {source['source']}\n"
                
        final_content += reference_section
    
    return {
        "content": final_content,
        "sources": sources,
        "date": datetime.now().strftime('%Y-%m-%d')
    }

def generate_research_report(topic, subtopics=None, days=7, output_file=None):
    """
    生成研究方向报告
    
    Args:
        topic (str): 主题
        subtopics (list): 子主题列表
        days (int): 天数范围
        output_file (str): 输出文件名或路径
        
    Returns:
        tuple: (报告文件路径, 报告数据)
    """
    # 确保输出目录存在
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    # 获取并处理研究数据
    research_data = get_research_data(topic, subtopics, days)
    
    # 确定输出文件路径
    if not output_file:
        # 如果没有提供输出文件，使用默认命名
        date_str = datetime.now().strftime('%Y%m%d')
        output_file = os.path.join(config.OUTPUT_DIR, f"{topic.replace(' ', '_').lower()}_research_report_{date_str}.md")
    elif not os.path.isabs(output_file):
        # 如果提供的是相对路径，确保正确拼接
        # 检查输出文件所在目录是否存在
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
    
    # 写入报告
    with open(output_file, 'w', encoding='utf-8-sig') as f:
        f.write(research_data["content"])
    
    print(f"\n=== 研究方向报告生成完成 ===")
    print(f"报告已保存至: {output_file}")
    
    # 修复报告中的标题问题
    print("正在优化报告标题格式...")
    fix_markdown_headings(output_file)
    
    return output_file, research_data

if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='生成研究方向报告')
    parser.add_argument('--topic', type=str, required=True, help='报告的主题')
    parser.add_argument('--subtopics', type=str, nargs='*', help='与主题相关的子主题')
    parser.add_argument('--days', type=int, default=7, help='搜索内容的天数范围')
    parser.add_argument('--output', type=str, help='输出文件名或路径')
    
    args = parser.parse_args()
    
    # 生成报告
    generate_research_report(args.topic, args.subtopics, args.days, args.output) 