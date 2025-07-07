import os
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
import sys
from fix_md_headings import fix_markdown_headings

from collectors.arxiv_collector import ArxivCollector
from collectors.tavily_collector import TavilyCollector
from collectors.brave_search_collector import BraveSearchCollector
# 添加对学术收集器的导入，如果文件存在
try:
    from collectors.academic_collector import AcademicCollector
    has_academic_collector = True
except ImportError:
    has_academic_collector = False
from collectors.parallel_llm_processor import ParallelLLMProcessor
from generators.report_generator import ReportGenerator
import config



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
    
    # 初始化LLM处理器
    llm_processor = None
    try:
        from collectors.llm_processor import LLMProcessor
        llm_processor = LLMProcessor()
        print("✅ LLM处理器已初始化")
    except Exception as e:
        print(f"⚠️ LLM处理器初始化失败: {str(e)}")
    
    # 收集学术文章 - 首先从arXiv获取
    print("从arxiv获取学术论文...")
    arxiv_collector = ArxivCollector()
    academic_articles = arxiv_collector.get_papers_by_topic(topic, subtopics, days)
    print(f"从arXiv找到 {len(academic_articles)} 篇学术论文")
    
    # 初始化Brave搜索收集器
    brave_collector = None
    try:
        brave_collector = BraveSearchCollector()
        print("✅ Brave搜索收集器已初始化")
    except Exception as e:
        print(f"⚠️ Brave搜索收集器初始化失败: {str(e)}")
    
    # 如果有AcademicCollector，尝试从其他学术源获取论文
    additional_articles = []
    if has_academic_collector:
        try:
            print("从其他学术数据源获取补充论文...")
            academic_collector = AcademicCollector()
            
            # 尝试从CrossRef获取论文
            crossref_articles = academic_collector.search_crossref(topic, days)
            print(f"从CrossRef找到 {len(crossref_articles)} 篇论文")
            additional_articles.extend(crossref_articles)
            
            # 尝试从CORE获取论文
            core_articles = academic_collector.search_core(topic, days)
            print(f"从CORE找到 {len(core_articles)} 篇论文")
            additional_articles.extend(core_articles)
            
            # 尝试从IEEE获取论文
            ieee_articles = academic_collector.search_ieee(topic, days)
            print(f"从IEEE找到 {len(ieee_articles)} 篇论文")
            additional_articles.extend(ieee_articles)
            
            # 尝试从Semantic Scholar获取论文
            semantic_articles = academic_collector.search_semantic_scholar(topic, days)
            print(f"从Semantic Scholar找到 {len(semantic_articles)} 篇论文")
            additional_articles.extend(semantic_articles)
            
            # 去重添加到学术文章列表中
            seen_urls = {article.get('url', '') for article in academic_articles}
            for article in additional_articles:
                if article.get('url', '') not in seen_urls:
                    academic_articles.append(article)
                    seen_urls.add(article.get('url', ''))
        except Exception as e:
            print(f"从其他学术源获取论文时出错: {str(e)}")
    
    # 使用Brave搜索获取研究内容
    research_insights = []
    if brave_collector and brave_collector.has_api_key:
        try:
            print("使用Brave搜索获取研究内容...")
            brave_results = brave_collector.search_research_content(topic, days_back=days, max_results=25)
            if brave_results:
                # 去重并添加到研究见解中
                seen_urls = {article.get('url', '') for article in academic_articles + additional_articles}
                for result in brave_results:
                    if result.get('url', '') not in seen_urls:
                        result['is_research_insight'] = True
                        research_insights.append(result)
                        seen_urls.add(result.get('url', ''))
                print(f"从Brave搜索获得 {len(research_insights)} 条研究见解")
        except Exception as e:
            print(f"Brave搜索研究内容时出错: {str(e)}")
    
    # 如果研究内容不足，使用Tavily补充
    if len(research_insights) < 15:
        print("研究内容数量不足，使用Tavily补充搜索...")
        tavily_collector = TavilyCollector()
        
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
        for search_term in search_topics[:8]:  # 限制使用前8个关键词
            try:
                # 确保搜索词是纯英文，以提高搜索质量
                if hasattr(arxiv_collector, "_translate_to_english"):
                    english_topic = arxiv_collector._translate_to_english(topic)
                else:
                    english_topic = topic
                    
                query = f"{english_topic} {search_term} academic research"
                print(f"搜索: {query}")
                
                results = tavily_collector.search(query, max_results=8)
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
    
    # 使用并行LLM处理器进行分析
    if llm_processor:
        print("使用并行大模型处理器处理和组织研究数据...")
        
        # 初始化并行处理器
        parallel_processor = ParallelLLMProcessor(
            llm_processor,
            config={
                'relevance_analyzer': {'max_workers': 3},
                'article_analyzer': {'max_workers': 4}, 
                'direction_analyzer': {'max_workers': 2}
            }
        )
        
        # 执行并行分析
        analysis_results = parallel_processor.process_research_data_parallel(research_items, topic)
        
        # 提取结果
        research_directions = analysis_results.get('research_directions', f"{topic}领域的主要研究方向无法自动识别。")
        future_outlook = analysis_results.get('future_outlook', "暂无未来展望分析。")
        article_analyses = analysis_results.get('article_analyses', [])
    
    else:
        # 如果没有LLM处理器，使用基本逻辑
        research_directions = f"{topic}领域的主要研究方向无法自动识别。"
        future_outlook = "暂无未来展望分析。"
        article_analyses = []

    
    # 5. 组合所有内容
    final_content = f"""
# {topic}研究方向

## 领域概述与主要研究方向

{research_directions}

## 未来展望与发展趋势

{future_outlook}

# 主要研究论文分析

    本节选取该领域最具代表性和创新性的25-30篇核心论文进行简洁分析。

{chr(10).join(article_analyses)}
"""
    
    # 文章引用已经在并行处理器中处理完成
    
    # 6. 添加参考资料
    sources = [{"title": item['title'], "url": item['url'], "authors": item['authors'], "source": item['source']} for item in research_items]
    
    reference_section = ""
    if sources:
        reference_section = "\n\n## 参考资料\n\n"
        unique_sources = {}
        for source in sources:
            if source["url"] not in unique_sources:
                unique_sources[source["url"]] = source
        academic_sources = [s for s in unique_sources.values() if s["source"] in ["arxiv", "IEEE Xplore", "CrossRef", "CORE"] or 
                          "arxiv" in s["source"].lower() or 
                          "ieee" in s["source"].lower() or 
                          "crossref" in s["source"].lower() or 
                          "core" in s["source"].lower()]
        insight_sources = [s for s in unique_sources.values() if s not in academic_sources]
        
        ref_counter = 1
        # 添加学术论文
        if academic_sources:
            reference_section += "### 学术论文\n\n"
            for source in academic_sources:
                authors_text = ', '.join(source['authors']) if isinstance(source['authors'], list) else source['authors']
                reference_section += f"{ref_counter}. [{source['title']}]({source['url']}) - {authors_text}\n"
                ref_counter += 1
        # 添加研究见解
        if insight_sources:
            reference_section += "\n### 研究见解\n\n"
            for source in insight_sources:
                reference_section += f"{ref_counter}. [{source['title']}]({source['url']}) - {source['source']}\n"
                ref_counter += 1
        final_content += reference_section
    
    return {
        "content": final_content,
        "sources": sources,
        "date": datetime.now().strftime('%Y-%m-%d')
    }

def generate_research_report(topic, subtopics=None, days=30, output_file=None):
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
    parser.add_argument('--days', type=int, default=30, help='搜索内容的天数范围')
    parser.add_argument('--output', type=str, help='输出文件名或路径')
    
    args = parser.parse_args()
    
    # 生成报告
    generate_research_report(args.topic, args.subtopics, args.days, args.output) 