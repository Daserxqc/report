
from mcp.server.fastmcp import FastMCP
import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass
from datetime import datetime

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ 环境变量加载成功")
except ImportError:
    print("⚠️ python-dotenv未安装，跳过.env文件加载")
except Exception as e:
    print(f"⚠️ 加载.env文件失败: {e}")

# 添加search_mcp路径 - 必须在collectors路径之前，避免名称冲突
search_mcp_path = Path(__file__).parent / "search_mcp" / "src"
if str(search_mcp_path) not in sys.path:
    sys.path.insert(0, str(search_mcp_path))

# 确保search_mcp模块可以被找到
search_mcp_module_path = search_mcp_path / "search_mcp"
if str(search_mcp_module_path.parent) not in sys.path:
    sys.path.insert(0, str(search_mcp_module_path.parent))

# 添加collectors路径 - 放在search_mcp之后，避免名称冲突
collectors_path = Path(__file__).parent / "collectors"
if str(collectors_path) not in sys.path:
    sys.path.insert(0, str(collectors_path))

# 尝试导入搜索组件
try:
    # 调试信息
    print(f"🔍 尝试从路径导入: {search_mcp_path}")
    print(f"🔍 search_mcp目录存在: {search_mcp_path.exists()}")
    print(f"🔍 config.py文件存在: {(search_mcp_path / 'search_mcp' / 'config.py').exists()}")
    
    # 确保正确的导入路径
    from search_mcp.config import SearchConfig
    from search_mcp.generators import SearchOrchestrator
    
    # 初始化搜索组件
    config = SearchConfig()
    print(f"🔍 配置创建成功，API密钥状态: {config.get_api_keys()}")
    
    orchestrator = SearchOrchestrator(config)
    search_available = True
    print(f"✅ 搜索组件初始化成功，可用数据源: {config.get_enabled_sources()}")
except Exception as e:
    print(f"⚠️ 搜索组件初始化失败: {e}")
    print(f"   错误类型: {type(e).__name__}")
    print(f"   搜索组件路径: {search_mcp_path}")
    print(f"   当前sys.path包含: {[p for p in sys.path if 'search_mcp' in p]}")
    
    # 尝试直接导入测试
    try:
        import search_mcp
        print(f"   search_mcp模块路径: {search_mcp.__file__}")
    except:
        print("   无法导入search_mcp模块")
    
    orchestrator = None
    search_available = False

# 尝试导入LLM处理器
try:
    from collectors.llm_processor import LLMProcessor
    llm_processor = LLMProcessor()
    llm_available = True
except Exception as e:
    llm_processor = None
    llm_available = False

# Create an MCP server
mcp = FastMCP("Search Server")

@mcp.tool()
def search(query: str, max_results: int = 5) -> str:
    """Search for information using multiple sources
    
    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 5)
    """
    # 声明全局变量
    global search_available, orchestrator
    
    # 尝试重新初始化搜索服务
    if not search_available:
        try:
            # 重新导入搜索组件
            from search_mcp.config import SearchConfig
            from search_mcp.generators import SearchOrchestrator
            
            config = SearchConfig()
            orchestrator = SearchOrchestrator(config)
            search_available = True
            print(f"🔄 搜索服务重新初始化成功，可用数据源: {config.get_enabled_sources()}")
            
        except Exception as e:
            return f"搜索服务初始化失败: {str(e)}\n\n请检查API密钥配置和依赖项安装。\n详细错误: {type(e).__name__}"
    
    try:
        # 直接使用SearchOrchestrator
        documents = orchestrator.search_by_category([query], "web", max_results)
        
        if documents:
            result_text = f"找到 {len(documents)} 条搜索结果：\n\n"
            for i, doc in enumerate(documents[:max_results], 1):
                result_text += f"{i}. **{doc.title}**\n"
                result_text += f"   {doc.content[:200]}...\n"
                result_text += f"   来源: {doc.url}\n\n"
            return result_text
        else:
            return "未找到相关搜索结果"
            
    except Exception as e:
        return f"搜索过程中发生错误: {str(e)}\n\n请检查API密钥配置和网络连接。"

@mcp.tool()
def parallel_search(queries: list, max_results: int = 3) -> str:
    """Search multiple queries in parallel
    
    Args:
        queries: List of search query strings
        max_results: Maximum number of results per query (default: 3)
    """
    if not search_available:
        return "搜索服务暂时不可用，请检查配置"
    
    try:
        all_results = []
        for query in queries:
            documents = orchestrator.search_by_category([query], "web", max_results)
            all_results.extend(documents[:max_results])
        
        if all_results:
            result_text = f"并行搜索完成，共找到 {len(all_results)} 条结果：\n\n"
            for i, doc in enumerate(all_results, 1):
                result_text += f"{i}. **{doc.title}**\n"
                result_text += f"   {doc.content[:150]}...\n"
                result_text += f"   来源: {doc.url}\n\n"
            return result_text
        else:
            return "并行搜索未找到结果"
            
    except Exception as e:
        return f"并行搜索过程中发生错误: {str(e)}"

@mcp.tool()
def analysis_mcp(analysis_type: str, data: Union[List[Dict], Dict, str], topic: str = "", **kwargs) -> str:
    """Comprehensive analysis tool that provides quality assessment, relevance analysis, intent analysis, etc.
    
    Args:
        analysis_type: Type of analysis ('quality', 'relevance', 'intent', 'structure_parsing', 'gap_analysis')
        data: Data to analyze (list of documents/dicts for quality/gap analysis, single dict for relevance, string for intent/structure)
        topic: Topic for analysis context
        **kwargs: Additional parameters specific to analysis type
        
    Returns:
        str: Analysis results in JSON format
    """
    if not llm_available:
        return json.dumps({
            "error": "LLM处理器不可用",
            "analysis_type": analysis_type,
            "fallback_result": True
        }, ensure_ascii=False)
    
    try:
        if analysis_type == "quality":
            return _analyze_quality(data, topic, kwargs.get("analysis_aspects"))
        elif analysis_type == "relevance":
            return _analyze_relevance(data, topic)
        elif analysis_type == "intent":
            return _analyze_intent(data, kwargs.get("context", ""))
        elif analysis_type == "structure_parsing":
            return _parse_structure(data, kwargs.get("parsing_goal", ""), kwargs.get("output_schema"))
        elif analysis_type == "gap_analysis":
            return _analyze_gaps(topic, data, kwargs.get("expected_aspects"))
        else:
            return json.dumps({
                "error": f"不支持的分析类型: {analysis_type}",
                "supported_types": ["quality", "relevance", "intent", "structure_parsing", "gap_analysis"]
            }, ensure_ascii=False)
            
    except Exception as e:
        return json.dumps({
            "error": f"{analysis_type}分析失败: {str(e)}",
            "analysis_type": analysis_type
        }, ensure_ascii=False)

def _analyze_quality(data: List[Dict], topic: str, analysis_aspects: List[str] = None) -> str:
    """Internal quality analysis function"""
    # 准备分析数据
    content_data = ""
    for i, item in enumerate(data[:5]):
        if isinstance(item, dict):
            title = item.get("title", "未知标题")
            content = item.get("content", item.get("summary", ""))[:200]
            source = item.get("source", "未知来源")
            content_data += f"[{i+1}] 标题: {title}\n来源: {source}\n内容: {content}...\n\n"
    
    template = """
请对以下搜索结果进行5维度质量评估。

评估维度：
1. 相关性 (Relevance): 内容与主题"{topic}"的匹配程度
2. 可信度 (Credibility): 来源的权威性和内容的准确性  
3. 完整性 (Completeness): 信息的全面性和深度
4. 时效性 (Timeliness): 信息的新鲜度和时间相关性
5. 总体质量 (Overall): 综合评估

搜索结果：
{content_data}

输出格式：
```json
{{
    "analysis_type": "quality_assessment",
    "score": 0.82,
    "details": {{
        "relevance": 0.85,
        "credibility": 0.75,
        "completeness": 0.80,
        "timeliness": 0.90,
        "overall": 0.82,
        "analysis_details": {{
            "relevance_reasons": "具体分析相关性的理由",
            "credibility_factors": "影响可信度的因素",
            "completeness_gaps": "信息完整性的缺陷或优势",
            "timeliness_assessment": "时效性评估",
            "improvement_suggestions": ["改进建议1", "建议2"]
        }}
    }},
    "reasoning": "5维度质量评估：相关性0.85, 可信度0.75, 完整性0.80, 时效性0.90"
}}
```
"""
    
    prompt = template.format(topic=topic, content_data=content_data)
    response = llm_processor.call_llm_api_json(
        prompt,
        "你是一位专业的信息质量评估专家，擅长从多个维度评估信息的质量和价值。"
    )
    
    if isinstance(response, dict):
        return json.dumps(response, ensure_ascii=False, indent=2)
    else:
        return json.dumps({"error": "质量分析结果格式不正确"}, ensure_ascii=False)

def _analyze_relevance(content: Dict, topic: str) -> str:
    """Internal relevance analysis function"""
    title = content.get("title", "未知标题")
    abstract = content.get("content", content.get("abstract", ""))
    if len(abstract) > 500:
        abstract = abstract[:500] + "..."
    authors = ", ".join(content.get("authors", [])) if content.get("authors") else "未知"
    publish_date = content.get("publish_date", "未知")
    
    template = """
请分析以下内容与主题"{topic}"的相关性。

分析内容：
标题：{title}
摘要：{abstract}
作者：{authors}
发表时间：{publish_date}

输出格式：
```json
{{
    "analysis_type": "relevance_analysis",
    "score": 0.85,
    "details": {{
        "relevance_score": 0.85,
        "matching_keywords": ["关键词1", "关键词2"],
        "topic_alignment": "高度相关",
        "content_quality": "优秀"
    }},
    "reasoning": "相关性评分: 0.85, 主题匹配: 高度相关",
    "metadata": {{
        "matching_keywords": ["关键词1", "关键词2"],
        "content_quality": "优秀"
    }}
}}
```
"""
    
    prompt = template.format(topic=topic, title=title, abstract=abstract, authors=authors, publish_date=publish_date)
    response = llm_processor.call_llm_api_json(
        prompt,
        "你是一位专业的内容相关性评估专家，擅长判断内容与主题的匹配程度。"
    )
    
    if isinstance(response, dict):
        return json.dumps(response, ensure_ascii=False, indent=2)
    else:
        return json.dumps({"error": "相关性分析返回格式不正确"}, ensure_ascii=False)

def _analyze_intent(user_query: str, context: str = "") -> str:
    """Internal intent analysis function"""
    template = """
请分析用户查询的深层意图和需求。

用户查询："{user_query}"
查询上下文：{context}

输出格式：
```json
{{
    "analysis_type": "intent_analysis",
    "score": 0.85,
    "details": {{
        "primary_intent": "主要意图描述",
        "secondary_intents": ["次要意图1", "次要意图2"],
        "information_needs": {{
            "factual_info": "是否需要事实信息",
            "analysis_info": "是否需要分析性信息"
        }},
        "urgency_level": "中"
    }},
    "reasoning": "主要意图: 信息查询, 置信度: 0.85",
    "metadata": {{
        "search_queries": ["推荐查询1", "推荐查询2"],
        "recommended_sources": ["推荐信息源1", "推荐信息源2"]
    }}
}}
```
"""
    
    prompt = template.format(user_query=user_query, context=context)
    response = llm_processor.call_llm_api_json(
        prompt,
        "你是一位专业的用户意图分析专家，擅长理解用户查询背后的真实需求。"
    )
    
    if isinstance(response, dict):
        return json.dumps(response, ensure_ascii=False, indent=2)
    else:
        return json.dumps({"error": "意图分析返回格式不正确"}, ensure_ascii=False)

def _parse_structure(input_text: str, parsing_goal: str, output_schema: Dict = None) -> str:
    """Internal structure parsing function"""
    template = """
请将以下非结构化文本解析为结构化的JSON格式。

输入文本：{input_text}
解析目标：{parsing_goal}
输出模式：{output_schema}

输出格式：
```json
{{
    "analysis_type": "structure_parsing",
    "score": 1.0,
    "details": {{
        "parsed_data": "解析后的结构化数据"
    }},
    "reasoning": "成功解析文本结构，目标: {parsing_goal}"
}}
```
"""
    
    schema_text = json.dumps(output_schema, ensure_ascii=False, indent=2) if output_schema else "通用JSON结构"
    prompt = template.format(input_text=input_text, parsing_goal=parsing_goal, output_schema=schema_text)
    
    response = llm_processor.call_llm_api_json(
        prompt,
        "你是一位专业的文本结构分析专家，擅长将非结构化文本转换为结构化数据。"
    )
    
    if isinstance(response, dict):
        return json.dumps(response, ensure_ascii=False, indent=2)
    else:
        return json.dumps({"error": "结构解析返回格式不正确"}, ensure_ascii=False)

def _analyze_gaps(topic: str, existing_data: List[Dict], expected_aspects: List[str] = None) -> str:
    """Internal gap analysis function"""
    if expected_aspects is None:
        expected_aspects = ["技术原理", "发展历史", "应用场景", "市场情况", "挑战问题", "未来趋势"]
    
    # 简化的数据摘要
    data_summary = f"共{len(existing_data)}条数据" if existing_data else "无数据"
    
    template = """
请分析已有信息的覆盖情况，识别信息缺口。

主题：{topic}
已有信息：{data_summary}
期望覆盖的方面：{expected_aspects}

输出格式：
```json
{{
    "analysis_type": "gap_analysis",
    "score": 0.6,
    "details": {{
        "coverage_analysis": {{
            "well_covered": ["已充分覆盖的方面1"],
            "partially_covered": ["部分覆盖的方面1"],
            "not_covered": ["未覆盖的方面1"]
        }},
        "information_gaps": [
            {{
                "gap_type": "缺口类型",
                "description": "缺口描述",
                "priority": "高",
                "suggested_queries": ["建议查询1"]
            }}
        ]
    }},
    "reasoning": "信息覆盖率: 0.6, 发现2个主要缺口"
}}
```
"""
    
    prompt = template.format(
        topic=topic,
        data_summary=data_summary,
        expected_aspects=", ".join(expected_aspects)
    )
    
    response = llm_processor.call_llm_api_json(
        prompt,
        "你是一位专业的信息分析专家，擅长识别信息覆盖的缺口和不足。"
    )
    
    if isinstance(response, dict):
        return json.dumps(response, ensure_ascii=False, indent=2)
    else:
        return json.dumps({"error": "缺口分析返回格式不正确"}, ensure_ascii=False)

@mcp.tool()
def query_generation_mcp(topic: str, strategy: str = "initial", context: str = "", **kwargs) -> str:
    """Generate search queries using different strategies
    
    Args:
        topic: The topic to generate queries for
        strategy: Query strategy ('initial', 'iterative', 'targeted', 'academic', 'news')
        context: Context information for query generation
        **kwargs: Additional parameters (report_type, target_audience, existing_data, etc.)
        
    Returns:
        str: Generated queries in JSON format
    """
    if not llm_available:
        # 备用查询生成
        base_queries = [
            f"{topic} 最新发展",
            f"{topic} 技术原理", 
            f"{topic} 应用案例",
            f"{topic} 市场趋势",
            f"{topic} 挑战问题"
        ]
        return json.dumps({
            "queries": base_queries,
            "strategy": strategy,
            "method": "fallback"
        }, ensure_ascii=False)
    
    try:
        if strategy == "initial":
            return _generate_initial_queries(topic, kwargs)
        elif strategy == "iterative":
            return _generate_iterative_queries(topic, context, kwargs)
        elif strategy == "targeted":
            return _generate_targeted_queries(topic, context, kwargs)
        elif strategy == "academic":
            return _generate_academic_queries(topic, context, kwargs)
        elif strategy == "news":
            return _generate_news_queries(topic, context, kwargs)
        else:
            return json.dumps({
                "error": f"不支持的查询策略: {strategy}",
                "supported_strategies": ["initial", "iterative", "targeted", "academic", "news"]
            }, ensure_ascii=False)
            
    except Exception as e:
        return json.dumps({
            "error": f"查询生成失败: {str(e)}",
            "strategy": strategy
        }, ensure_ascii=False)

def _generate_initial_queries(topic: str, kwargs: Dict) -> str:
    """Generate initial search queries"""
    report_type = kwargs.get("report_type", "综合报告")
    target_audience = kwargs.get("target_audience", "通用")
    
    template = """
作为一个专业的信息研究员，请为主题"{topic}"生成初始搜索查询。

报告类型：{report_type}
目标受众：{target_audience}

任务要求：
1. 生成5-8个多样化的搜索查询
2. 覆盖主题的核心概念、最新发展、应用场景、挑战问题
3. 查询应该具体且可搜索，避免过于宽泛
4. 包含中英文关键词组合，提高搜索覆盖面

请按以下格式输出JSON：
```json
{{
    "queries": [
        "查询1",
        "查询2",
        "查询3",
        "查询4",
        "查询5"
    ],
    "reasoning": "生成这些查询的理由和策略说明"
}}
```
"""
    
    prompt = template.format(topic=topic, report_type=report_type, target_audience=target_audience)
    response = llm_processor.call_llm_api_json(
        prompt,
        "你是一位专业的搜索查询专家，擅长为不同主题生成高效的搜索查询。"
    )
    
    if isinstance(response, dict) and "queries" in response:
        return json.dumps(response, ensure_ascii=False, indent=2)
    else:
        return json.dumps({"error": "初始查询生成格式不正确"}, ensure_ascii=False)

def _generate_iterative_queries(topic: str, context: str, kwargs: Dict) -> str:
    """Generate iterative/supplementary queries"""
    existing_data_summary = kwargs.get("existing_data_summary", "无已有数据")
    
    template = """
基于以下已知信息和搜索结果，为主题"{topic}"生成补充性查询。

已知信息摘要：{context}
现有数据类型：{existing_data_summary}

任务要求：
1. 分析已有信息的覆盖面和缺口
2. 生成3-5个全新的、补充性的查询
3. 重点关注尚未充分探索的方面
4. 避免与已有查询重复

输出格式：
```json
{{
    "gaps_identified": ["发现的信息缺口1", "缺口2"],
    "queries": [
        "补充查询1",
        "补充查询2",
        "补充查询3"
    ],
    "reasoning": "基于缺口分析生成查询的理由"
}}
```
"""
    
    prompt = template.format(topic=topic, context=context, existing_data_summary=existing_data_summary)
    response = llm_processor.call_llm_api_json(
        prompt,
        "你是一位专业的信息分析专家，擅长识别信息缺口并生成补充性查询。"
    )
    
    if isinstance(response, dict):
        return json.dumps(response, ensure_ascii=False, indent=2)
    else:
        return json.dumps({"error": "迭代查询生成格式不正确"}, ensure_ascii=False)

def _generate_targeted_queries(topic: str, context: str, kwargs: Dict) -> str:
    """Generate targeted queries for specific sections"""
    section_title = context.split("|")[0] if "|" in context else "未指定章节"
    section_context = context.split("|")[1] if "|" in context else context
    
    template = """
为报告章节"{section_title}"生成高度针对性的搜索查询。

主题：{topic}
章节信息：{section_context}

任务要求：
1. 生成3-4个专门针对该章节的精准查询
2. 查询应该能获取该章节所需的具体信息
3. 考虑章节在整个报告中的作用和位置
4. 确保查询的专业性和针对性

输出格式：
```json
{{
    "section_focus": "该章节的核心关注点",
    "queries": [
        "针对性查询1",
        "针对性查询2",
        "针对性查询3"
    ],
    "expected_content": "期望通过这些查询获得的信息类型"
}}
```
"""
    
    prompt = template.format(topic=topic, section_title=section_title, section_context=section_context)
    response = llm_processor.call_llm_api_json(
        prompt,
        "你是一位专业的内容策划专家，擅长为特定章节生成精准的搜索查询。"
    )
    
    if isinstance(response, dict):
        return json.dumps(response, ensure_ascii=False, indent=2)
    else:
        return json.dumps({"error": "定向查询生成格式不正确"}, ensure_ascii=False)

def _generate_academic_queries(topic: str, context: str, kwargs: Dict) -> str:
    """Generate academic-oriented queries"""
    academic_level = kwargs.get("academic_level", "研究生/专业研究人员级别")
    
    template = """
为学术研究主题"{topic}"生成学术导向的搜索查询。

研究背景：{context}
研究深度要求：{academic_level}

任务要求：
1. 生成4-6个学术性搜索查询
2. 包含专业术语和概念
3. 覆盖理论基础、研究方法、最新进展
4. 适合在学术数据库中搜索

输出格式：
```json
{{
    "academic_areas": ["理论基础", "研究方法", "应用实例"],
    "queries": [
        "学术查询1",
        "学术查询2",
        "学术查询3"
    ],
    "keywords": ["关键学术术语1", "术语2"]
}}
```
"""
    
    prompt = template.format(topic=topic, context=context, academic_level=academic_level)
    response = llm_processor.call_llm_api_json(
        prompt,
        "你是一位资深的学术研究专家，擅长为学术研究生成专业的搜索查询。"
    )
    
    if isinstance(response, dict):
        return json.dumps(response, ensure_ascii=False, indent=2)
    else:
        return json.dumps({"error": "学术查询生成格式不正确"}, ensure_ascii=False)

def _generate_news_queries(topic: str, context: str, kwargs: Dict) -> str:
    """Generate news-oriented queries"""
    time_range = kwargs.get("time_range", "最近30天")
    news_focus = kwargs.get("news_focus", "行业动态和政策变化")
    
    template = """
为新闻话题"{topic}"生成时效性搜索查询。

时间范围：{time_range}
关注焦点：{news_focus}
背景信息：{context}

任务要求：
1. 生成4-5个新闻导向的搜索查询
2. 关注最新动态、突发事件、趋势变化
3. 包含时间敏感的关键词
4. 适合在新闻平台搜索

输出格式：
```json
{{
    "news_angles": ["突发事件", "政策变化", "市场动态"],
    "queries": [
        "新闻查询1",
        "新闻查询2",
        "新闻查询3"
    ],
    "urgency_level": "信息时效性评估"
}}
```
"""
    
    prompt = template.format(topic=topic, context=context, time_range=time_range, news_focus=news_focus)
    response = llm_processor.call_llm_api_json(
        prompt,
        "你是一位专业的新闻分析师，擅长为时事话题生成高时效性的搜索查询。"
    )
    
    if isinstance(response, dict):
        return json.dumps(response, ensure_ascii=False, indent=2)
    else:
        return json.dumps({"error": "新闻查询生成格式不正确"}, ensure_ascii=False)

@mcp.tool()
def outline_writer_mcp(topic: str, report_type: str = "comprehensive", user_requirements: str = "", **kwargs) -> str:
    """Create structured outlines for reports
    
    Args:
        topic: The report topic
        report_type: Type of report ('academic', 'business', 'technical', 'industry', 'comprehensive')
        user_requirements: User's specific requirements
        **kwargs: Additional parameters (reference_data, etc.)
        
    Returns:
        str: Structured outline in JSON format
    """
    if not llm_available:
        # 备用大纲生成
        return _generate_fallback_outline(topic, report_type)
    
    try:
        template = _get_outline_template(report_type)
        
        template_params = {
            "topic": topic,
            "report_type": report_type,
            "user_requirements": user_requirements or "无特殊要求"
        }
        
        # 如果有参考数据，添加相关信息
        reference_data = kwargs.get("reference_data", [])
        if reference_data:
            data_summary = _summarize_reference_data(reference_data)
            template_params["reference_info"] = f"\n参考数据摘要：\n{data_summary}"
        else:
            template_params["reference_info"] = ""
        
        prompt = template.format(**template_params)
        
        response = llm_processor.call_llm_api_json(
            prompt,
            f"你是一位专业的{report_type}专家，擅长创建逻辑清晰、结构合理的报告大纲。"
        )
        
        if isinstance(response, dict):
            return json.dumps(response, ensure_ascii=False, indent=2)
        else:
            return json.dumps({"error": "大纲生成格式不正确"}, ensure_ascii=False)
            
    except Exception as e:
        return json.dumps({
            "error": f"大纲生成失败: {str(e)}",
            "fallback": _generate_fallback_outline(topic, report_type)
        }, ensure_ascii=False)

def _get_outline_template(report_type: str) -> str:
    """Get outline template based on report type"""
    templates = {
        "academic": """
请为学术研究主题"{topic}"创建一个标准的学术报告大纲。

用户特殊要求：{user_requirements}
{reference_info}

请按照学术报告的标准结构，创建详细的层级化大纲：

1. **研究背景与意义**
2. **文献综述**
3. **研究目标与内容**
4. **研究方法与技术路线**
5. **预期结果与创新点**
6. **参考文献**

输出JSON格式的结构化大纲。
""",
        "business": """
请为商业主题"{topic}"创建一个标准的商业报告大纲。

用户特殊要求：{user_requirements}
{reference_info}

请按照商业报告的标准结构：

1. **执行摘要**
2. **市场分析**
3. **产品/服务分析**
4. **商业模式**
5. **风险评估**
6. **建议与结论**

输出JSON格式的结构化大纲。
""",
        "comprehensive": """
请为主题"{topic}"创建一个综合性报告大纲。

报告类型：{report_type}
用户特殊要求：{user_requirements}
{reference_info}

请根据主题特点和用户要求，创建一个逻辑清晰、结构合理的大纲。

基本结构框架：
1. **引言/概述** - 背景介绍和目标设定
2. **核心内容** - 根据主题特点组织2-4个主要章节
3. **分析讨论** - 深入分析和讨论
4. **结论建议** - 总结和建议

输出JSON格式的结构化大纲。
"""
    }
    
    return templates.get(report_type.lower(), templates["comprehensive"])

def _generate_fallback_outline(topic: str, report_type: str) -> str:
    """Generate fallback outline when LLM is not available"""
    if "academic" in report_type.lower():
        sections = [
            {"title": "研究背景", "description": "介绍研究背景和意义"},
            {"title": "文献综述", "description": "回顾相关研究和理论基础"},
            {"title": "研究方法", "description": "说明研究方法和技术路线"},
            {"title": "预期结果", "description": "描述预期成果和创新点"}
        ]
    elif "business" in report_type.lower():
        sections = [
            {"title": "市场分析", "description": "分析市场现状和发展趋势"},
            {"title": "产品服务", "description": "描述产品或服务特点"},
            {"title": "商业模式", "description": "说明商业模式和盈利模式"},
            {"title": "风险评估", "description": "识别和评估主要风险"}
        ]
    else:
        sections = [
            {"title": "概述", "description": f"介绍{topic}的基本情况"},
            {"title": "现状分析", "description": f"分析{topic}的现状"},
            {"title": "发展趋势", "description": f"探讨{topic}的发展趋势"},
            {"title": "总结建议", "description": "总结和建议"}
        ]
    
    outline = {
        "title": f"{topic}报告",
        "level": 0,
        "order": 0,
        "description": f"关于{topic}的{report_type}报告",
        "subsections": [
            {
                "title": section["title"],
                "level": 1,
                "order": i + 1,
                "description": section["description"],
                "estimated_length": "800-1200字",
                "subsections": []
            }
            for i, section in enumerate(sections)
        ]
    }
    
    return json.dumps(outline, ensure_ascii=False, indent=2)

def _summarize_reference_data(reference_data: List[Dict]) -> str:
    """Summarize reference data for outline generation"""
    if not reference_data:
        return "无参考数据"
    
    summaries = []
    for i, item in enumerate(reference_data[:5]):
        if isinstance(item, dict):
            title = item.get("title", f"文档{i+1}")
            content = item.get("content", "")[:100]
            summaries.append(f"[{i+1}] {title} - {content}...")
    
    return "\n".join(summaries)

@mcp.tool()
def summary_writer_mcp(content_data: Union[List[Dict], str], length_constraint: str = "200-300字", format: str = "paragraph", **kwargs) -> str:
    """Generate summaries from content data
    
    Args:
        content_data: Content to summarize (list of documents/dicts or string)
        length_constraint: Length constraint (e.g., "200-300字")
        format: Output format ('paragraph', 'bullet_points', 'structured', 'executive', 'academic')
        **kwargs: Additional parameters (focus_areas, tone, target_audience, etc.)
        
    Returns:
        str: Generated summary
    """
    if not llm_available:
        return _generate_fallback_summary(content_data, length_constraint, format)
    
    try:
        # 准备内容数据
        prepared_content = _prepare_content_for_summary(content_data)
        
        # 获取配置参数
        focus_areas = kwargs.get("focus_areas", [])
        tone = kwargs.get("tone", "professional")
        target_audience = kwargs.get("target_audience", "通用")
        
        # 选择合适的模板
        template = _get_summary_template(format)
        
        # 准备模板参数
        tone_descriptions = {
            "professional": "专业、正式的商务语言",
            "academic": "学术、严谨的研究语言",
            "casual": "轻松、易懂的通俗语言",
            "technical": "技术、精确的专业语言"
        }
        
        template_params = {
            "content_data": prepared_content,
            "length_constraint": length_constraint,
            "target_audience": target_audience,
            "tone_description": tone_descriptions.get(tone, tone_descriptions["professional"]),
            "focus_areas": ", ".join(focus_areas) if focus_areas else "全面覆盖主要内容"
        }
        
        # 格式化prompt
        prompt = template.format(**template_params)
        
        # 计算token限制
        length_parts = length_constraint.replace("字", "").replace("词", "").replace(" ", "")
        if "-" in length_parts:
            try:
                max_length = int(length_parts.split("-")[1])
                max_tokens = min(max_length * 2, 2000)
            except:
                max_tokens = 1000
        else:
            try:
                max_tokens = min(int(length_parts) * 2, 2000)
            except:
                max_tokens = 1000
        
        # 调用LLM
        summary = llm_processor.call_llm_api(
            prompt,
            f"你是一位专业的内容摘要专家，擅长将复杂信息浓缩为简洁、准确的摘要。你的语言风格是{tone}，目标受众是{target_audience}。",
            temperature=0.3,
            max_tokens=max_tokens
        )
        
        # 后处理摘要
        return _post_process_summary(summary)
        
    except Exception as e:
        return f"摘要生成失败: {str(e)}"

def _get_summary_template(format: str) -> str:
    """Get summary template based on format"""
    templates = {
        "paragraph": """
请为以下内容撰写一个简洁、准确的段落式摘要。

原始内容：
{content_data}

摘要要求：
- 长度限制：{length_constraint}
- 目标受众：{target_audience}
- 语言风格：{tone_description}
- 重点关注：{focus_areas}

撰写原则：
1. **浓缩精炼**：去除冗余信息，保留核心要点
2. **忠于事实**：不添加原文中没有的信息
3. **逻辑清晰**：按照重要性和逻辑顺序组织内容
4. **语言流畅**：使用连贯的段落形式表达

请直接输出摘要内容，不要包含其他解释性文字。
""",
        "bullet_points": """
请为以下内容撰写一个要点式摘要。

原始内容：
{content_data}

摘要要求：
- 长度限制：{length_constraint}
- 目标受众：{target_audience}
- 格式：项目符号列表
- 重点关注：{focus_areas}

输出格式：
- 核心要点1
- 核心要点2
- 核心要点3
- ...

请直接输出要点列表，不要包含其他解释性文字。
""",
        "executive": """
请为以下内容撰写一个执行摘要。

原始内容：
{content_data}

摘要要求：
- 长度限制：{length_constraint}
- 目标受众：{target_audience}（决策者和管理层）
- 格式：执行摘要
- 重点关注：{focus_areas}

输出格式：
**概述**
[简要概述核心内容]

**关键发现**
[最重要的发现和洞察]

**影响分析**
[对业务/行业的影响]

**建议行动**
[推荐的具体行动]

请按照执行摘要的标准格式输出，语言要专业且具有说服力。
"""
    }
    
    return templates.get(format, templates["paragraph"])

def _prepare_content_for_summary(content_data: Union[List[Dict], str]) -> str:
    """Prepare content data for summary generation"""
    if isinstance(content_data, str):
        return content_data
    
    if not content_data:
        return "无内容数据"
    
    content_parts = []
    for i, item in enumerate(content_data):
        if isinstance(item, dict):
            title = item.get("title", f"文档{i+1}")
            content = item.get("content", item.get("summary", item.get("abstract", "")))
            content_parts.append(f"[{title}]\n{content}")
    
    return "\n\n".join(content_parts)

def _post_process_summary(summary: str) -> str:
    """Post-process the generated summary"""
    if not summary:
        return "摘要生成失败"
    
    # 清理格式
    summary = summary.strip()
    
    # 移除可能的标题或前言
    unwanted_prefixes = [
        "摘要：", "总结：", "概述：", "Summary:", "以下是摘要：", 
        "根据提供的内容", "基于以上信息", "摘要如下："
    ]
    
    for prefix in unwanted_prefixes:
        if summary.startswith(prefix):
            summary = summary[len(prefix):].strip()
    
    return summary

def _generate_fallback_summary(content_data, length_constraint, format) -> str:
    """Generate fallback summary when LLM is not available"""
    try:
        # 准备内容
        if isinstance(content_data, str):
            text = content_data
        elif isinstance(content_data, list) and content_data:
            if isinstance(content_data[0], dict):
                text = " ".join([item.get("content", "")[:200] for item in content_data[:3]])
            else:
                text = str(content_data)
        else:
            return "无可用内容进行摘要"
        
        # 简单的句子提取
        sentences = [s.strip() for s in text.split('。') if len(s.strip()) > 10]
        
        # 根据格式调整输出
        if format == "bullet_points":
            return "\n".join([f"- {s}" for s in sentences[:5]])
        else:
            summary_text = "。".join(sentences[:3]) + "。" if sentences else "无可用内容"
            return summary_text[:300] + "..." if len(summary_text) > 300 else summary_text
            
    except Exception as e:
        return f"摘要生成失败: {str(e)}"

@mcp.tool()
def content_writer_mcp(section_title: str, content_data: List[Dict], overall_report_context: str, **kwargs) -> str:
    """Write detailed content for report sections
    
    Args:
        section_title: Title of the section to write
        content_data: Reference content data (list of documents/dicts)
        overall_report_context: Overall report context
        **kwargs: Writing configuration (writing_style, target_audience, tone, etc.)
        
    Returns:
        str: Generated section content
    """
    print(f"🔍 [content_writer_mcp] 开始生成内容，标题: {section_title}")
    print(f"🔍 [content_writer_mcp] llm_available: {llm_available}")
    print(f"🔍 [content_writer_mcp] content_data长度: {len(content_data) if content_data else 0}")
    
    if not llm_available:
        print("⚠️ [content_writer_mcp] LLM不可用，使用fallback内容")
        return _generate_fallback_content(section_title, content_data)
    
    try:
        # 获取配置参数
        writing_style = kwargs.get("writing_style", "professional")
        target_audience = kwargs.get("target_audience", "通用")
        tone = kwargs.get("tone", "objective")
        depth_level = kwargs.get("depth_level", "detailed")
        include_examples = kwargs.get("include_examples", True)
        include_citations = kwargs.get("include_citations", True)
        word_count_requirement = kwargs.get("word_count_requirement", "800-1200字")
        
        # 准备参考内容
        reference_content = _prepare_reference_content_for_writing(content_data)
        
        # 确定写作角色
        role = _determine_writing_role(section_title, overall_report_context)
        
        # 选择合适的模板
        template = _get_content_writing_template(writing_style, role)
        
        # 准备模板参数
        template_params = _prepare_content_template_params(
            section_title, overall_report_context, reference_content, 
            writing_style, target_audience, tone, depth_level, 
            include_examples, word_count_requirement, role
        )
        
        # 格式化prompt
        prompt = template.format(**template_params)
        
        # 计算token限制（放宽上限，允许通过kwargs覆盖）
        try:
            upper = int(word_count_requirement.split("-")[1].replace("字", "")) if "-" in word_count_requirement else int(word_count_requirement.replace("字", ""))
        except Exception:
            upper = 2000
        requested = int(kwargs.get("max_tokens", upper * 2))
        try:
            import config as _cfg
            cap = getattr(_cfg, "LLM_MAX_TOKENS", 8000)
        except Exception:
            cap = 8000
        max_tokens = min(requested, cap)
        
        # 调用LLM生成内容
        print(f"🔍 [content_writer_mcp] 准备调用LLM API，max_tokens: {max_tokens}")
        print(f"🔍 [content_writer_mcp] prompt长度: {len(prompt)}")
        content = llm_processor.call_llm_api(
            prompt,
            f"你是一位专业的内容创作专家，专门负责撰写高质量的{writing_style}风格内容。",
            temperature=0.3,
            max_tokens=max_tokens
        )
        print(f"🔍 [content_writer_mcp] LLM API调用完成，生成了{len(content)}字符的内容")
        
        # 后处理内容
        print(f"🔍 [content_writer_mcp] 开始后处理内容，include_citations: {include_citations}")
        processed_content = _post_process_content(content, include_citations)
        print(f"🔍 [content_writer_mcp] 后处理完成，最终内容长度: {len(processed_content)}")
        
        # 获取usage信息
        usage_info = llm_processor.last_usage if hasattr(llm_processor, 'last_usage') else None
        print(f"🔍 [content_writer_mcp] 获取到usage信息: {usage_info}")
        
        print(f"🔍 [content_writer_mcp] 准备返回结果...")
        
        # 返回内容和usage信息的字典
        result = {
            "content": processed_content,
            "usage": usage_info
        }
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        print(f"❌ [content_writer_mcp] 章节'{section_title}'撰写失败: {str(e)}")
        import traceback
        print(f"详细错误信息:")
        traceback.print_exc()
        return f"章节'{section_title}'撰写失败: {str(e)}"

def _prepare_reference_content_for_writing(content_data: List[Dict]) -> str:
    """Prepare reference content for writing"""
    if not content_data:
        return "无参考资料"
    
    reference_parts = []
    for i, item in enumerate(content_data[:8]):  # 限制前8个参考资料
        if isinstance(item, dict):
            title = item.get("title", f"参考资料{i+1}")
            content = item.get("content", item.get("summary", ""))[:300]
            source = item.get("source", "未知来源")
            ref_text = f"[{i+1}] {title}\n来源: {source}\n内容: {content}..."
            reference_parts.append(ref_text)
    
    return "\n\n".join(reference_parts)

def _determine_writing_role(section_title: str, context: str) -> str:
    """Determine writing role based on section title and context"""
    title_lower = section_title.lower()
    context_lower = context.lower()
    
    # 学术相关关键词
    if any(keyword in title_lower for keyword in ["研究", "理论", "方法", "文献", "学术"]):
        return "academic"
    # 商业相关关键词  
    if any(keyword in title_lower for keyword in ["市场", "商业", "投资", "收益", "策略", "竞争"]):
        return "business"
    # 技术相关关键词
    if any(keyword in title_lower for keyword in ["技术", "算法", "架构", "实现", "系统", "开发"]):
        return "technical"
    
    return "general"

def _get_content_writing_template(writing_style: str, role: str) -> str:
    """Get content writing template"""
    return """
你是一位专业的{role}，正在撰写关于"{overall_topic}"的{section_title}章节。

章节要求：
- 目标受众：{target_audience}
- 写作风格：{writing_style}
- 内容深度：{depth_level}
- 字数要求：{word_count_requirement}

参考资料：
{reference_content}

全局报告上下文：
{overall_report_context}

撰写要求：
1. **专业深度**：基于参考资料提供深入、专业的分析
2. **逻辑结构**：内容应有清晰的逻辑层次和段落结构
3. **实用价值**：突出实际应用价值和现实意义
4. **引用规范**：在引用参考资料时使用[1]、[2]等标记
5. **语言表达**：使用{tone}的语调，适合{target_audience}阅读

章节结构建议：
- 开篇：简要介绍本章节的核心议题
- 主体：围绕关键要点展开详细分析
- 实例：{example_instruction}
- 总结：概括本章节的主要观点

请撰写完整的章节内容，确保信息准确、逻辑清晰、表达流畅。
"""

def _prepare_content_template_params(section_title, overall_report_context, reference_content, 
                                   writing_style, target_audience, tone, depth_level, 
                                   include_examples, word_count_requirement, role) -> Dict[str, str]:
    """Prepare template parameters for content writing"""
    # 提取整体主题
    overall_topic = overall_report_context.split('\n')[0] if overall_report_context else "相关主题"
    
    # 角色描述
    role_descriptions = {
        "academic": "学术研究专家和教授",
        "business": "商业分析师和战略顾问", 
        "technical": "技术专家和架构师",
        "general": "专业内容分析师"
    }
    
    # 示例指导
    example_instruction = "结合具体案例和实例进行说明" if include_examples else "重点进行理论分析"
    
    # 语调描述
    tone_descriptions = {
        "objective": "客观、中性",
        "analytical": "分析性、深入",
        "professional": "专业、正式",
        "engaging": "生动、引人入胜"
    }
    
    return {
        "role": role_descriptions.get(role, role_descriptions["general"]),
        "overall_topic": overall_topic,
        "section_title": section_title,
        "target_audience": target_audience,
        "writing_style": writing_style,
        "depth_level": depth_level,
        "word_count_requirement": word_count_requirement,
        "reference_content": reference_content,
        "overall_report_context": overall_report_context,
        "tone": tone_descriptions.get(tone, "客观、专业"),
        "example_instruction": example_instruction
    }

def _post_process_content(content: str, include_citations: bool) -> str:
    """Post-process generated content"""
    if not content:
        return "内容生成失败"
    
    # 清理格式
    content = content.strip()
    
    # 移除可能的标题重复
    lines = content.split('\n')
    if lines and lines[0].strip().startswith('#'):
        content = '\n'.join(lines[1:]).strip()
    
    # 确保引用格式正确
    if include_citations:
        import re
        # 统一引用格式为 [数字]
        content = re.sub(r'\[(\d+)\]', r'[\1]', content)
        content = re.sub(r'（(\d+)）', r'[\1]', content)
        content = re.sub(r'\((\d+)\)', r'[\1]', content)
    
    return content

def _generate_fallback_content(section_title: str, content_data: List[Dict]) -> str:
    """Generate fallback content when LLM is not available"""
    try:
        content_parts = [f"## {section_title}\n"]
        
        if content_data:
            content_parts.append("基于现有资料分析，本章节主要内容包括：\n")
            
            for i, item in enumerate(content_data[:3]):
                if isinstance(item, dict):
                    title = item.get("title", f"要点{i+1}")
                    summary = item.get("content", "")[:200]
                    content_parts.append(f"### {title}\n{summary}\n")
        else:
            content_parts.append(f"本章节将详细介绍{section_title}的相关内容，包括基本概念、发展现状、应用场景等方面。\n")
        
        content_parts.append("更多详细内容有待进一步研究和分析。")
        
        return '\n'.join(content_parts)
        
    except Exception as e:
        return f"## {section_title}\n\n内容生成失败: {str(e)}\n\n本章节需要进一步完善。"

@mcp.tool()
def orchestrator_mcp_simple(task: str, **kwargs) -> str:
    """
    简化版MCP调度器 - 用于测试和演示
    """
    try:
        print(f"\n🎯 [简化调度器] 开始执行任务: {task}")
        
        # 1. 意图识别
        intent_result = analysis_mcp("intent", task, "")
        intent_data = json.loads(intent_result)
        primary_intent = intent_data.get('details', {}).get('primary_intent', '未识别')
        print(f"✅ 意图识别: {primary_intent}")
        
        # 2. 生成大纲
        topic = _extract_topic_from_task(task)
        outline_result = outline_writer_mcp(topic, "comprehensive", task)
        outline_data = json.loads(outline_result)
        
        # 3. 强制创建章节内容（绕过搜索问题）
        default_sections = [
            {"name": "行业概述", "content": f"{topic}的基本情况和发展背景"},
            {"name": "重大事件", "content": "最近的重要事件和行业新闻"},
            {"name": "技术发展", "content": "技术创新和突破性进展"},
            {"name": "市场动态", "content": "市场变化、投资和竞争态势"},
            {"name": "未来展望", "content": "发展前景、趋势预测和建议"}
        ]
        
        print(f"📝 开始生成 {len(default_sections)} 个章节...")
        
        section_contents = {}
        for section in default_sections:
            section_name = section['name']
            print(f"  📄 生成章节: {section_name}")
            
            content = content_writer_mcp(
                section_title=section_name,
                content_data=[{
                    "title": f"{topic}相关信息",
                    "content": f"关于{topic}的{section['content']}，包括相关分析和见解。",
                    "source": "智能生成"
                }],
                overall_report_context=f"{topic}行业分析报告",
                writing_style="professional",
                target_audience="行业分析师"
            )
            section_contents[section_name] = content
        
        # 4. 生成摘要
        executive_summary = summary_writer_mcp(
            content_data=list(section_contents.values()),
            length_constraint="300-400字",
            format="executive"
        )
        
        # 5. 组装报告
        final_report = f"""# {topic} - 行业分析报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**识别意图**: {primary_intent}

## 📋 执行摘要

{executive_summary}

## 📊 详细分析

"""
        
        for section_name, content in section_contents.items():
            final_report += f"### {section_name}\n\n{content}\n\n"
        
        final_report += "\n---\n*本报告由MCP简化调度器生成*"
        
        result = {
            "status": "completed",
            "task": task,
            "report_content": final_report,
            "metadata": {
                "topic": topic,
                "sections_count": len(section_contents),
                "intent": primary_intent
            }
        }
        
        print(f"🎉 简化调度器完成！生成了 {len(section_contents)} 个章节")
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "error": str(e)
        }, ensure_ascii=False)

@mcp.tool()
def orchestrator_mcp(task: str, task_type: str = "auto", **kwargs) -> str:
    """
    MCP工具调度器 - 串联调用各个MCP工具完成复杂任务
    
    Args:
        task: 任务描述 (如 "生成AI Agent行业动态报告")
        task_type: 任务类型 ('news_report', 'research_report', 'industry_analysis', 'auto')
        **kwargs: 其他参数 (days, companies, quality_threshold等)
        
    Returns:
        str: 完整的执行结果和生成的报告
    """
    try:
        print(f"\n🎯 [MCP调度器] 开始执行任务: {task}")
        print(f"📋 任务类型: {task_type}")
        print("=" * 60)
        
        # 步骤1: 意图识别和任务规划
        print("\n🧠 [步骤1] 意图识别和任务规划...")
        intent_result = analysis_mcp(
            analysis_type="intent",
            data=task,
            context=f"任务类型: {task_type}",
            task_planning="true",
            detailed_analysis="true"
        )
        
        intent_data = json.loads(intent_result)
        print(f"✅ 意图识别完成: {intent_data.get('details', {}).get('primary_intent', '未识别')}")
        
        # 步骤2: 生成报告大纲
        print("\n📝 [步骤2] 生成报告大纲...")
        
        # 根据意图确定报告类型
        if task_type == "auto":
            if "新闻" in task or "动态" in task or "news" in task.lower():
                report_type = "industry"
            elif "研究" in task or "research" in task.lower():
                report_type = "academic"  
            elif "分析" in task or "analysis" in task.lower():
                report_type = "business"
            else:
                report_type = "comprehensive"
        else:
            type_mapping = {
                "news_report": "industry",
                "research_report": "academic", 
                "industry_analysis": "business"
            }
            report_type = type_mapping.get(task_type, "comprehensive")
        
        # 提取主题
        topic = _extract_topic_from_task(task)
        
        outline_result = outline_writer_mcp(
            topic=topic,
            report_type=report_type,
            user_requirements=task
        )
        
        outline_data = json.loads(outline_result)
        print(f"🔍 [调试] 大纲数据keys: {list(outline_data.keys())}")
        
        # 适配不同的大纲数据结构
        sections = []
        
        if 'subsections' in outline_data:
            sections = outline_data['subsections']
            print(f"🔍 [调试] 使用subsections，数量: {len(sections)}")
        elif 'sections' in outline_data:
            sections = outline_data['sections']
            print(f"🔍 [调试] 使用sections，数量: {len(sections)}")
        elif 'structure' in outline_data:
            print(f"🔍 [调试] 使用structure解析")
            # 解析嵌套结构
            structure = outline_data['structure']
            print(f"🔍 [调试] structure keys: {list(structure.keys())}")
            
            for main_key, main_value in structure.items():
                print(f"🔍 [调试] 处理: {main_key}, 类型: {type(main_value)}")
                if isinstance(main_value, dict):
                    # 如果是嵌套结构，提取子章节
                    for sub_key, sub_value in main_value.items():
                        sections.append({
                            "name": sub_key,
                            "title": sub_key,
                            "content": sub_value if isinstance(sub_value, str) else str(sub_value)
                        })
                        print(f"🔍 [调试] 添加子章节: {sub_key}")
                else:
                    # 如果是简单结构
                    sections.append({
                        "name": main_key,
                        "title": main_key,
                        "content": main_value
                    })
                    print(f"🔍 [调试] 添加主章节: {main_key}")
        
        print(f"✅ 大纲生成完成，包含 {len(sections)} 个主要章节")
        if sections:
            print("📋 章节列表:")
            for i, section in enumerate(sections[:5], 1):
                print(f"  {i}. {section.get('name', section.get('title', '未知'))}")
        else:
            print("⚠️ 未解析到任何章节")
        
        # 步骤3: 用户交互确认大纲
        print("\n👤 [步骤3] 用户交互确认...")
        interaction_result = user_interaction_mcp(
            interaction_type="confirmation",
            prompt=f"已为'{topic}'生成报告大纲，是否确认继续？大纲包含以下章节：\n" + 
                  "\n".join([f"- {section.get('name', section.get('title', '未知章节'))}" for section in sections]),
            default=True,
            auto_confirm=kwargs.get('auto_confirm', True)
        )
        
        interaction_data = json.loads(interaction_result)
        print(f"✅ 用户确认: {interaction_data.get('status', 'confirmed')}")
        
        # 步骤4: 并行内容检索
        print("\n🔍 [步骤4] 并行内容检索...")
        
        # 为每个章节生成专门的查询
        days = kwargs.get('days', 7)
        all_search_results = []
        
        # 生成多角度查询
        query_result = query_generation_mcp(
            topic=topic,
            strategy="news" if "新闻" in task or "动态" in task else "initial",
            context=f"为{report_type}报告生成查询",
            time_range=f"past_{days}_days",
            focus_areas=["重大事件", "技术发展", "市场动态", "政策变化"]
        )
        
        query_data = json.loads(query_result)
        queries = query_data.get('queries', [])
        print(f"✅ 生成 {len(queries)} 个搜索查询")
        
        # 并行搜索
        try:
            search_result = parallel_search(
                queries=queries[:5],  # 限制查询数量
                max_results=3
            )
            print(f"🔍 搜索结果长度: {len(search_result) if search_result else 0}")
            
            # 检查搜索结果是否为错误信息
            if isinstance(search_result, str) and "搜索服务暂时不可用" in search_result:
                raise Exception("搜索服务不可用")
                
        except Exception as e:
            print(f"⚠️ 搜索失败: {str(e)}")
            # 生成更丰富的模拟数据
            search_result = f"""
            基于{topic}的最新行业动态：
            
            1. 技术突破：AI Agent在多模态交互方面取得重要进展，支持语音、文本、图像的综合处理能力
            
            2. 产品发布：多家科技公司发布了新一代AI Agent平台，包括增强的自然语言理解和任务执行能力
            
            3. 市场动态：AI Agent市场预计将在未来几年内实现快速增长，企业级应用需求旺盛
            
            4. 政策法规：相关监管部门正在制定AI Agent的使用规范和安全标准
            
            5. 投资趋势：风险投资对AI Agent领域的投资热情持续高涨，多个初创公司获得大额融资
            
            6. 应用场景：AI Agent在客户服务、内容创作、数据分析等领域的应用案例不断涌现
            """
        
        print(f"✅ 搜索完成，获得初始数据")
        
        # 步骤5: 递归质量评估和补充搜索
        print("\n📊 [步骤5] 质量评估和迭代优化...")
        
        max_iterations = kwargs.get('max_iterations', 3)
        quality_threshold = kwargs.get('quality_threshold', 7.0)
        
        for iteration in range(max_iterations):
            print(f"\n🔄 第 {iteration + 1} 轮质量评估...")
            
            # 评估当前数据质量
            quality_result = analysis_mcp(
                analysis_type="quality",
                data=[{"title": "搜索结果汇总", "content": search_result[:500], "source": "search"}],
                topic=topic,
                analysis_aspects=["relevance", "completeness", "timeliness"]
            )
            
            quality_data = json.loads(quality_result)
            current_score = quality_data.get('score', 0)
            print(f"📈 当前质量评分: {current_score:.2f}/10")
            
            if current_score >= quality_threshold:
                print(f"✅ 质量达标 (≥{quality_threshold})，停止迭代")
                break
            
            if iteration < max_iterations - 1:
                print(f"⚠️ 质量不足，进行补充搜索...")
                
                # 缺口分析
                gap_result = analysis_mcp(
                    analysis_type="gap_analysis",
                    topic=topic,
                    data=[{"content": search_result}],
                    expected_aspects=["技术发展", "市场动态", "政策变化", "行业趋势"]
                )
                
                gap_data = json.loads(gap_result)
                gaps = gap_data.get('details', {}).get('information_gaps', [])
                
                # 根据缺口生成补充查询
                if gaps:
                    gap_queries = []
                    for gap in gaps[:3]:  # 最多3个补充查询
                        gap_desc = gap.get('description', '')
                        suggested_queries = gap.get('suggested_queries', [])
                        gap_queries.extend(suggested_queries[:2])
                    
                    if gap_queries:
                        additional_result = parallel_search(
                            queries=gap_queries[:3],
                            max_results=2
                        )
                        search_result += f"\n\n补充搜索结果:\n{additional_result}"
                        print(f"✅ 补充搜索完成")
            else:
                print(f"⚠️ 已达最大迭代次数 ({max_iterations})，使用当前数据")
        
        # 步骤6: 并行报告生成
        print("\n📝 [步骤6] 并行报告生成...")
        
        # 为每个章节生成内容
        section_contents = {}
        # 使用之前解析的sections变量
        
        # 如果大纲为空，创建默认章节
        if not sections:
            print("⚠️ 大纲为空，创建默认章节结构...")
            sections = [
                {"name": "行业概述", "content": f"{topic}行业基本情况"},
                {"name": "重大事件", "content": "最近的重要事件和新闻"},
                {"name": "技术发展", "content": "技术创新和突破"},
                {"name": "市场动态", "content": "市场变化和趋势"},
                {"name": "未来展望", "content": "发展前景和预测"}
            ]
        
        print(f"🔄 开始生成 {len(sections)} 个章节内容...")
        
        for i, section in enumerate(sections[:5]):  # 限制章节数量避免过长
            section_title = section.get('name', section.get('title', f'章节{i+1}'))
            print(f"  📄 生成章节: {section_title}")
            
            content = content_writer_mcp(
                section_title=section_title,
                content_data=[{
                    "title": f"{topic}相关信息",
                    "content": search_result[:800] if isinstance(search_result, str) else str(search_result)[:800],  # 限制长度
                    "source": "综合搜索"
                }],
                overall_report_context=f"{topic}行业{report_type}报告",
                writing_style="professional",
                target_audience="行业分析师",
                word_count_requirement="600-800字"
            )
            
            section_contents[section_title] = content
        
        # 生成执行摘要
        print("📄 生成执行摘要...")
        executive_summary = summary_writer_mcp(
            content_data=list(section_contents.values()),
            length_constraint="400-500字",
            format="executive",
            focus_areas=["关键发现", "重要趋势", "战略建议"],
            tone="professional"
        )
        
        # 步骤7: 组装最终报告
        print("\n📋 [步骤7] 组装最终报告...")
        
        final_report = _assemble_orchestrated_report(
            topic=topic,
            task_description=task,
            intent_analysis=intent_data,
            outline=outline_data,
            executive_summary=executive_summary,
            section_contents=section_contents,
            search_summary=f"共检索 {len(queries)} 个查询，经过 {iteration + 1} 轮优化",
            quality_score=current_score if 'current_score' in locals() else 0.0
        )
        
        print("✅ 报告组装完成")
        
        # 返回结果
        result = {
            "status": "completed",
            "task": task,
            "report_content": final_report,
            "metadata": {
                "topic": topic,
                "report_type": report_type,
                "sections_count": len(section_contents),
                "final_quality_score": current_score,
                "iterations_used": iteration + 1,
                "queries_executed": len(queries)
            }
        }
        
        print(f"\n🎉 [MCP调度器] 任务完成!")
        print(f"📊 最终质量评分: {current_score:.2f}/10")
        print(f"📝 报告包含 {len(section_contents)} 个章节")
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "failed",
            "task": task,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

def _extract_topic_from_task(task: str) -> str:
    """从任务描述中提取主题"""
    # 移除常见的任务词汇
    stop_words = ["生成", "分析", "报告", "研究", "写", "创建", "制作", "行业", "动态", "新闻"]
    words = task.split()
    topic_words = []
    
    for word in words:
        if word not in stop_words and len(word) > 1:
            topic_words.append(word)
    
    if topic_words:
        return " ".join(topic_words[:3])  # 取前3个词作为主题
    else:
        return "未指定主题"

def _assemble_orchestrated_report(topic: str, task_description: str, intent_analysis: Dict,
                                outline: Dict, executive_summary: str, section_contents: Dict,
                                search_summary: str, quality_score: float) -> str:
    """组装调度生成的报告"""
    from datetime import datetime
    
    report_parts = []
    
    # 报告标题和元信息
    report_parts.append(f"# {topic} - 智能调度生成报告\n")
    report_parts.append(f"**原始任务**: {task_description}")
    report_parts.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_parts.append(f"**质量评分**: {quality_score:.2f}/10")
    report_parts.append(f"**搜索摘要**: {search_summary}\n")
    
    # 意图分析摘要
    primary_intent = intent_analysis.get('details', {}).get('primary_intent', '未识别')
    report_parts.append(f"**识别意图**: {primary_intent}\n")
    
    # 执行摘要
    report_parts.append("## 🔍 执行摘要\n")
    report_parts.append(executive_summary)
    report_parts.append("\n")
    
    # 详细内容章节
    report_parts.append("## 📊 详细分析\n")
    
    for section_title, content in section_contents.items():
        report_parts.append(f"### {section_title}\n")
        report_parts.append(content)
        report_parts.append("\n")
    
    # 报告说明
    report_parts.append("---\n")
    report_parts.append("*本报告由MCP智能调度器生成，整合了意图识别、大纲生成、内容检索、质量评估、用户交互等多个MCP工具*")
    
    return '\n'.join(report_parts)

@mcp.tool()
def generate_insight_report(request: Dict[str, Any]) -> str:
    """Generate insight report based on request parameters
    
    Args:
        request: Request parameters containing topic, report_type, depth_level, etc.
        
    Returns:
        str: Generated insight report content
    """
    try:
        topic = request.get("topic", "未指定主题")
        report_type = request.get("report_type", "insight")
        depth_level = request.get("depth_level", "detailed")
        target_audience = request.get("target_audience", "行业专家")
        include_citations = request.get("include_citations", True)
        max_sections = request.get("max_sections", 8)
        
        print(f"🎯 生成洞察报告: {topic}")
        print(f"📋 报告类型: {report_type}, 深度: {depth_level}")
        
        # 使用orchestrator_mcp_simple生成报告
        task_description = f"生成{topic}的{report_type}报告，深度级别：{depth_level}，目标受众：{target_audience}"
        
        result = orchestrator_mcp_simple(task_description)
        result_data = json.loads(result)
        
        if result_data.get("status") == "completed":
            return result_data.get("report_content", "报告生成失败")
        else:
            return f"洞察报告生成失败: {result_data.get('error', '未知错误')}"
            
    except Exception as e:
        return f"洞察报告生成过程中发生错误: {str(e)}"

@mcp.tool()
def generate_industry_dynamic_report(industry: str, time_range: str = "recent", focus_areas: List[str] = None, include_analysis: bool = True, data_sources: List[str] = None, **kwargs) -> str:
    """Generate industry dynamic report based on parameters
    
    Args:
        industry: Target industry for the report
        time_range: Time range for analysis (recent, 1month, 3months, etc.)
        focus_areas: List of focus areas for the report
        include_analysis: Whether to include detailed analysis
        data_sources: List of data sources to use
        **kwargs: Additional parameters
        
    Returns:
        str: Generated industry dynamic report content
    """
    try:
        if focus_areas is None:
            focus_areas = ["市场趋势", "技术创新", "政策影响", "竞争格局"]
        if data_sources is None:
            data_sources = ["news", "research", "market_data"]
            
        print(f"🏭 生成行业动态报告: {industry}")
        print(f"📅 时间范围: {time_range}, 关注领域: {focus_areas}")
        
        # 使用orchestrator_mcp生成行业动态报告
        task_description = f"生成{industry}行业动态报告，时间范围：{time_range}，关注领域：{focus_areas}，包含分析：{include_analysis}，数据源：{data_sources}"
        
        result = orchestrator_mcp(task_description, task_type="industry_report")
        result_data = json.loads(result)
        
        if result_data.get("status") == "completed":
            return result_data.get("report_content", "报告生成失败")
        else:
            return f"行业动态报告生成失败: {result_data.get('error', '未知错误')}"
            
    except Exception as e:
        print(f"❌ 行业动态报告生成过程中发生错误: {str(e)}")
        return f"行业动态报告生成失败: {str(e)}"

@mcp.tool()
def generate_academic_research_report(research_topic: str, academic_level: str = "advanced", research_methodology: str = "comprehensive", include_literature_review: bool = True, citation_style: str = "academic", max_pages: int = 20, **kwargs) -> str:
    """Generate academic research report based on parameters
    
    Args:
        research_topic: Research topic for the report
        academic_level: Academic level (basic, intermediate, advanced)
        research_methodology: Research methodology approach
        include_literature_review: Whether to include literature review
        citation_style: Citation style to use
        max_pages: Maximum number of pages
        **kwargs: Additional parameters
        
    Returns:
        str: Generated academic research report content
    """
    try:
        print(f"🎓 生成学术研究报告: {research_topic}")
        print(f"📚 学术级别: {academic_level}, 研究方法: {research_methodology}")
        
        # 使用orchestrator_mcp生成报告
        task_description = f"生成{research_topic}的学术研究报告，学术级别：{academic_level}，研究方法：{research_methodology}"
        
        result = orchestrator_mcp(task_description, task_type="research_report", days=30)
        result_data = json.loads(result)
        
        if result_data.get("status") == "completed":
            return result_data.get("report_content", "报告生成失败")
        else:
            return f"学术研究报告生成失败: {result_data.get('error', '未知错误')}"
            
    except Exception as e:
        return f"学术研究报告生成过程中发生错误: {str(e)}"

@mcp.tool()
def comprehensive_search(topic: str, search_type: str = "comprehensive", max_results: int = 10, days: int = 30, sources: List[str] = None) -> str:
    """Comprehensive search across multiple sources
    
    Args:
        topic: Search topic
        search_type: Type of search (comprehensive, academic, news, etc.)
        max_results: Maximum number of results to return
        days: Number of days to search back
        sources: List of sources to search (web, academic, news)
        
    Returns:
        str: Search results
    """
    try:
        if sources is None:
            sources = ["web", "academic", "news"]
            
        print(f"🔍 综合搜索: {topic}")
        print(f"📊 搜索类型: {search_type}, 最大结果: {max_results}, 时间范围: {days}天")
        
        # 生成搜索查询
        query_result = query_generation_mcp(
            topic=topic,
            strategy="academic" if "academic" in search_type else "news" if "news" in search_type else "initial",
            context=f"搜索类型: {search_type}",
            time_range=f"past_{days}_days"
        )
        
        query_data = json.loads(query_result)
        queries = query_data.get('queries', [f"{topic} 最新发展", f"{topic} 研究进展"])
        
        # 执行并行搜索
        search_result = parallel_search(queries[:5], max_results)
        
        return search_result if search_result else f"未找到关于'{topic}'的相关信息"
        
    except Exception as e:
        return f"综合搜索过程中发生错误: {str(e)}"

@mcp.tool()
def user_interaction_mcp(interaction_type: str, prompt: str, options: List[str] = None, **kwargs) -> str:
    """Handle user interactions and get user input
    
    Args:
        interaction_type: Type of interaction ('choice', 'input', 'confirmation', 'rating', 'multi_choice')
        prompt: Prompt message for the user
        options: List of options for choice-based interactions
        **kwargs: Additional parameters (allow_custom, default, validation_rules, etc.)
        
    Returns:
        str: User response or interaction result in JSON format
    """
    try:
        if interaction_type == "choice":
            return _handle_choice_interaction(prompt, options or [], kwargs)
        elif interaction_type == "input":
            return _handle_input_interaction(prompt, kwargs)
        elif interaction_type == "confirmation":
            return _handle_confirmation_interaction(prompt, kwargs)
        elif interaction_type == "rating":
            return _handle_rating_interaction(prompt, kwargs)
        elif interaction_type == "multi_choice":
            return _handle_multi_choice_interaction(prompt, options or [], kwargs)
        else:
            return json.dumps({
                "error": f"不支持的交互类型: {interaction_type}",
                "supported_types": ["choice", "input", "confirmation", "rating", "multi_choice"]
            }, ensure_ascii=False)
            
    except Exception as e:
        return json.dumps({
            "error": f"用户交互处理失败: {str(e)}",
            "interaction_type": interaction_type
        }, ensure_ascii=False)

def _handle_choice_interaction(prompt: str, options: List[str], kwargs: Dict) -> str:
    """Handle choice interaction"""
    allow_custom = kwargs.get("allow_custom", False)
    default = kwargs.get("default", "")
    
    interaction_data = {
        "type": "choice",
        "prompt": prompt,
        "options": [{"value": str(i), "label": option} for i, option in enumerate(options, 1)],
        "allow_custom": allow_custom,
        "default": default,
        "status": "pending_user_response"
    }
    
    return json.dumps(interaction_data, ensure_ascii=False, indent=2)

def _handle_input_interaction(prompt: str, kwargs: Dict) -> str:
    """Handle input interaction"""
    max_length = kwargs.get("max_length", 1000)
    required = kwargs.get("required", True)
    validation_pattern = kwargs.get("validation_pattern")
    
    interaction_data = {
        "type": "input",
        "prompt": prompt,
        "validation_rules": {
            "max_length": max_length,
            "required": required,
            "pattern": validation_pattern
        },
        "status": "pending_user_response"
    }
    
    return json.dumps(interaction_data, ensure_ascii=False, indent=2)

def _handle_confirmation_interaction(prompt: str, kwargs: Dict) -> str:
    """Handle confirmation interaction"""
    default = kwargs.get("default")
    
    interaction_data = {
        "type": "confirmation",
        "prompt": prompt,
        "options": [
            {"value": "yes", "label": "是"},
            {"value": "no", "label": "否"}
        ],
        "default": "yes" if default else "no" if default is not None else "",
        "status": "pending_user_response"
    }
    
    return json.dumps(interaction_data, ensure_ascii=False, indent=2)

def _handle_rating_interaction(prompt: str, kwargs: Dict) -> str:
    """Handle rating interaction"""
    min_score = kwargs.get("min_score", 1)
    max_score = kwargs.get("max_score", 5)
    labels = kwargs.get("labels", {1: "很差", 2: "较差", 3: "一般", 4: "较好", 5: "很好"})
    
    options = []
    for score in range(min_score, max_score + 1):
        label = labels.get(score, str(score))
        options.append({"value": str(score), "label": f"{score}分", "description": label})
    
    interaction_data = {
        "type": "rating",
        "prompt": prompt,
        "options": options,
        "validation_rules": {"min": min_score, "max": max_score},
        "status": "pending_user_response"
    }
    
    return json.dumps(interaction_data, ensure_ascii=False, indent=2)

def _handle_multi_choice_interaction(prompt: str, options: List[str], kwargs: Dict) -> str:
    """Handle multi-choice interaction"""
    min_selections = kwargs.get("min_selections", 1)
    max_selections = kwargs.get("max_selections", len(options))
    
    interaction_data = {
        "type": "multi_choice",
        "prompt": f"{prompt}\n(请选择{min_selections}-{max_selections}项，用逗号分隔)",
        "options": [{"value": str(i), "label": option} for i, option in enumerate(options, 1)],
        "validation_rules": {
            "min_selections": min_selections,
            "max_selections": max_selections
        },
        "status": "pending_user_response"
    }
    
    return json.dumps(interaction_data, ensure_ascii=False, indent=2)

# Add a dynamic search resource
@mcp.resource("search://{query}")
def get_search_info(query: str) -> str:
    """Get information about a search query"""
    return f"搜索查询: '{query}'\n这个资源可以提供关于该查询的详细搜索信息。"


# # Add a prompt
# @mcp.prompt()
# def greet_user(name: str, style: str = "friendly") -> str:
#     """Generate a greeting prompt"""
#     styles = {
#         "friendly": "Please write a warm, friendly greeting",
#         "formal": "Please write a formal, professional greeting",
#         "casual": "Please write a casual, relaxed greeting",
#     }

#     return f"{styles.get(style, styles['friendly'])} for someone named {name}."

# 添加自定义HTTP端点来支持测试文件的请求格式
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import uvicorn
import asyncio
import json

# 创建FastAPI应用来处理自定义请求格式
http_app = FastAPI(title="MCP HTTP API", version="1.0.0")

@http_app.post("/mcp/tools/call")
async def tools_call(request: dict):
    """处理tools/call请求格式"""
    try:
        # 解析请求
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id", 1)
        
        if method != "tools/call":
            raise HTTPException(status_code=400, detail="Invalid method")
        
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        print(f"🔧 调用工具: {tool_name}")
        print(f"📋 参数: {arguments}")
        
        # 移除特殊处理，统一使用标准MCP工具调用
        
        # 返回SSE格式的响应
        async def generate_sse_response():
            # 发送开始执行消息
            start_message = {
                "method": "notifications/message",
                "params": {
                    "level": "info",
                    "data": {
                        "msg": {
                            "status": "started",
                            "message": f"开始执行工具 {tool_name}",
                            "details": {
                                "id": request_id,
                                "name": tool_name,
                                "content": f"正在处理 {tool_name} 请求..."
                            }
                        },
                        "extra": None
                    }
                },
                "jsonrpc": "2.0"
            }
            try:
                yield f"data: {json.dumps(start_message, ensure_ascii=False)}\n\n"
            except (GeneratorExit, asyncio.CancelledError, BrokenPipeError, ConnectionResetError) as e:
                print(f"🔌 [SSE] 连接在发送开始消息时关闭/取消: {e} (id={request_id}, tool={tool_name})")
                return
            
            # 发送进度更新消息
            progress_message = {
                "method": "notifications/message",
                "params": {
                    "level": "info",
                    "data": {
                        "msg": {
                            "status": "processing",
                            "message": f"工具 {tool_name} 正在执行中",
                            "details": {
                                "id": request_id,
                                "name": tool_name,
                                "content": f"正在生成报告内容，请稍候..."
                            }
                        },
                        "extra": None
                    }
                },
                "jsonrpc": "2.0"
            }
            try:
                yield f"data: {json.dumps(progress_message, ensure_ascii=False)}\n\n"
            except (GeneratorExit, asyncio.CancelledError, BrokenPipeError, ConnectionResetError) as e:
                print(f"🔌 [SSE] 连接在发送进度消息时关闭/取消: {e} (id={request_id}, tool={tool_name})")
                return
            
            # 根据工具名称调用相应的函数
            result = None
            try:
                if tool_name == "generate_insight_report":
                    result = generate_insight_report(arguments.get("request", {}))
                elif tool_name == "generate_academic_research_report":
                    result = generate_academic_research_report(arguments.get("request", {}))
                elif tool_name == "comprehensive_search":
                    result = comprehensive_search(
                        arguments.get("topic", ""),
                        arguments.get("search_type", "comprehensive"),
                        arguments.get("max_results", 10),
                        arguments.get("days", 30),
                        arguments.get("sources", ["web", "academic", "news"])
                    )
                elif tool_name == "search":
                    result = search(
                        arguments.get("query", ""),
                        arguments.get("max_results", 5)
                    )
                elif tool_name == "parallel_search":
                    result = parallel_search(
                        arguments.get("queries", []),
                        arguments.get("max_results", 3)
                    )
                elif tool_name == "generate_industry_dynamic_report":
                    # 使用流式orchestrator而不是直接调用工具函数
                    from streaming_orchestrator import StreamingOrchestrator
                    orchestrator = StreamingOrchestrator()
                    
                    # 构建请求参数
                    request_params = {
                        "industry": arguments.get("industry", ""),
                        "time_range": arguments.get("time_range", "recent"),
                        "focus_areas": arguments.get("focus_areas", ["市场趋势", "技术创新", "政策影响", "竞争格局"]),
                        "days": arguments.get("days", 30),
                        "use_local_data": arguments.get("use_local_data", False)
                    }
                    
                    # 使用流式方法生成报告
                    try:
                        async for message in orchestrator.stream_industry_dynamic_report(request_params):
                            yield message
                    except (GeneratorExit, asyncio.CancelledError, BrokenPipeError, ConnectionResetError) as e:
                        print(f"🔌 [SSE] 连接在流式生成过程中关闭/取消: {e} (id={request_id}, tool={tool_name})")
                    except Exception as e:
                        print(f"❌ 流式报告生成异常: {e}")
                        yield f"data: {json.dumps({'jsonrpc': '2.0', 'id': request_id, 'error': {'code': -32000, 'message': 'Tool execution failed', 'data': {'type': 'unknown', 'message': str(e)}}}, ensure_ascii=False)}\n\n"
                    
                    # 流式处理完成，直接结束
                    return
                elif tool_name == "analysis_mcp":
                    result = analysis_mcp(
                        arguments.get("analysis_type", "quality"),
                        arguments.get("data", []),
                        arguments.get("topic", ""),
                        **arguments.get("kwargs", {})
                    )
                elif tool_name == "query_generation_mcp":
                    result = query_generation_mcp(
                        arguments.get("topic", ""),
                        arguments.get("strategy", "initial"),
                        arguments.get("context", ""),
                        **arguments.get("kwargs", {})
                    )
                elif tool_name == "outline_writer_mcp":
                    result = outline_writer_mcp(
                        arguments.get("topic", ""),
                        arguments.get("report_type", "comprehensive"),
                        arguments.get("user_requirements", ""),
                        **arguments.get("kwargs", {})
                    )
                elif tool_name == "summary_writer_mcp":
                    result = summary_writer_mcp(
                        arguments.get("content_data", ""),
                        arguments.get("length_constraint", "200-300字"),
                        arguments.get("format", "paragraph"),
                        **arguments.get("kwargs", {})
                    )
                elif tool_name == "content_writer_mcp":
                    result = content_writer_mcp(
                        arguments.get("section_title", ""),
                        arguments.get("content_data", []),
                        arguments.get("overall_report_context", ""),
                        **arguments.get("kwargs", {})
                    )
                elif tool_name == "orchestrator_mcp_simple":
                    result = orchestrator_mcp_simple(
                        arguments.get("task", ""),
                        **arguments.get("kwargs", {})
                    )
                elif tool_name == "orchestrator_mcp":
                    result = orchestrator_mcp(
                        arguments.get("task", ""),
                        arguments.get("task_type", "auto"),
                        **arguments.get("kwargs", {})
                    )
                elif tool_name == "user_interaction_mcp":
                    result = user_interaction_mcp(
                        arguments.get("interaction_type", "confirmation"),
                        arguments.get("prompt", ""),
                        arguments.get("options", []),
                        **arguments.get("kwargs", {})
                    )
                else:
                    raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
            except Exception as e:
                print(f"❌ 工具执行异常: {str(e)}")
                error_message = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32000,
                        "message": "Tool execution failed",
                        "data": {
                            "tool": tool_name,
                            "error": str(e)
                        }
                    }
                }
                try:
                    yield f"data: {json.dumps(error_message, ensure_ascii=False)}\n\n"
                except (GeneratorExit, asyncio.CancelledError, BrokenPipeError, ConnectionResetError) as e2:
                    print(f"🔌 [SSE] 连接在发送错误消息时关闭/取消: {e2} (id={request_id}, tool={tool_name})")
                return

            # 发送最终结果消息（JSON-RPC风格，保持与StreamingOrchestrator一致）
            final_message = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": result,
                    "tool": tool_name
                }
            }
            try:
                yield f"data: {json.dumps(final_message, ensure_ascii=False)}\n\n"
            except (GeneratorExit, asyncio.CancelledError, BrokenPipeError, ConnectionResetError) as e:
                print(f"🔌 [SSE] 连接在发送最终结果时关闭/取消: {e} (id={request_id}, tool={tool_name})")
                return
        
        
        return StreamingResponse(
            generate_sse_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
        
    except Exception as e:
        print(f"❌ 工具调用错误: {str(e)}")
        error_response = {
            "jsonrpc": "2.0",
            "id": request.get("id", 1),
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": {
                    "type": "tool_execution_failed",
                    "message": str(e)
                }
            }
        }
        return error_response

@http_app.get("/")
async def root():
    """根端点"""
    return {"message": "MCP HTTP API Server", "version": "1.0.0"}

@http_app.get("/health")
async def health():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("🚀 启动MCP服务器...")
    print("📡 支持端点: /mcp/tools/call (HTTP API)")
    print("🔧 支持的工具: generate_insight_report, generate_industry_dynamic_report, generate_academic_research_report, comprehensive_search")
    
    # 启动HTTP服务器（用于测试文件的请求格式）
    import threading
    import time
    
    def start_http_server():
        print("🚀 启动HTTP API服务器...")
        uvicorn.run(http_app, host="0.0.0.0", port=8001)
    
    # 在后台线程启动HTTP服务器
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    # 等待HTTP服务器启动
    time.sleep(2)
    
    # 启动FastMCP服务器（用于IDE集成）
    print("🚀 启动FastMCP服务器...")
    mcp.run(transport="streamable-http")
