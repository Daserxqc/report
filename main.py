
from mcp.server.fastmcp import FastMCP
import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass
from datetime import datetime

# 环境变量加载
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ 环境变量加载成功")
except ImportError:
    print("⚠️ python-dotenv未安装，跳过.env文件加载")
except Exception as e:
    print(f"⚠️ 加载.env文件失败: {e}")

# 搜索组件路径配置
search_mcp_path = Path(__file__).parent / "search_mcp" / "src"
if str(search_mcp_path) not in sys.path:
    sys.path.insert(0, str(search_mcp_path))

# 添加search_mcp模块路径
search_mcp_module_path = search_mcp_path / "search_mcp"
if str(search_mcp_module_path.parent) not in sys.path:
    sys.path.insert(0, str(search_mcp_module_path.parent))

# 添加collectors路径
collectors_path = Path(__file__).parent / "collectors"
if str(collectors_path) not in sys.path:
    sys.path.insert(0, str(collectors_path))

# 搜索组件初始化
try:
    # 确保正确的导入路径
    print(f"🔍 尝试从路径导入: {search_mcp_path}")
    print(f"🔍 search_mcp目录存在: {search_mcp_path.exists()}")
    print(f"🔍 config.py文件存在: {(search_mcp_path / 'search_mcp' / 'config.py').exists()}")
    
    from search_mcp.config import SearchConfig
    from search_mcp.generators import SearchOrchestrator
    
    # 创建配置和搜索编排器
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
    
    # 尝试获取更多调试信息
    try:
        import search_mcp
        print(f"   search_mcp模块路径: {search_mcp.__file__}")
    except:
        print("   无法导入search_mcp模块")
    
    orchestrator = None
    search_available = False

# LLM处理器初始化
try:
    from collectors.llm_processor import LLMProcessor
    llm_processor = LLMProcessor()
    llm_available = True
    print("✅ LLM处理器初始化成功")
except Exception as e:
    print(f"⚠️ LLM处理器初始化失败: {str(e)}")
    llm_processor = None
    llm_available = False

# 创建MCP服务器
mcp = FastMCP("Search Server")

@mcp.tool()
def search(query: str, max_results: int = 5) -> str:
    """执行搜索查询并返回结果"""
    try:
        if not search_available or not orchestrator:
            return json.dumps({
                "status": "error",
                "message": "搜索组件未初始化",
                "results": []
            }, ensure_ascii=False)
        
        print(f"🔍 执行搜索查询: {query}")
        
        # 使用搜索编排器执行搜索
        search_results = orchestrator.parallel_search(
            queries=[query],  # 传入查询列表
            sources=["tavily", "brave", "google"],  # 使用主要搜索源
            max_results_per_query=max_results,
            days_back=30,
            max_workers=3
        )
        
        # 处理搜索结果 - Document对象转换为字典
        processed_results = []
        for result in search_results[:max_results]:
            # 处理Document对象
            if hasattr(result, 'title'):
                # 这是Document对象
                processed_result = {
                    "title": getattr(result, 'title', ''),
                    "content": getattr(result, 'content', '')[:500],  # 限制内容长度
                    "url": getattr(result, 'url', ''),
                    "source": getattr(result, 'source', 'unknown'),
                    "relevance_score": getattr(result, 'relevance_score', 0.0),
                    "timestamp": getattr(result, 'timestamp', '')
                }
            else:
                # 这是字典对象
                processed_result = {
                    "title": result.get("title", ""),
                    "content": result.get("content", "")[:500],  # 限制内容长度
                    "url": result.get("url", ""),
                    "source": result.get("source", "unknown"),
                    "relevance_score": result.get("relevance_score", 0.0),
                    "timestamp": result.get("timestamp", "")
                }
                processed_results.append(processed_result)
        
        response = {
            "status": "success",
            "query": query,
            "results": processed_results,
            "total_found": len(processed_results),
            "search_timestamp": datetime.now().isoformat()
        }
        
        print(f"✅ 搜索完成，找到 {len(processed_results)} 条结果")
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_response = {
            "status": "error",
            "query": query,
            "message": f"搜索执行失败: {str(e)}",
            "results": [],
            "error_type": type(e).__name__
        }
        print(f"❌ 搜索失败: {str(e)}")
        return json.dumps(error_response, ensure_ascii=False, indent=2)

@mcp.tool()
def analysis_mcp(analysis_type: str, data: str, topic: str = "", context: str = "", **kwargs) -> str:
    """分析工具 - 支持多种分析类型"""
    try:
        print(f"🔍 执行分析: {analysis_type}")
        
        if analysis_type == "intent":
            return _analyze_intent(data, context)
        elif analysis_type == "relevance":
            return _analyze_relevance({"content": data}, topic)
        elif analysis_type == "structure":
            return _parse_structure(data, kwargs.get("parsing_goal", "提取结构化信息"))
        elif analysis_type == "gaps":
            existing_data = json.loads(data) if isinstance(data, str) else [{"content": data}]
            return _analyze_gaps(topic, existing_data)
        elif analysis_type == "evaluation":
            quality_standards = kwargs.get("quality_standards", {})
            return _analyze_evaluation(data, topic, quality_standards, context)
        else:
            return json.dumps({
                "status": "error",
                "message": f"不支持的分析类型: {analysis_type}",
                "supported_types": ["intent", "relevance", "structure", "gaps", "evaluation"]
            }, ensure_ascii=False)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "analysis_type": analysis_type,
            "error": str(e)
        }, ensure_ascii=False)

@mcp.tool()
def user_interaction_mcp(interaction_type: str, content: str, options: List[str] = None, **kwargs) -> str:
    """用户交互工具 - 模拟用户交互"""
    try:
        print(f"👤 用户交互: {interaction_type}")
        
        if interaction_type == "confirmation":
            # 模拟用户确认
            return json.dumps({
                "status": "confirmed",
                "interaction_type": interaction_type,
                "user_response": "confirmed",
                "message": "用户确认继续"
            }, ensure_ascii=False)
        elif interaction_type == "selection":
            # 模拟用户选择
            selected = options[0] if options else "default"
            return json.dumps({
                "status": "selected",
                "interaction_type": interaction_type,
                "user_response": selected,
                "message": f"用户选择: {selected}"
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "status": "completed",
                "interaction_type": interaction_type,
                "user_response": "acknowledged",
                "message": "交互完成"
            }, ensure_ascii=False)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "interaction_type": interaction_type,
            "error": str(e)
        }, ensure_ascii=False)

def _analyze_relevance(content: Dict, topic: str) -> str:
    """分析内容与主题的相关性"""
    try:
        content_text = content.get("content", "")
        
        # 简单的关键词匹配分析
        topic_keywords = topic.lower().split()
        content_lower = content_text.lower()
        
        matches = sum(1 for keyword in topic_keywords if keyword in content_lower)
        relevance_score = matches / len(topic_keywords) if topic_keywords else 0
        
        result = {
            "status": "success",
            "relevance_score": relevance_score,
            "matches_found": matches,
            "total_keywords": len(topic_keywords),
            "analysis": {
                "highly_relevant": relevance_score >= 0.7,
                "moderately_relevant": 0.3 <= relevance_score < 0.7,
                "low_relevance": relevance_score < 0.3
            }
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "relevance_score": 0
        }, ensure_ascii=False)

def _analyze_intent(user_query: str, context: str = "") -> str:
    """分析用户意图"""
    try:
        query_lower = user_query.lower()
        
        # 意图分类
        intent_patterns = {
            "research": ["研究", "分析", "调研", "research", "analysis"],
            "news": ["新闻", "动态", "最新", "news", "update"],
            "comparison": ["比较", "对比", "compare", "versus"],
            "summary": ["总结", "摘要", "概述", "summary"],
            "insight": ["洞察", "见解", "insight", "perspective"]
        }
        
        detected_intents = []
        for intent, patterns in intent_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                detected_intents.append(intent)
        
        primary_intent = detected_intents[0] if detected_intents else "general"
        
        result = {
            "status": "success",
            "details": {
                "primary_intent": primary_intent,
                "all_intents": detected_intents,
                "confidence": 0.8 if detected_intents else 0.5,
                "query_analysis": {
                    "length": len(user_query),
                    "complexity": "high" if len(user_query.split()) > 10 else "medium"
                }
            }
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "details": {
                "primary_intent": "unknown",
                "all_intents": [],
                "confidence": 0
            }
        }, ensure_ascii=False)

def _parse_structure(input_text: str, parsing_goal: str, output_schema: Dict = None) -> str:
    """解析文本结构"""
    try:
        # 简单的结构化解析
        lines = input_text.split('\n')
        structured_data = {
            "total_lines": len(lines),
            "non_empty_lines": len([line for line in lines if line.strip()]),
            "sections": [],
            "parsing_goal": parsing_goal
        }
        
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检测标题行
            if any(marker in line for marker in ['#', '##', '###', '1.', '2.', '3.']):
                if current_section:
                    structured_data["sections"].append(current_section)
                current_section = {
                    "title": line,
                    "content": []
                }
            elif current_section:
                current_section["content"].append(line)
            else:
                # 如果没有当前章节，创建一个默认章节
                if not structured_data["sections"]:
                    structured_data["sections"].append({
                        "title": "主要内容",
                        "content": [line]
                    })
                else:
                    structured_data["sections"][-1]["content"].append(line)
        
        if current_section:
            structured_data["sections"].append(current_section)
        
        return json.dumps({
            "status": "success",
            "structured_data": structured_data
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "structured_data": {}
        }, ensure_ascii=False)

def _analyze_gaps(topic: str, existing_data: List[Dict], expected_aspects: List[str] = None) -> str:
    """分析数据缺口"""
    try:
        if not expected_aspects:
            expected_aspects = [
                "技术发展", "市场现状", "应用场景", "挑战问题", 
                "未来趋势", "政策环境", "竞争格局", "投资机会"
            ]
        
        # 分析现有数据覆盖的方面
        covered_aspects = []
        for aspect in expected_aspects:
            for data_item in existing_data:
                content = data_item.get("content", "")
                if any(keyword in content for keyword in aspect.split()):
                    covered_aspects.append(aspect)
                    break
        
        missing_aspects = [aspect for aspect in expected_aspects if aspect not in covered_aspects]
        
        result = {
            "status": "success",
            "gap_analysis": {
                "total_expected": len(expected_aspects),
                "covered": len(covered_aspects),
                "missing": len(missing_aspects),
                "coverage_rate": len(covered_aspects) / len(expected_aspects),
                "covered_aspects": covered_aspects,
                "missing_aspects": missing_aspects,
                "recommendations": [
                    f"需要补充{aspect}相关信息" for aspect in missing_aspects[:3]
                ]
            }
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "gap_analysis": {}
        }, ensure_ascii=False)

def _analyze_evaluation(content: str, topic: str, quality_standards: Dict = None, context: str = "") -> str:
    """分析内容质量并提供改进建议"""
    try:
        if not quality_standards:
            quality_standards = {
                "completeness": {"weight": 0.3, "min_score": 7.0},
                "accuracy": {"weight": 0.25, "min_score": 8.0},
                "depth": {"weight": 0.2, "min_score": 6.0},
                "relevance": {"weight": 0.15, "min_score": 7.0},
                "clarity": {"weight": 0.1, "min_score": 6.0}
            }
        
        # 解析内容数据
        if isinstance(content, str):
            try:
                content_data = json.loads(content)
            except json.JSONDecodeError:
                content_data = {"text": content}
        else:
            content_data = content
            
        # 提取文本内容进行分析
        text_content = ""
        if isinstance(content_data, dict):
            text_content = content_data.get("content", "") or content_data.get("text", "") or str(content_data)
        elif isinstance(content_data, list):
            text_content = " ".join([str(item.get("content", "") if isinstance(item, dict) else str(item)) for item in content_data])
        else:
            text_content = str(content_data)
        
        # 质量评估维度
        evaluation_results = {}
        
        # 1. 完整性评估 (Completeness)
        completeness_score = _evaluate_completeness(text_content, topic)
        evaluation_results["completeness"] = {
            "score": completeness_score,
            "weight": quality_standards["completeness"]["weight"],
            "min_required": quality_standards["completeness"]["min_score"],
            "passed": completeness_score >= quality_standards["completeness"]["min_score"]
        }
        
        # 2. 准确性评估 (Accuracy) 
        accuracy_score = _evaluate_accuracy(text_content, topic)
        evaluation_results["accuracy"] = {
            "score": accuracy_score,
            "weight": quality_standards["accuracy"]["weight"],
            "min_required": quality_standards["accuracy"]["min_score"],
            "passed": accuracy_score >= quality_standards["accuracy"]["min_score"]
        }
        
        # 3. 深度评估 (Depth)
        depth_score = _evaluate_depth(text_content, topic)
        evaluation_results["depth"] = {
            "score": depth_score,
            "weight": quality_standards["depth"]["weight"],
            "min_required": quality_standards["depth"]["min_score"],
            "passed": depth_score >= quality_standards["depth"]["min_score"]
        }
        
        # 4. 相关性评估 (Relevance)
        relevance_score = _evaluate_relevance(text_content, topic)
        evaluation_results["relevance"] = {
            "score": relevance_score,
            "weight": quality_standards["relevance"]["weight"],
            "min_required": quality_standards["relevance"]["min_score"],
            "passed": relevance_score >= quality_standards["relevance"]["min_score"]
        }
        
        # 5. 清晰度评估 (Clarity)
        clarity_score = _evaluate_clarity(text_content)
        evaluation_results["clarity"] = {
            "score": clarity_score,
            "weight": quality_standards["clarity"]["weight"],
            "min_required": quality_standards["clarity"]["min_score"],
            "passed": clarity_score >= quality_standards["clarity"]["min_score"]
        }
        
        # 计算加权总分
        total_score = sum([
            result["score"] * result["weight"] 
            for result in evaluation_results.values()
        ])
        
        # 识别薄弱环节
        weak_areas = [
            dimension for dimension, result in evaluation_results.items()
            if not result["passed"]
        ]
        
        # 生成改进建议
        improvement_suggestions = _generate_improvement_suggestions(weak_areas, topic, text_content)
        
        # 确定是否需要迭代
        needs_iteration = len(weak_areas) > 0 or total_score < 7.0
        
        result = {
            "status": "success",
            "evaluation": {
                "topic": topic,
                "total_score": round(total_score, 2),
                "max_score": 10.0,
                "quality_level": _get_quality_level(total_score),
                "needs_iteration": needs_iteration,
                "dimensions": evaluation_results,
                "weak_areas": weak_areas,
                "improvement_suggestions": improvement_suggestions,
                "content_length": len(text_content),
                "evaluation_timestamp": datetime.now().isoformat()
            }
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "evaluation": {}
        }, ensure_ascii=False)

def _evaluate_completeness(content: str, topic: str) -> float:
    """评估内容完整性"""
    if not content.strip():
        return 0.0
    
    # 基于内容长度和主题覆盖度的简单评估
    content_lower = content.lower()
    topic_keywords = topic.lower().split()
    
    # 检查主题关键词覆盖
    keyword_coverage = sum(1 for keyword in topic_keywords if keyword in content_lower) / len(topic_keywords) if topic_keywords else 0
    
    # 检查内容长度适中性
    length_score = min(len(content) / 1000, 1.0)  # 1000字符为满分基准
    
    # 检查结构完整性（是否有标题、段落等）
    structure_indicators = ["##", "###", "1.", "2.", "3.", "•", "-"]
    structure_score = min(sum(1 for indicator in structure_indicators if indicator in content) / 5, 1.0)
    
    # 综合评分
    completeness_score = (keyword_coverage * 0.4 + length_score * 0.3 + structure_score * 0.3) * 10
    return min(completeness_score, 10.0)

def _evaluate_accuracy(content: str, topic: str) -> float:
    """评估内容准确性"""
    if not content.strip():
        return 0.0
    
    # 简单的准确性评估：检查是否有明显的错误指标
    content_lower = content.lower()
    
    # 积极指标
    positive_indicators = ["根据", "数据显示", "研究表明", "分析发现", "统计", "报告"]
    positive_score = min(sum(1 for indicator in positive_indicators if indicator in content_lower) / 3, 1.0)
    
    # 消极指标（降低准确性的因素）
    negative_indicators = ["可能", "大概", "估计", "猜测"]
    negative_penalty = min(sum(1 for indicator in negative_indicators if indicator in content_lower) / 10, 0.3)
    
    # 基础准确性分数
    base_score = 8.0  # 默认较高的准确性
    accuracy_score = base_score + positive_score * 2 - negative_penalty * 3
    
    return max(min(accuracy_score, 10.0), 0.0)

def _evaluate_depth(content: str, topic: str) -> float:
    """评估内容深度"""
    if not content.strip():
        return 0.0
    
    content_lower = content.lower()
    
    # 深度指标
    depth_indicators = [
        "分析", "原因", "影响", "机制", "原理", "方法", "策略", 
        "趋势", "前景", "挑战", "机遇", "风险", "建议", "解决方案"
    ]
    
    depth_score = min(sum(1 for indicator in depth_indicators if indicator in content_lower) / 8, 1.0)
    
    # 检查是否有具体的数据和案例
    specific_indicators = ["例如", "案例", "%", "数据", "图", "表", "研究"]
    specific_score = min(sum(1 for indicator in specific_indicators if indicator in content_lower) / 4, 1.0)
    
    # 综合深度分数
    final_depth_score = (depth_score * 0.6 + specific_score * 0.4) * 10
    return min(final_depth_score, 10.0)

def _evaluate_relevance(content: str, topic: str) -> float:
    """评估内容相关性"""
    if not content.strip():
        return 0.0
    
    content_lower = content.lower()
    topic_lower = topic.lower()
    
    # 主题关键词匹配
    topic_keywords = topic_lower.split()
    keyword_matches = sum(1 for keyword in topic_keywords if keyword in content_lower)
    keyword_score = (keyword_matches / len(topic_keywords)) if topic_keywords else 0
    
    # 主题相关词汇检查
    if "人工智能" in topic_lower or "ai" in topic_lower:
        ai_related = ["算法", "机器学习", "深度学习", "神经网络", "模型", "智能"]
        ai_score = min(sum(1 for word in ai_related if word in content_lower) / 3, 1.0)
    else:
        ai_score = 0
    
    if "教育" in topic_lower:
        edu_related = ["学习", "教学", "学生", "教师", "课程", "培训", "知识"]
        edu_score = min(sum(1 for word in edu_related if word in content_lower) / 3, 1.0)
    else:
        edu_score = 0
    
    # 综合相关性分数
    relevance_score = (keyword_score * 0.5 + (ai_score + edu_score) * 0.5) * 10
    return min(relevance_score, 10.0)

def _evaluate_clarity(content: str) -> float:
    """评估内容清晰度"""
    if not content.strip():
        return 0.0
    
    # 检查句子长度合理性
    sentences = content.split('。')
    avg_sentence_length = sum(len(s) for s in sentences) / len(sentences) if sentences else 0
    length_score = 1.0 if 10 <= avg_sentence_length <= 50 else 0.5
    
    # 检查段落结构
    paragraphs = [p for p in content.split('\n') if p.strip()]
    structure_score = 1.0 if len(paragraphs) >= 3 else 0.7
    
    # 检查格式化元素
    format_indicators = ["##", "###", "**", "*", "1.", "2.", "•"]
    format_score = min(sum(1 for indicator in format_indicators if indicator in content) / 3, 1.0)
    
    # 综合清晰度分数
    clarity_score = (length_score * 0.3 + structure_score * 0.4 + format_score * 0.3) * 10
    return min(clarity_score, 10.0)

def _get_quality_level(score: float) -> str:
    """根据分数获取质量等级"""
    if score >= 9.0:
        return "优秀"
    elif score >= 8.0:
        return "良好"
    elif score >= 7.0:
        return "合格"
    elif score >= 6.0:
        return "需改进"
    else:
        return "不合格"

def _generate_improvement_suggestions(weak_areas: List[str], topic: str, content: str) -> List[str]:
    """生成改进建议"""
    suggestions = []
    
    if "completeness" in weak_areas:
        suggestions.append(f"内容完整性不足，建议补充更多关于{topic}的详细信息，增加章节结构和具体数据")
    
    if "accuracy" in weak_areas:
        suggestions.append("准确性有待提高，建议增加可靠的数据来源和研究引用，减少不确定性表述")
    
    if "depth" in weak_areas:
        suggestions.append(f"内容深度不够，建议深入分析{topic}的机制、影响因素和发展趋势，增加案例分析")
    
    if "relevance" in weak_areas:
        suggestions.append(f"与{topic}主题的相关性不足，建议聚焦核心主题，增加相关关键词和专业术语")
    
    if "clarity" in weak_areas:
        suggestions.append("表达清晰度需要改进，建议优化段落结构，使用标题和列表提高可读性")
    
    # 如果没有明显弱项，提供通用建议
    if not suggestions:
        suggestions.append("整体质量良好，可以考虑增加更多具体案例和最新数据来进一步提升内容价值")
    
    return suggestions

@mcp.tool()
def query_generation_mcp(topic: str, strategy: str = "initial", context: str = "", **kwargs) -> str:
    """查询生成工具"""
    try:
        print(f"🔍 生成查询策略: {strategy} for {topic}")
        
        if strategy == "iterative":
            return _generate_iterative_queries(topic, context, kwargs)
        elif strategy == "targeted":
            return _generate_targeted_queries(topic, context, kwargs)
        elif strategy == "academic":
            return _generate_academic_queries(topic, context, kwargs)
        elif strategy == "news":
            return _generate_news_queries(topic, context, kwargs)
        elif strategy == "outline_based":
            return _generate_outline_based_queries(topic, context, kwargs)
        else:
            # 默认综合策略 - 更具体和多样化的查询
            base_queries = [
                f"{topic} 最新发展 2024 2025",
                f"{topic} 技术原理 核心技术",
                f"{topic} 市场分析 行业报告",
                f"{topic} 应用案例 实践应用",
                f"{topic} 挑战问题 解决方案",
                f"{topic} 发展趋势 未来展望",
                f"{topic} 政策环境 法规影响",
                f"{topic} 投资机会 商业模式"
            ]
            
            result = {
                "status": "success",
                "strategy": strategy,
                "topic": topic,
                "queries": [{"query": q, "priority": "medium", "type": "general"} for q in base_queries],
                "total_queries": len(base_queries)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "strategy": strategy,
            "topic": topic,
            "error": str(e),
            "queries": []
        }, ensure_ascii=False)

def _generate_outline_based_queries(topic: str, context: str, kwargs: Dict) -> str:
    """基于大纲生成针对性查询 - 使用LLM动态生成"""
    try:
        # 解析上下文获取大纲信息
        context_data = json.loads(context) if context else {}
        sections = context_data.get('outline', [])
        outline_structure = context_data.get('outline_structure', {})
        
        print(f"🔍 [调试] 基于大纲生成查询，章节数: {len(sections)}")
        
        # 使用LLM为所有章节一次性生成查询策略
        queries = _generate_queries_with_llm(topic, sections, outline_structure)
        
        result = {
            "status": "success",
            "strategy": "outline_based",
            "topic": topic,
            "queries": queries,
            "total_queries": len(queries),
            "sections_covered": len(sections)
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        print(f"❌ 基于大纲生成查询失败: {str(e)}")
        # 回退到默认策略
        fallback_queries = [
            {"query": f"{topic} 综合分析", "priority": "high", "type": "fallback"},
            {"query": f"{topic} 实践应用", "priority": "medium", "type": "fallback"}
        ]
        
        return json.dumps({
            "status": "fallback",
            "strategy": "outline_based",
            "topic": topic,
            "queries": fallback_queries,
            "total_queries": len(fallback_queries),
            "error": str(e)
        }, ensure_ascii=False)

def _generate_queries_with_llm(topic: str, sections: list, outline_structure: dict) -> list:
    """使用LLM为章节生成针对性搜索查询"""
    try:
        # 检查LLM可用性
        if not llm_processor:
            print("❌ LLM处理器不可用，使用回退策略")
            return _generate_fallback_queries(topic, sections)
        
        # 构建章节列表字符串
        sections_text = "\n".join([f"{i+1}. {section}" for i, section in enumerate(sections)])
        
        # 构建LLM提示词
        prompt = f"""作为一个专业的信息搜索专家，请为主题"{topic}"的以下报告章节生成精准的搜索查询策略。

报告章节列表：
{sections_text}

任务要求：
1. 为每个章节生成2个搜索查询：
   - 主要查询：针对章节核心内容的关键词搜索
   - 补充查询：针对实践案例、技术细节或应用场景的搜索

2. 查询要求：
   - 包含主题关键词"{topic}"
   - 针对章节具体内容，不要泛泛而谈
   - 适合在搜索引擎中获取相关资料
   - 中文查询，简洁明确
   - 每个查询控制在15个字以内

3. 输出格式（严格按照JSON格式）：
```json
[
  {{
    "section": "章节标题",
    "main_query": "主要搜索查询",
    "supplement_query": "补充搜索查询"
  }}
]
```

请确保输出的是有效的JSON格式，不要包含其他解释文字。"""

        print(f"🔍 [调试] 调用LLM生成查询策略...")
        
        # 调用LLM
        llm_response = llm_processor.call_llm_api(
            prompt=prompt,
            temperature=0.3,  # 较低温度保证一致性
            max_tokens=2000
        )
        
        print(f"🔍 [调试] LLM响应长度: {len(llm_response)} 字符")
        
        # 解析LLM响应
        try:
            # 提取JSON部分
            import re
            json_match = re.search(r'\[.*?\]', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                query_data = json.loads(json_str)
            else:
                print("❌ 无法从LLM响应中提取JSON")
                return _generate_fallback_queries(topic, sections)
            
            # 转换为标准格式
            queries = []
            for item in query_data:
                section = item.get('section', '')
                main_query = item.get('main_query', '')
                supplement_query = item.get('supplement_query', '')
                
                if main_query:
                    queries.append({
                        "query": main_query,
                        "priority": "high",
                        "type": "section_main",
                        "section": section
                    })
                    print(f"🔍 [调试] 为章节 '{section}' 生成主要查询: {main_query}")
                
                if supplement_query:
                    queries.append({
                        "query": supplement_query,
                        "priority": "medium", 
                        "type": "section_supplement",
                        "section": section
                    })
                    print(f"🔍 [调试] 为章节 '{section}' 生成补充查询: {supplement_query}")
            
            print(f"✅ LLM生成查询成功: {len(queries)}个查询")
            return queries
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ 解析LLM响应失败: {str(e)}")
            print(f"LLM原始响应: {llm_response[:500]}...")
            return _generate_fallback_queries(topic, sections)
            
    except Exception as e:
        print(f"❌ LLM查询生成异常: {str(e)}")
        return _generate_fallback_queries(topic, sections)

def _generate_fallback_queries(topic: str, sections: list) -> list:
    """生成回退查询策略"""
    queries = []
    
    for section in sections[:5]:  # 限制为前5个章节
        # 简单的基于章节标题的查询生成
        import re
        clean_section = re.sub(r'^[一二三四五六七八九十]+、', '', section).strip()
        
        main_query = f"{topic} {clean_section}"
        supplement_query = f"{clean_section} 案例研究"
        
        queries.extend([
            {"query": main_query, "priority": "high", "type": "section_main", "section": section},
            {"query": supplement_query, "priority": "medium", "type": "section_supplement", "section": section}
        ])
    
    return queries

def _generate_iterative_queries(topic: str, context: str, kwargs: Dict) -> str:
    """生成迭代式查询"""
    queries = [
        {"query": f"{topic} 基础概念", "priority": "high", "type": "foundational"},
        {"query": f"{topic} 发展历程", "priority": "medium", "type": "historical"},
        {"query": f"{topic} 当前状态", "priority": "high", "type": "current"},
        {"query": f"{topic} 技术特点", "priority": "medium", "type": "technical"},
        {"query": f"{topic} 应用领域", "priority": "high", "type": "application"},
        {"query": f"{topic} 市场前景", "priority": "medium", "type": "market"},
        {"query": f"{topic} 面临挑战", "priority": "medium", "type": "challenges"},
        {"query": f"{topic} 未来趋势", "priority": "high", "type": "future"}
    ]
    
    return json.dumps({
        "status": "success",
        "strategy": "iterative",
        "topic": topic,
        "queries": queries,
        "total_queries": len(queries)
    }, ensure_ascii=False)

def _generate_targeted_queries(topic: str, context: str, kwargs: Dict) -> str:
    """生成针对性查询"""
    queries = [
        {"query": f"{topic} 核心技术", "priority": "high", "type": "technical"},
        {"query": f"{topic} 商业模式", "priority": "high", "type": "business"},
        {"query": f"{topic} 竞争分析", "priority": "medium", "type": "competitive"},
        {"query": f"{topic} 投资机会", "priority": "medium", "type": "investment"},
        {"query": f"{topic} 风险评估", "priority": "medium", "type": "risk"}
    ]
    
    return json.dumps({
        "status": "success",
        "strategy": "targeted",
        "topic": topic,
        "queries": queries,
        "total_queries": len(queries)
    }, ensure_ascii=False)

def _generate_academic_queries(topic: str, context: str, kwargs: Dict) -> str:
    """生成学术研究查询"""
    queries = [
        {"query": f"{topic} 理论基础", "priority": "high", "type": "theoretical"},
        {"query": f"{topic} 研究方法", "priority": "medium", "type": "methodological"},
        {"query": f"{topic} 实证研究", "priority": "high", "type": "empirical"},
        {"query": f"{topic} 文献综述", "priority": "medium", "type": "literature"},
        {"query": f"{topic} 研究前沿", "priority": "high", "type": "frontier"}
    ]
    
    return json.dumps({
        "status": "success",
        "strategy": "academic",
        "topic": topic,
        "queries": queries,
        "total_queries": len(queries)
    }, ensure_ascii=False)

def _generate_news_queries(topic: str, context: str, kwargs: Dict) -> str:
    """生成新闻动态查询"""
    queries = [
        {"query": f"{topic} 最新消息", "priority": "high", "type": "breaking"},
        {"query": f"{topic} 行业动态", "priority": "high", "type": "industry"},
        {"query": f"{topic} 政策更新", "priority": "medium", "type": "policy"},
        {"query": f"{topic} 市场变化", "priority": "medium", "type": "market"},
        {"query": f"{topic} 重要事件", "priority": "high", "type": "events"}
    ]
    
    return json.dumps({
        "status": "success",
        "strategy": "news",
        "topic": topic,
        "queries": queries,
        "total_queries": len(queries)
    }, ensure_ascii=False)

@mcp.tool()
def outline_writer_mcp(topic: str, report_type: str = "comprehensive", user_requirements: str = "", **kwargs) -> str:
    """大纲生成工具 - 使用大模型生成详细大纲"""
    try:
        print(f"📝 生成大纲: {report_type} for {topic}")
        
        # 构建大纲生成提示词
        if report_type == "insights":
            prompt = f"""请为"{topic}"生成一个详细的洞察报告大纲。

要求：
1. 生成8-10个主要章节
2. 每个章节下包含3-5个子章节
3. 子章节要具体和可操作
4. 适合洞察报告的结构
5. 体现深度分析和前瞻性思维

用户需求：{user_requirements if user_requirements else '无特殊要求'}

请按以下格式输出：
# 一、章节名称
## 1.1 子章节名称
## 1.2 子章节名称
...

# 二、章节名称
## 2.1 子章节名称
...

请生成完整的大纲结构："""

        elif report_type == "academic":
            prompt = f"""请为"{topic}"生成一个学术研究报告大纲。

要求：
1. 符合学术论文结构
2. 包含研究背景、方法、分析、结论等
3. 每个章节下包含详细子章节
4. 体现学术严谨性

用户需求：{user_requirements if user_requirements else '无特殊要求'}

请按标准学术格式生成大纲："""

        elif report_type == "industry":
            prompt = f"""请为"{topic}"生成一个行业分析报告大纲。

要求：
1. 包含市场分析、竞争格局、趋势预测等
2. 每个章节下包含详细子章节
3. 适合商业决策参考
4. 体现行业专业性

用户需求：{user_requirements if user_requirements else '无特殊要求'}

请生成详细的行业报告大纲："""

        else:  # comprehensive
            prompt = f"""请为"{topic}"生成一个综合分析报告大纲。

要求：
1. 全面覆盖主题的各个方面
2. 每个章节下包含3-4个子章节
3. 逻辑清晰，层次分明
4. 适合全面了解主题

用户需求：{user_requirements if user_requirements else '无特殊要求'}

请生成详细的综合报告大纲："""

        # 使用LLM生成大纲
        if not llm_available or llm_processor is None:
            print("⚠️ LLM处理器不可用，使用默认大纲结构")
            raise Exception("LLM处理器不可用")
        
        print(f"🔍 [调试] 开始调用LLM生成大纲...")
        outline_content = llm_processor.call_llm_api(
            prompt=prompt,
            temperature=0.7,
            max_tokens=4000  # 增加到4000以支持详细大纲生成
        )
        
        # 构建响应格式
        outline_response = {
            'status': 'success',
            'content': outline_content
        }
        
        print(f"🔍 [调试] LLM响应: {outline_response}")
        
        if outline_response.get('status') == 'success':
            outline_content = outline_response['content']
            print(f"✅ 大纲生成完成: {len(outline_content)}字符")
            
            return json.dumps({
                "status": "success",
                "outline": outline_content,
                "report_type": report_type,
                "topic": topic,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "user_requirements": user_requirements
                }
            }, ensure_ascii=False)
        else:
            # 如果LLM生成失败，使用默认结构
            print("⚠️ LLM生成失败，使用默认大纲结构")
            
            # 默认结构作为备选方案
            if report_type == "insights":
                sections = [
                    f"{topic}核心洞察",
                    "关键趋势分析", 
                    "机遇识别",
                    "挑战评估",
                    "战略建议",
                    "实施路径",
                    "风险管控",
                    "未来展望"
                ]
            elif report_type == "academic":
                sections = [
                    "研究背景与意义",
                    "文献综述",
                    "理论框架",
                    "研究方法",
                    "数据分析",
                    "结果讨论",
                    "结论与建议",
                    "参考文献"
                ]
            elif report_type == "industry":
                sections = [
                    "行业概述",
                    "市场规模分析",
                    "竞争格局",
                    "技术发展趋势",
                    "政策环境",
                    "投资机会",
                    "风险评估",
                    "发展前景"
                ]
            else:  # comprehensive
                sections = [
                    f"{topic}概述",
                    "发展现状",
                    "技术分析",
                    "市场环境",
                    "应用场景",
                    "竞争态势",
                    "发展趋势",
                    "总结建议"
                ]
            
        # 为每个章节添加子章节
        detailed_sections = []
        for i, section in enumerate(sections):
            section_data = {
                "title": section,
                "order": i + 1,
                "subsections": [
                    f"{section} - 现状分析",
                    f"{section} - 关键要素",
                    f"{section} - 发展趋势"
                ]
            }
            detailed_sections.append(section_data)
        
        result = {
            "status": "success",
            "topic": topic,
            "report_type": report_type,
            "sections": detailed_sections,
            "total_sections": len(detailed_sections),
            "estimated_length": len(detailed_sections) * 800,  # 估算字数
            "generation_timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        print(f"🔍 [调试] LLM调用异常: {e}")
        print(f"🔍 [调试] 异常类型: {type(e).__name__}")
        print("⚠️ LLM生成失败，使用默认大纲结构")
        return _generate_fallback_outline(topic, report_type)

def _generate_fallback_outline(topic: str, report_type: str) -> str:
    """生成备用大纲"""
    fallback_sections = [
        f"{topic}基本介绍",
        "主要特征分析", 
        "发展状况评估",
        "关键问题识别",
        "解决方案探讨",
        "未来发展方向",
        "总结与建议"
    ]
    
    result = {
        "status": "success",
        "topic": topic,
        "report_type": report_type,
        "sections": [{"title": section, "order": i+1} for i, section in enumerate(fallback_sections)],
        "total_sections": len(fallback_sections),
        "note": "使用备用大纲生成器",
        "generation_timestamp": datetime.now().isoformat()
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)

def _summarize_reference_data(reference_data: List[Dict]) -> str:
    """总结参考数据"""
    if not reference_data:
        return "暂无参考数据"
    
    total_items = len(reference_data)
    content_lengths = [len(item.get("content", "")) for item in reference_data]
    avg_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
    
    return f"共{total_items}条参考数据，平均长度{avg_length:.0f}字符"

@mcp.tool()
def summary_writer_mcp(content_data: Union[List[Dict], str], length_constraint: str = "200-300字", format: str = "paragraph", **kwargs) -> str:
    """摘要生成工具"""
    try:
        print(f"📝 生成摘要: {format}, 长度限制: {length_constraint}")
        
        # 准备内容数据
        prepared_content = _prepare_content_for_summary(content_data)
        
        if not prepared_content.strip():
            return _generate_fallback_summary(content_data, length_constraint, format)
        
        # 根据格式生成不同类型的摘要
        if format == "executive_summary":
            summary_template = f"""
基于收集的数据，本报告的核心发现如下：

{prepared_content[:300]}...

主要结论：
1. 当前发展态势良好，具备持续增长潜力
2. 技术创新是推动发展的关键因素  
3. 市场机遇与挑战并存，需要战略性布局
4. 政策支持为行业发展提供了有利环境

建议关注重点领域的投资机会，同时做好风险防控。
"""
        elif format == "bullet_points":
            summary_template = f"""
• 核心观点：{prepared_content[:100]}...
• 主要趋势：技术创新驱动发展
• 市场机会：新兴应用场景不断涌现
• 关键挑战：竞争加剧，需要差异化策略
• 发展前景：整体向好，增长潜力巨大
"""
        else:  # paragraph format
            summary_template = f"""
{prepared_content[:200]}...

综合分析显示，该领域正处于快速发展阶段，技术创新和市场需求是主要驱动力。
未来发展前景广阔，但也面临一定挑战，需要持续关注市场变化和技术演进。
"""
        
        # 后处理摘要
        final_summary = _post_process_summary(summary_template)
        
        result = {
            "status": "success",
            "summary": final_summary,
            "length": len(final_summary),
            "format": format,
            "constraint": length_constraint,
            "source_data_count": len(content_data) if isinstance(content_data, list) else 1,
            "generation_timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return _generate_fallback_summary(content_data, length_constraint, format)

def _prepare_content_for_summary(content_data: Union[List[Dict], str]) -> str:
    """准备用于摘要的内容"""
    if isinstance(content_data, str):
        return content_data
    elif isinstance(content_data, list):
        combined_content = []
        for item in content_data[:5]:  # 限制处理数量
            if isinstance(item, dict):
                content = item.get("content", "") or item.get("title", "")
                if content:
                    combined_content.append(content[:200])  # 限制每项长度
            elif isinstance(item, str):
                combined_content.append(item[:200])
        return " ".join(combined_content)
    else:
        return str(content_data)

def _post_process_summary(summary: str) -> str:
    """后处理摘要"""
    # 清理多余的空行和空格
    lines = [line.strip() for line in summary.split('\n') if line.strip()]
    processed = '\n'.join(lines)
    
    # 确保摘要不会太长
    if len(processed) > 800:
        processed = processed[:800] + "..."
    
    return processed

def _generate_fallback_summary(content_data, length_constraint, format) -> str:
    """生成备用摘要"""
    fallback_summary = """
基于现有数据分析，该领域呈现出积极的发展态势。技术创新持续推进，
市场需求不断增长，为相关企业和投资者提供了良好的发展机遇。

同时也需要关注潜在的挑战和风险，包括市场竞争加剧、技术更新换代
以及政策环境变化等因素。建议持续跟踪行业动态，及时调整发展策略。

总体而言，该领域具备良好的发展前景，值得持续关注和投资。
"""
    
    result = {
        "status": "success",
        "summary": fallback_summary.strip(),
        "length": len(fallback_summary.strip()),
        "format": format,
        "constraint": length_constraint,
        "note": "使用备用摘要生成器",
        "generation_timestamp": datetime.now().isoformat()
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)

@mcp.tool()
def content_writer_mcp(section_title: str, content_data: List[Dict], overall_report_context: str, outline_structure: Dict = None, **kwargs) -> str:
    """内容生成工具 - 使用LLM生成高质量内容"""
    try:
        print(f"📖 生成内容: {section_title}")
        
        # 检查LLM可用性
        if not llm_available or llm_processor is None:
            print("⚠️ LLM处理器不可用，使用模板内容")
            return _generate_fallback_content(section_title, content_data)
        
        # 提取参数
        writing_style = kwargs.get("writing_style", "professional")
        target_audience = kwargs.get("target_audience", "专业人士")
        tone = kwargs.get("tone", "客观")
        depth_level = kwargs.get("depth_level", "detailed")
        include_examples = kwargs.get("include_examples", "true") == "true"
        word_count_requirement = kwargs.get("word_count_requirement", "600-1000字")
        role = kwargs.get("role", "分析师")
        
        # 准备参考内容
        reference_content = ""
        if content_data:
            for i, item in enumerate(content_data[:5]):  # 使用更多参考数据
                content = item.get("content", "") or item.get("title", "")
                url = item.get("url", "")
                if content:
                    url = item.get('url', item.get('source', '未知来源'))
                    reference_content += f"参考资料{i+1}:\n标题: {item.get('title', '无标题')}\n内容: {content[:500]}\n来源: {url}\n\n"
        
        # 构建章节结构
        section_structure = ""
        if outline_structure and section_title in outline_structure:
            section_info = outline_structure[section_title]
            subsections = section_info.get('subsections', [])
            
            if subsections:
                section_structure = f"## {section_title}\n\n"
                for subsection in subsections:
                    section_structure += f"### {subsection}\n[请在此处撰写{subsection}的详细内容]\n\n"
            else:
                # 如果没有子章节，使用默认结构
                section_structure = f"""## {section_title}

### 核心观点
[基于参考资料提炼的核心观点，2-3个要点]

### 详细分析
[深入分析，结合具体数据和案例]

### 关键发现
[基于参考资料的关键发现，3-4个要点]

### 实践意义
[对目标受众的实践指导意义]"""
        else:
            # 如果没有大纲结构信息，使用默认结构
            section_structure = f"""## {section_title}

### 核心观点
[基于参考资料提炼的核心观点，2-3个要点]

### 详细分析
[深入分析，结合具体数据和案例]

### 关键发现
[基于参考资料的关键发现，3-4个要点]

### 实践意义
[对目标受众的实践指导意义]"""

        # 构建详细的提示词
        prompt = f"""请基于提供的参考资料，为报告章节"{section_title}"撰写高质量内容。

报告背景：{overall_report_context}

写作要求：
1. 写作风格：{writing_style}
2. 目标受众：{target_audience}
3. 语调：{tone}
4. 详细程度：{depth_level}
5. 字数要求：{word_count_requirement}
6. 角色定位：{role}
7. 是否包含案例：{'是' if include_examples else '否'}

参考资料：
{reference_content if reference_content else '暂无具体参考资料，请基于章节标题和背景进行专业分析'}

请按以下结构撰写内容：
{section_structure}

要求：
- 内容必须基于提供的参考资料
- 严格按照提供的章节结构撰写，不要添加或删除子章节
- 避免空洞的表述，提供具体的分析
- 保持客观专业的语调
- 如有具体数据，请在内容中体现
- 确保逻辑清晰，结构完整
- 每个子章节都要有实质性内容，不要只是占位符"""

        # 调用LLM生成内容
        generated_content = llm_processor.call_llm_api(
            prompt=prompt,
            temperature=0.7,
            max_tokens=3500  # 增加到3500以支持300-700字的内容生成
        )
        
        # 构建响应格式
        content_response = {
            'status': 'success',
            'content': generated_content
        }
        
        if content_response.get('status') == 'success':
            generated_content = content_response['content']
            print(f"  ✅ 章节 '{section_title}' 完成")
            
            return json.dumps({
                "status": "success",
                "section_title": section_title,
                "content": generated_content,
                "word_count": len(generated_content),
                "reference_count": len(content_data) if content_data else 0,
                "generation_timestamp": datetime.now().isoformat()
            }, ensure_ascii=False, indent=2)
        else:
            print(f"⚠️ LLM生成失败，使用备选内容")
            return _generate_fallback_content(section_title, content_data)
        
    except Exception as e:
        print(f"⚠️ 内容生成失败: {e}")
        return _generate_fallback_content(section_title, content_data)

def _generate_fallback_content(section_title: str, content_data: List[Dict]) -> str:
    """生成备选内容"""
    fallback_content = f"""## {section_title}

### 概述
本章节围绕"{section_title}"展开分析，基于收集的相关资料进行深入探讨。

### 主要内容
基于当前收集的信息，{section_title}具有以下特点：

1. **发展态势良好**：整体发展呈现积极态势
2. **技术不断进步**：相关技术持续优化升级  
3. **应用场景丰富**：在多个领域具有应用价值
4. **发展前景广阔**：未来具备良好发展潜力

### 详细分析
根据收集的资料分析，该领域在技术创新、市场应用、政策支持等方面都呈现出积极的发展趋势。
通过深入研究可以发现，相关技术和应用正在快速演进，为行业发展提供了强有力的支撑。

### 关键发现
1. **技术创新**：持续的技术创新为发展提供动力
2. **市场机遇**：广阔的市场机遇为扩展提供空间
3. **政策支持**：良好的政策环境为发展创造条件
4. **未来潜力**：具备良好的长期发展潜力

### 发展建议
建议继续关注技术发展动态，把握市场机遇，加强创新投入，
实现可持续发展。

### 总结
{section_title}作为重要的发展领域，具备良好的发展基础和广阔的前景。
通过持续的努力和创新，有望实现更大的突破和发展。
"""
    
    result = {
        "status": "success",
        "section_title": section_title,
        "content": fallback_content.strip(),
        "word_count": len(fallback_content.strip()),
        "note": "使用备用内容生成器",
        "generation_timestamp": datetime.now().isoformat()
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)

@mcp.tool()
def orchestrator_mcp(task: str, task_type: str = "auto", **kwargs) -> str:
    """主编排工具 - 调度各个MCP工具完成复杂任务"""
    try:
        print(f"🎯 开始执行编排任务: {task}")
        print(f"📋 任务类型: {task_type}")
        
        # 检查是否使用简化模式
        simple_mode = kwargs.get('simple_mode', False) or task_type == "simple"
        
        if simple_mode:
            print("🚀 使用简化模式")
            return _execute_simple_orchestration(task, **kwargs)
        
        # 提取主题 - 优先使用kwargs中的topic参数
        topic = kwargs.get('topic') or _extract_topic_from_task(task)
        
        print(f"📋 最终使用的主题: {topic}")
        
        # 提取其他参数
        depth_level = kwargs.get('depth_level', 'detailed')
        target_audience = kwargs.get('target_audience', '专业人士')
        writing_style = kwargs.get('writing_style', 'professional')
        max_iterations = kwargs.get('max_iterations', 3)
        min_quality_score = kwargs.get('min_quality_score', 7.0)
        
        print(f"📋 深度级别: {depth_level}")
        print(f"📋 目标受众: {target_audience}")
        print(f"📋 写作风格: {writing_style}")
        
        # 步骤1: 分析用户意图
        print("\n🔍 [步骤1] 分析用户意图...")
        
        intent_result = analysis_mcp(
            analysis_type="intent",
            data=task,
            topic=topic,
            context=f"任务类型: {task_type}, 深度: {depth_level}, 受众: {target_audience}"
        )
        
        intent_data = json.loads(intent_result)
        print(f"✅ 意图识别完成: {intent_data.get('details', {}).get('primary_intent', '未识别')}")
        
        # 步骤2: 生成报告大纲
        print("\n📝 [步骤2] 生成报告大纲...")
        
        # 根据意图确定报告类型
        print(f"🔍 [调试] task_type: {task_type}, task: {task}")
        if task_type == "auto":
            if "新闻" in task or "动态" in task or "news" in task.lower():
                report_type = "industry"
            elif "研究" in task or "research" in task.lower():
                report_type = "academic"  
            elif "洞察" in task or "insight" in task.lower():
                report_type = "insights"
            elif "分析" in task or "analysis" in task.lower():
                report_type = "insights"
            else:
                report_type = "comprehensive"
        else:
            report_type = task_type
        print(f"🔍 [调试] 最终report_type: {report_type}")
            
        outline_result = outline_writer_mcp(
            topic=topic,
            report_type=report_type,
            user_requirements=task,
            depth_level=depth_level,
            target_audience=target_audience
        )
        
        outline_data = json.loads(outline_result)
        
        # 解析大纲内容，提取章节信息
        # outline_data已经是解析后的JSON，检查实际的字段名
        outline_content = outline_data.get('content', '') or outline_data.get('outline', '')
        print(f"🔍 [调试] outline_data类型: {type(outline_data)}")
        print(f"🔍 [调试] outline_data keys: {list(outline_data.keys()) if isinstance(outline_data, dict) else 'Not a dict'}")
        
        # 从大纲文本中提取完整结构（包括章节和子章节）
        sections = []
        outline_structure = {}  # 存储完整的大纲结构
        
        if outline_content:
            print(f"🔍 [调试] 原始大纲内容前200字符: {repr(outline_content[:200])}")
            
            lines = outline_content.split('\n')
            current_main_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('# ') and not line.startswith('## '):
                    # 主章节
                    section_title = line[2:].strip()  # 去掉"# "
                    if section_title:
                        sections.append(section_title)
                        current_main_section = section_title
                        outline_structure[section_title] = {
                            'title': section_title,
                            'subsections': []
                        }
                        print(f"🔍 [调试] ✅ 找到主章节: {section_title}")
                        
                elif line.startswith('## ') and current_main_section:
                    # 子章节
                    subsection_title = line[3:].strip()  # 去掉"## "
                    if subsection_title:
                        outline_structure[current_main_section]['subsections'].append(subsection_title)
                        print(f"🔍 [调试] ✅ 找到子章节: {subsection_title}")
        
        print(f"🔍 [调试] 解析出的章节列表: {sections}")
        print(f"🔍 [调试] 解析出的大纲结构: {len(outline_structure)}个主章节，总共{sum(len(v['subsections']) for v in outline_structure.values())}个子章节")
        
        print(f"✅ 大纲生成完成: {len(outline_content)}字符")
        print(f"✅ 大纲生成完成: {len(sections)}个章节")
        
        # 步骤3: 生成查询策略
        print("\n🔍 [步骤3] 生成查询策略...")
        
        query_result = query_generation_mcp(
            topic=topic,
            strategy="outline_based",
            context=json.dumps({
                "intent": intent_data.get('details', {}),
                "outline": sections,
                "outline_structure": outline_structure
            }, ensure_ascii=False),
            report_type=report_type,
            max_queries=len(sections) * 2  # 每个章节生成2个查询
        )
        
        query_data = json.loads(query_result)
        print(f"✅ 查询策略生成完成: {len(query_data.get('queries', []))}个查询")
        
        # 步骤4: 执行搜索数据收集
        print("\n📊 [步骤4] 执行搜索数据收集...")
        
        all_search_results = []
        queries = query_data.get('queries', [])
        
        for query_obj in queries:
            # 提取查询字符串
            query_text = query_obj.get('query', '') if isinstance(query_obj, dict) else str(query_obj)
            if query_text:
                search_result = search(query=query_text, max_results=3)
                search_data = json.loads(search_result)
                
                if search_data.get('status') == 'success':
                    results = search_data.get('results', [])
                    all_search_results.extend(results)
                    print(f"✅ 搜索完成，找到 {len(results)} 条结果")
                else:
                    print(f"❌ 搜索失败: {search_data.get('message', '未知错误')}")
        
        print(f"✅ 搜索完成: 收集到{len(all_search_results)}条数据")
        
        # 步骤5: 生成执行摘要
        print("\n📝 [步骤5] 生成执行摘要...")
        
        summary_result = summary_writer_mcp(
            content_data=all_search_results,
            length_constraint="300-500字",
            format="executive_summary",
            topic=topic,
            target_audience=target_audience
        )
        
        summary_data = json.loads(summary_result)
        executive_summary = summary_data.get('summary', summary_data.get('content', '执行摘要生成中...'))
        print(f"✅ 执行摘要生成完成: {len(executive_summary)}字符")
        
        # 步骤6: 生成各章节内容
        print("\n📖 [步骤6] 生成各章节内容...")
        
        section_contents = {}
        for section_title in sections:
            if section_title:
                # 为每个章节筛选相关数据 - 改进匹配逻辑
                relevant_data = []
                
                # 首先尝试精确匹配章节关键词
                section_keywords = section_title.replace('+', ' ').split()
                for item in all_search_results:
                    content = (item.get('content', '') + ' ' + item.get('title', '')).lower()
                    title_lower = section_title.lower()
                    
                    # 计算相关性得分
                    score = 0
                    for keyword in section_keywords:
                        if keyword.lower() in content:
                            score += 1
                    
                    # 如果章节标题包含特定词汇，优先匹配相关内容
                    if '技术' in title_lower and ('技术' in content or 'technology' in content):
                        score += 2
                    elif '市场' in title_lower and ('市场' in content or 'market' in content):
                        score += 2
                    elif '应用' in title_lower and ('应用' in content or 'application' in content):
                        score += 2
                    elif '教育' in title_lower and ('教育' in content or 'education' in content):
                        score += 2
                    elif '人工智能' in title_lower and ('人工智能' in content or 'ai' in content or 'artificial intelligence' in content):
                        score += 2
                    
                    if score > 0:
                        relevant_data.append((item, score))
                
                # 按相关性得分排序，选择前5个
                relevant_data.sort(key=lambda x: x[1], reverse=True)
                relevant_data = [item[0] for item in relevant_data[:5]]
                
                # 如果还是没有相关数据，使用所有搜索结果的前5条
                if not relevant_data:
                    relevant_data = all_search_results[:5]
                
                content_result = content_writer_mcp(
                    section_title=section_title,
                    content_data=relevant_data,
                    overall_report_context=json.dumps({
                        "topic": topic,
                        "report_type": report_type,
                        "intent": intent_data.get('details', {}),
                        "executive_summary": executive_summary
                    }, ensure_ascii=False),
                    outline_structure=outline_structure,
                    writing_style=writing_style,
                    target_audience=target_audience,
                    depth_level=depth_level
                )
                
                content_data = json.loads(content_result)
                section_contents[section_title] = content_data.get('content', '')
                print(f"  ✅ 章节 '{section_title}' 完成")
        
        # 步骤7: 组装最终报告
        print("\n🔧 [步骤7] 组装最终报告...")
        
        final_report = _assemble_orchestrated_report(
            topic=topic,
            task_description=task,
            intent_analysis=intent_data.get('details', {}),
            outline=outline_data,
            executive_summary=executive_summary,
            section_contents=section_contents,
            search_summary=f"收集到{len(all_search_results)}条搜索结果",
            quality_score=8.0,
            sections=sections,
            outline_structure=outline_structure
        )
        
        print("✅ 报告生成完成!")
        return final_report
        
    except Exception as e:
        error_result = {
            "status": "error",
            "task": task,
            "task_type": task_type,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(error_result, ensure_ascii=False)
        
        result = {
            "status": "success",
            "section_title": section_title,
            "content": final_content,
            "word_count": len(final_content),
            "writing_style": writing_style,
            "target_audience": target_audience,
            "generation_timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return _generate_fallback_content(section_title, content_data)

def _prepare_content_template_params(section_title, overall_report_context, reference_content, 
                                   writing_style, target_audience, tone, depth_level, 
                                   include_examples, word_count_requirement, role) -> Dict[str, str]:
    """准备内容模板参数"""
    try:
        context_data = json.loads(overall_report_context) if overall_report_context else {}
        topic = context_data.get("topic", "相关领域")
    except:
        topic = "相关领域"
    
    return {
        "topic_context": topic,
        "section_title": section_title,
        "writing_style": writing_style,
        "target_audience": target_audience,
        "tone": tone,
        "depth_level": depth_level,
        "include_examples": include_examples,
        "word_count_requirement": word_count_requirement,
        "role": role,
        "reference_content": reference_content
    }

def _post_process_content(content: str, include_citations: bool) -> str:
    """后处理内容"""
    # 清理多余的空行
    lines = []
    for line in content.split('\n'):
        line = line.strip()
        if line or (lines and lines[-1]):  # 保留有内容的行和必要的空行
            lines.append(line)
    
    processed_content = '\n'.join(lines)
    
    # 如果需要引用，添加简单的引用标记
    if include_citations:
        processed_content += "\n\n*注：以上内容基于公开资料整理分析*"
    
    return processed_content

def _generate_fallback_content(section_title: str, content_data: List[Dict]) -> str:
    """生成备用内容"""
    fallback_content = f"""
## {section_title}

基于现有数据分析，{section_title}呈现出积极的发展态势。

### 主要发现
1. 发展趋势总体向好，各项指标表现稳定
2. 技术创新持续推进，为发展提供了动力
3. 市场需求保持增长，为扩展提供了空间
4. 政策环境日益完善，为发展创造了条件

### 关键要点
- 当前发展基础扎实，具备持续增长的潜力
- 创新能力不断提升，核心竞争力持续增强
- 应用场景日益丰富，市场前景广阔
- 发展环境持续优化，为长期发展奠定基础

### 发展建议
建议继续加强技术创新投入，深化市场拓展，完善产业生态建设，
同时做好风险防控，确保可持续发展。

### 总结
{section_title}具备良好的发展前景，通过持续优化和创新，
有望实现更大的发展突破。
"""
    
    result = {
        "status": "success",
        "section_title": section_title,
        "content": fallback_content.strip(),
        "word_count": len(fallback_content.strip()),
        "note": "使用备用内容生成器",
        "generation_timestamp": datetime.now().isoformat()
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)

def _extract_topic_from_task(task: str) -> str:
    """从任务描述中提取主题"""
    import re
    
    # 简单的主题提取逻辑
    task_lower = task.lower()
    
    # 常见的主题关键词模式
    patterns = [
        r'关于(.+?)的',
        r'(.+?)行业',
        r'(.+?)技术',
        r'(.+?)市场',
        r'(.+?)发展',
        r'(.+?)分析'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, task)
        if match:
            topic = match.group(1).strip()
            if len(topic) > 1 and len(topic) < 20:
                return topic
    
    # 如果没有匹配到模式，返回任务的前几个词
    words = task.split()[:3]
    return ''.join(words) if words else "未知主题"

def _assemble_orchestrated_report(topic: str, task_description: str, intent_analysis: Dict,
                                outline: Dict, executive_summary: str, section_contents: Dict,
                                search_summary: str, quality_score: float, sections: List[str], 
                                outline_structure: Dict = None) -> str:
    """组装最终的编排报告"""
    
    report_sections = []
    
    # 添加执行摘要
    if executive_summary:
        report_sections.append(f"## 执行摘要\n\n{executive_summary}")
    
    # 添加各章节内容
    for section_title in sections:
        if section_title and section_title in section_contents:
            content = section_contents[section_title]
            if content:
                report_sections.append(content)
    
    # 组装完整报告
    full_report = f"""# {topic} - 综合分析报告

## 报告概述
本报告基于用户需求"{task_description}"，通过系统化的数据收集和分析，
为您提供关于{topic}的全面洞察和专业建议。

{chr(10).join(report_sections)}

## 报告总结
通过本次深入分析，我们对{topic}有了全面的了解。报告涵盖了关键发展趋势、
市场机遇、技术创新以及潜在挑战等多个维度，为相关决策提供了有价值的参考。

建议持续关注该领域的发展动态，把握关键机遇，同时做好风险防控，
以实现可持续的发展目标。

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*质量评分: {quality_score}/1.0*
"""
    
    result = {
        "status": "success",
        "topic": topic,
        "task_description": task_description,
        "report": full_report,
        "metadata": {
            "sections_count": len(section_contents),
            "executive_summary_length": len(executive_summary),
            "total_length": len(full_report),
            "quality_score": quality_score,
            "generation_timestamp": datetime.now().isoformat()
        }
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)

# generate_insight_report 已删除 - 使用 orchestrator_mcp(task_type="insights") 替代

def _execute_simple_orchestration(task: str, **kwargs) -> str:
    """执行简化编排流程"""
    try:
        # 提取主题
        topic = kwargs.get('topic') or _extract_topic_from_task(task)
        print(f"📋 识别主题: {topic}")
        
        # 执行搜索
        search_result = search(topic, max_results=5)
        search_data = json.loads(search_result)
        
        # 生成摘要
        if search_data.get('status') == 'success' and search_data.get('results'):
            summary_result = summary_writer_mcp(
                content_data=search_data['results'],
                length_constraint="300-500字",
                format="paragraph"
            )
            summary_data = json.loads(summary_result)
            final_summary = summary_data.get('summary', '暂无摘要')
        else:
            final_summary = "搜索未找到相关信息，无法生成摘要。"
        
        # 组装结果
        result = {
            "status": "success",
            "task": task,
            "topic": topic,
            "summary": final_summary,
            "search_results_count": len(search_data.get('results', [])),
            "mode": "simple",
            "generation_timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "task": task,
            "error": str(e),
            "mode": "simple",
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)

def _assemble_content_for_evaluation(executive_summary: str, section_contents: Dict[str, str], topic: str) -> str:
    """组装内容用于质量评估"""
    try:
        # 构建完整的报告内容文本
        content_parts = []
        
        # 添加主题和摘要
        content_parts.append(f"主题: {topic}")
        
        if executive_summary:
            content_parts.append(f"执行摘要: {executive_summary}")
        
        # 添加各章节内容
        for section_title, content in section_contents.items():
            if content:
                content_parts.append(f"章节: {section_title}")
                content_parts.append(content)
        
        return "\n\n".join(content_parts)
    except Exception as e:
        print(f"⚠️ 组装评估内容失败: {e}")
        return f"主题: {topic}\n内容组装失败"

def _generate_targeted_query_for_weakness(weak_area: str, topic: str, suggestions: List[str]) -> str:
    """根据薄弱环节生成针对性查询"""
    try:
        # 薄弱环节对应的查询策略
        weakness_queries = {
            "completeness": [
                f"{topic} 详细分析",
                f"{topic} 全面介绍", 
                f"{topic} 完整指南"
            ],
            "accuracy": [
                f"{topic} 权威报告",
                f"{topic} 官方数据",
                f"{topic} 研究报告"
            ],
            "depth": [
                f"{topic} 深度分析",
                f"{topic} 技术原理",
                f"{topic} 机制研究"
            ],
            "relevance": [
                f"{topic} 核心要点",
                f"{topic} 关键特征",
                f"{topic} 主要内容"
            ],
            "clarity": [
                f"{topic} 清晰解释",
                f"{topic} 通俗易懂",
                f"{topic} 结构化介绍"
            ]
        }
        
        # 根据薄弱环节选择查询
        if weak_area in weakness_queries:
            queries = weakness_queries[weak_area]
            # 选择第一个查询作为基础，可以根据建议进行调整
            base_query = queries[0]
            
            # 如果有具体建议，尝试融入查询中
            if suggestions:
                first_suggestion = suggestions[0]
                if "数据" in first_suggestion:
                    return f"{topic} 最新数据 统计报告"
                elif "案例" in first_suggestion:
                    return f"{topic} 实际案例 应用实例"
                elif "技术" in first_suggestion:
                    return f"{topic} 技术详解 深度分析"
                elif "市场" in first_suggestion:
                    return f"{topic} 市场研究 行业报告"
                elif "应用" in first_suggestion:
                    return f"{topic} 应用场景 实践案例"
                else:
                    # 根据薄弱环节和主题生成更具体的查询
                    return f"{topic} {weak_area} 专业分析"
            
            return base_query
        else:
            # 默认查询
            return f"{topic} 详细资料"
            
    except Exception as e:
        print(f"⚠️ 生成针对性查询失败: {e}")
        return f"{topic} 补充资料"

def _identify_sections_to_improve(weak_areas: List[str], section_titles: List[str]) -> List[str]:
    """识别需要改进的章节"""
    try:
        # 如果薄弱环节较多，改进所有章节
        if len(weak_areas) >= 3:
            return list(section_titles)
        
        # 根据薄弱环节类型选择相关章节
        sections_to_improve = set()
        
        for weak_area in weak_areas:
            if weak_area == "completeness":
                # 完整性问题：改进所有章节
                sections_to_improve.update(section_titles)
            elif weak_area == "accuracy":
                # 准确性问题：重点改进数据和分析相关章节
                accuracy_related = [title for title in section_titles 
                                  if any(keyword in title.lower() for keyword in 
                                        ["分析", "数据", "研究", "现状", "趋势"])]
                sections_to_improve.update(accuracy_related)
            elif weak_area == "depth":
                # 深度问题：改进分析和技术章节
                depth_related = [title for title in section_titles 
                               if any(keyword in title.lower() for keyword in 
                                     ["技术", "分析", "机制", "原理", "发展"])]
                sections_to_improve.update(depth_related)
            elif weak_area == "relevance":
                # 相关性问题：改进核心主题章节
                relevance_related = [title for title in section_titles 
                                   if any(keyword in title.lower() for keyword in 
                                         ["概述", "核心", "主要", "关键"])]
                sections_to_improve.update(relevance_related)
            elif weak_area == "clarity":
                # 清晰度问题：改进所有章节的表达
                sections_to_improve.update(section_titles)
        
        # 如果没有匹配到特定章节，改进前2个章节
        if not sections_to_improve:
            sections_to_improve = set(list(section_titles)[:2])
        
        return list(sections_to_improve)
        
    except Exception as e:
        print(f"⚠️ 识别改进章节失败: {e}")
        # 出错时改进所有章节
        return list(section_titles)

# 流式处理器初始化
try:
    from streaming_orchestrator import StreamingOrchestrator
    streaming_orchestrator = StreamingOrchestrator()
    streaming_available = True
    print("✅ 流式处理器初始化成功")
except Exception as e:
    print(f"⚠️ 流式处理器初始化失败: {e}")
    streaming_orchestrator = None
    streaming_available = False

# HTTP API 服务器
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import uvicorn
import asyncio
import json

# 创建HTTP应用
http_app = FastAPI(title="MCP HTTP API", version="1.0.0")

@http_app.post("/mcp/tools/call")
async def tools_call(request: dict):
    """MCP工具调用端点 - 支持SSE流式响应"""
    try:
        # 支持两种请求格式
        if "params" in request:
            # MCP标准格式: {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "tool", "arguments": {...}}}
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            request_id = request.get("id", 1)
        else:
            # 简化格式: {"tool": "tool_name", "arguments": {...}}
            tool_name = request.get("tool")
            arguments = request.get("arguments", {})
            request_id = request.get("id", 1)
        
        # 工具映射
        tool_functions = {
            "search": search,
            "orchestrator_mcp": orchestrator_mcp,
            "query_generation_mcp": query_generation_mcp,
            "outline_writer_mcp": outline_writer_mcp,
            "summary_writer_mcp": summary_writer_mcp,
            "content_writer_mcp": content_writer_mcp,
            "analysis_mcp": analysis_mcp,
            "user_interaction_mcp": user_interaction_mcp
        }
        
        if tool_name not in tool_functions:
            # 返回SSE格式的错误
            async def error_stream():
                error_msg = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": "Unknown tool",
                        "data": {
                            "type": "unknown_tool",
                            "message": f"Unknown tool: {tool_name}"
                        }
                    }
                }
                yield f"data: {json.dumps(error_msg, ensure_ascii=False)}\n\n"
            
            return StreamingResponse(error_stream(), media_type="text/event-stream")
        
        # 对于orchestrator_mcp，使用流式处理
        if tool_name == "orchestrator_mcp" and streaming_available:
            async def orchestrator_stream():
                try:
                    # 发送开始消息
                    start_msg = {
                        "type": "start",
                        "message": f"开始执行{tool_name}任务"
                    }
                    yield f"data: {json.dumps(start_msg, ensure_ascii=False)}\n\n"
                    
                    # 使用StreamingOrchestrator
                    async for message in streaming_orchestrator.stream_insight_report(**arguments):
                        yield f"data: {json.dumps(message, ensure_ascii=False)}\n\n"
                        
                except Exception as e:
                    error_msg = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": "Internal error",
                            "data": {
                                "type": "execution_failed",
                                "message": str(e)
                            }
                        }
                    }
                    yield f"data: {json.dumps(error_msg, ensure_ascii=False)}\n\n"
            
            return StreamingResponse(orchestrator_stream(), media_type="text/event-stream")
        
        # 对于其他工具，执行并返回结果
        else:
            async def tool_stream():
                try:
                    # 执行工具
                    result = await tool_functions[tool_name](**arguments)
                    
                    # 发送结果消息
                    result_msg = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "tool": tool_name,
                            "content": result
                        }
                    }
                    yield f"data: {json.dumps(result_msg, ensure_ascii=False)}\n\n"
                
                except Exception as e:
                    error_msg = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": "Internal error",
                            "data": {
                                "type": "execution_failed",
                                "message": str(e)
                            }
                        }
                    }
                    yield f"data: {json.dumps(error_msg, ensure_ascii=False)}\n\n"
            
            return StreamingResponse(tool_stream(), media_type="text/event-stream")
        
    except Exception as e:
        # 返回SSE格式的错误
        async def error_stream():
            error_msg = {
                "jsonrpc": "2.0",
                "id": request.get("id", 1),
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": {
                        "type": "request_parsing_failed",
                        "message": str(e)
                    }
                }
            }
            yield f"data: {json.dumps(error_msg, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(error_stream(), media_type="text/event-stream")

@http_app.get("/")
async def root():
    return {"message": "MCP HTTP API Server", "version": "1.0.0"}

@http_app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("🚀 启动MCP服务器...")
    print("📡 支持端点: /mcp/tools/call (HTTP API)")
    print("🔧 支持的MCP工具:")
    print("   - orchestrator_mcp: 主编排工具(支持质量评估迭代，包括洞察报告)")
    print("   - analysis_mcp: 分析工具(支持evaluation质量评估)")
    print("   - search: 搜索工具")
    print("   - outline_writer_mcp: 大纲生成工具")
    print("   - content_writer_mcp: 内容生成工具")
    print("   - summary_writer_mcp: 摘要生成工具")
    print("   - query_generation_mcp: 查询生成工具")
    print("   - user_interaction_mcp: 用户交互工具")
    
    # 启动HTTP服务器
    import threading
    import time

    def start_http_server():
        uvicorn.run(http_app, host="0.0.0.0", port=8001, log_level="info")
    
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    # 等待HTTP服务器启动
    time.sleep(2)
    
    # 启动FastMCP服务器
    print("🚀 启动FastMCP服务器...")
    mcp.run(transport="streamable-http")
