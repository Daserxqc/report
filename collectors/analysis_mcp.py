import json
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass, asdict
from pydantic import BaseModel
from collectors.llm_processor import LLMProcessor
from collectors.search_mcp_old import Document


@dataclass
class AnalysisResult:
    """分析结果数据结构"""
    analysis_type: str
    score: float
    details: Dict[str, Any]
    reasoning: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return asdict(self)


class QualityScore(BaseModel):
    """质量评分模型"""
    relevance: float        # 相关性 (0-1)
    credibility: float      # 可信度 (0-1)
    completeness: float     # 完整性 (0-1)
    timeliness: float       # 时效性 (0-1)
    overall: float          # 总体评分 (0-1)


class RelevanceAnalysis(BaseModel):
    """相关性分析模型"""
    relevance_score: float
    matching_keywords: List[str]
    topic_alignment: str
    content_quality: str


class IntentAnalysis(BaseModel):
    """意图分析模型"""
    primary_intent: str
    confidence: float
    secondary_intents: List[str]
    search_queries: List[str]
    recommended_sources: List[str]


class AnalysisMcp:
    """
    分析MCP (Model Context Protocol)
    
    用途：对文本或数据进行结构化的LLM分析。
    
    职责：
    - 评估搜索结果的质量（5维度评估）
    - 评估学术论文与主题的相关性
    - 理解用户查询的深层意图
    - 将非结构化文本（如大纲）解析为结构化JSON
    
    输入：data: list[Document] | str, prompt_template: str, output_schema: BaseModel
    输出：AnalysisResult
    
    实现要点：利用支持JSON模式输出的LLM API。为每个分析任务（质量、相关性、意图）创建专用的Prompt模板。
    """
    
    def __init__(self):
        """初始化AnalysisMcp"""
        try:
            self.llm_processor = LLMProcessor()
            self.has_llm = True
            print("✅ AnalysisMcp初始化完成")
        except Exception as e:
            print(f"⚠️ LLM处理器初始化失败: {str(e)}")
            self.has_llm = False
        
        # 预定义的分析模板
        self.analysis_templates = self._load_analysis_templates()
    
    def _load_analysis_templates(self) -> Dict[str, str]:
        """加载分析模板"""
        return {
            "quality_assessment": """
请对以下搜索结果进行5维度质量评估。

评估维度：
1. 相关性 (Relevance): 内容与主题"{topic}"的匹配程度
2. 可信度 (Credibility): 来源的权威性和内容的准确性
3. 完整性 (Completeness): 信息的全面性和深度
4. 时效性 (Timeliness): 信息的新鲜度和时间相关性
5. 总体质量 (Overall): 综合评估

搜索结果：
{content_data}

请为每个维度给出0-1的评分，并提供详细的分析理由。

输出格式：
```json
{{
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
}}
```
""",

            "relevance_analysis": """
请分析以下学术论文/内容与主题"{topic}"的相关性。

分析内容：
标题：{title}
摘要：{abstract}
作者：{authors}
发表时间：{publish_date}

请从以下方面进行分析：
1. 主题匹配程度
2. 关键词重叠
3. 研究领域一致性
4. 内容价值评估

输出格式：
```json
{{
    "relevance_score": 0.85,
    "matching_keywords": ["关键词1", "关键词2", "关键词3"],
    "topic_alignment": "高度相关/部分相关/弱相关/不相关",
    "content_quality": "优秀/良好/一般/较差",
    "detailed_analysis": {{
        "theme_match": "主题匹配分析",
        "keyword_analysis": "关键词分析",
        "research_value": "研究价值评估",
        "usage_recommendations": "使用建议"
    }}
}}
```
""",

            "intent_analysis": """
请分析用户查询的深层意图和需求。

用户查询："{user_query}"
查询上下文：{context}

请分析：
1. 用户的主要意图是什么？
2. 可能的次要意图有哪些？
3. 用户真正想了解的信息类型
4. 推荐的搜索策略和信息源

输出格式：
```json
{{
    "primary_intent": "主要意图描述",
    "confidence": 0.85,
    "secondary_intents": ["次要意图1", "次要意图2"],
    "information_needs": {{
        "factual_info": "是否需要事实信息",
        "analysis_info": "是否需要分析性信息",
        "procedural_info": "是否需要操作指导",
        "comparative_info": "是否需要比较信息"
    }},
    "search_queries": ["推荐查询1", "推荐查询2", "推荐查询3"],
    "recommended_sources": ["推荐信息源1", "推荐信息源2"],
    "urgency_level": "高/中/低"
}}
```
""",

            "structure_parsing": """
请将以下非结构化文本解析为结构化的JSON格式。

输入文本：
{input_text}

解析目标：{parsing_goal}
输出模式：{output_schema}

请仔细分析文本的层级结构、逻辑关系和关键信息，然后按照指定的模式输出结构化数据。

注意事项：
1. 保持原文的逻辑层次
2. 准确提取关键信息
3. 确保输出符合指定的JSON模式
4. 对于不确定的信息，标明不确定性

输出格式：严格按照提供的output_schema格式输出JSON数据。
""",

            "gap_analysis": """
请分析已有信息的覆盖情况，识别信息缺口。

主题：{topic}
已有信息：
{existing_data}

期望覆盖的方面：{expected_aspects}

请分析：
1. 已覆盖的信息领域
2. 明显的信息缺口
3. 信息质量不足的领域
4. 补充信息的优先级

输出格式：
```json
{{
    "coverage_analysis": {{
        "well_covered": ["已充分覆盖的方面1", "方面2"],
        "partially_covered": ["部分覆盖的方面1", "方面2"],
        "not_covered": ["未覆盖的方面1", "方面2"]
    }},
    "information_gaps": [
        {{
            "gap_type": "缺口类型",
            "description": "缺口描述",
            "priority": "高/中/低",
            "suggested_queries": ["建议查询1", "查询2"]
        }}
    ],
    "quality_issues": [
        {{
            "area": "质量问题领域",
            "issue": "具体问题",
            "improvement_suggestions": ["改进建议1", "建议2"]
        }}
    ]
}}
```
"""
        }

    def analyze_quality(self, 
                       data: Union[List[Document], List[Dict]], 
                       topic: str,
                       analysis_aspects: List[str] = None) -> AnalysisResult:
        """
        评估搜索结果的质量
        
        Args:
            data: 搜索结果数据
            topic: 分析主题
            analysis_aspects: 分析方面
            
        Returns:
            AnalysisResult: 质量分析结果
        """
        if not self.has_llm:
            return self._fallback_quality_analysis(data, topic)
        
        try:
            # 准备分析数据
            content_data = self._prepare_content_for_analysis(data)
            
            # 使用质量评估模板
            template = self.analysis_templates["quality_assessment"]
            prompt = template.format(
                topic=topic,
                content_data=content_data
            )
            
            # 调用LLM进行分析
            response = self.llm_processor.call_llm_api_json(
                prompt,
                "你是一位专业的信息质量评估专家，擅长从多个维度评估信息的质量和价值。"
            )
            
            # 解析结果
            if isinstance(response, dict):
                quality_score = QualityScore(
                    relevance=response.get("relevance", 0.5),
                    credibility=response.get("credibility", 0.5),
                    completeness=response.get("completeness", 0.5),
                    timeliness=response.get("timeliness", 0.5),
                    overall=response.get("overall", 0.5)
                )
                
                return AnalysisResult(
                    analysis_type="quality_assessment",
                    score=quality_score.overall,
                    details=response.get("analysis_details", {}),
                    reasoning=f"5维度质量评估：相关性{quality_score.relevance:.2f}, 可信度{quality_score.credibility:.2f}, 完整性{quality_score.completeness:.2f}, 时效性{quality_score.timeliness:.2f}",
                    metadata={"quality_score": quality_score.dict()}
                )
            else:
                raise ValueError("LLM返回格式不正确")
                
        except Exception as e:
            print(f"❌ 质量分析失败: {str(e)}")
            return self._fallback_quality_analysis(data, topic)
    
    def analyze_relevance(self, 
                         content: Union[Document, Dict], 
                         topic: str) -> AnalysisResult:
        """
        分析内容与主题的相关性
        
        Args:
            content: 内容数据
            topic: 主题
            
        Returns:
            AnalysisResult: 相关性分析结果
        """
        if not self.has_llm:
            return self._fallback_relevance_analysis(content, topic)
        
        try:
            # 提取内容信息
            if isinstance(content, Document):
                title = content.title
                abstract = content.content[:500] + "..." if len(content.content) > 500 else content.content
                authors = ", ".join(content.authors) if content.authors else "未知"
                publish_date = content.publish_date or "未知"
            else:
                title = content.get("title", "未知标题")
                abstract = content.get("content", content.get("abstract", ""))
                authors = ", ".join(content.get("authors", [])) if content.get("authors") else "未知"
                publish_date = content.get("publish_date", "未知")
            
            # 使用相关性分析模板
            template = self.analysis_templates["relevance_analysis"]
            prompt = template.format(
                topic=topic,
                title=title,
                abstract=abstract,
                authors=authors,
                publish_date=publish_date
            )
            
            # 调用LLM分析
            response = self.llm_processor.call_llm_api_json(
                prompt,
                "你是一位专业的内容相关性评估专家，擅长判断内容与主题的匹配程度。"
            )
            
            if isinstance(response, dict):
                relevance_score = response.get("relevance_score", 0.5)
                
                return AnalysisResult(
                    analysis_type="relevance_analysis",
                    score=relevance_score,
                    details=response.get("detailed_analysis", {}),
                    reasoning=f"相关性评分: {relevance_score:.2f}, 主题匹配: {response.get('topic_alignment', '未知')}",
                    metadata={
                        "matching_keywords": response.get("matching_keywords", []),
                        "content_quality": response.get("content_quality", "未评估")
                    }
                )
            else:
                raise ValueError("相关性分析返回格式不正确")
                
        except Exception as e:
            print(f"❌ 相关性分析失败: {str(e)}")
            return self._fallback_relevance_analysis(content, topic)
    
    def analyze_intent(self, 
                      user_query: str, 
                      context: str = "") -> AnalysisResult:
        """
        分析用户查询意图
        
        Args:
            user_query: 用户查询
            context: 查询上下文
            
        Returns:
            AnalysisResult: 意图分析结果
        """
        if not self.has_llm:
            return self._fallback_intent_analysis(user_query)
        
        try:
            # 使用意图分析模板
            template = self.analysis_templates["intent_analysis"]
            prompt = template.format(
                user_query=user_query,
                context=context
            )
            
            # 调用LLM分析
            response = self.llm_processor.call_llm_api_json(
                prompt,
                "你是一位专业的用户意图分析专家，擅长理解用户查询背后的真实需求。"
            )
            
            if isinstance(response, dict):
                confidence = response.get("confidence", 0.5)
                primary_intent = response.get("primary_intent", "信息查询")
                
                return AnalysisResult(
                    analysis_type="intent_analysis",
                    score=confidence,
                    details={
                        "primary_intent": primary_intent,
                        "secondary_intents": response.get("secondary_intents", []),
                        "information_needs": response.get("information_needs", {}),
                        "urgency_level": response.get("urgency_level", "中")
                    },
                    reasoning=f"主要意图: {primary_intent}, 置信度: {confidence:.2f}",
                    metadata={
                        "search_queries": response.get("search_queries", []),
                        "recommended_sources": response.get("recommended_sources", [])
                    }
                )
            else:
                raise ValueError("意图分析返回格式不正确")
                
        except Exception as e:
            print(f"❌ 意图分析失败: {str(e)}")
            return self._fallback_intent_analysis(user_query)
    
    def parse_structure(self, 
                       input_text: str, 
                       parsing_goal: str,
                       output_schema: Dict = None) -> AnalysisResult:
        """
        解析文本结构
        
        Args:
            input_text: 输入文本
            parsing_goal: 解析目标
            output_schema: 输出模式
            
        Returns:
            AnalysisResult: 结构解析结果
        """
        if not self.has_llm:
            return self._fallback_structure_parsing(input_text, parsing_goal)
        
        try:
            # 使用结构解析模板
            template = self.analysis_templates["structure_parsing"]
            prompt = template.format(
                input_text=input_text,
                parsing_goal=parsing_goal,
                output_schema=json.dumps(output_schema, ensure_ascii=False, indent=2) if output_schema else "通用JSON结构"
            )
            
            # 调用LLM解析
            response = self.llm_processor.call_llm_api_json(
                prompt,
                "你是一位专业的文本结构分析专家，擅长将非结构化文本转换为结构化数据。"
            )
            
            if isinstance(response, dict):
                return AnalysisResult(
                    analysis_type="structure_parsing",
                    score=1.0,  # 结构解析成功即为满分
                    details=response,
                    reasoning=f"成功解析文本结构，目标: {parsing_goal}",
                    metadata={"parsing_goal": parsing_goal}
                )
            else:
                raise ValueError("结构解析返回格式不正确")
                
        except Exception as e:
            print(f"❌ 结构解析失败: {str(e)}")
            return self._fallback_structure_parsing(input_text, parsing_goal)
    
    def analyze_gaps(self, 
                    topic: str,
                    existing_data: List[Union[Document, Dict]],
                    expected_aspects: List[str] = None) -> AnalysisResult:
        """
        分析信息缺口
        
        Args:
            topic: 主题
            existing_data: 已有数据
            expected_aspects: 期望覆盖的方面
            
        Returns:
            AnalysisResult: 缺口分析结果
        """
        if not self.has_llm:
            return self._fallback_gap_analysis(topic, existing_data)
        
        try:
            # 准备已有数据摘要
            data_summary = self._summarize_existing_data(existing_data)
            
            # 默认期望方面
            if expected_aspects is None:
                expected_aspects = [
                    "技术原理", "发展历史", "应用场景", "市场情况", 
                    "挑战问题", "未来趋势", "相关标准", "案例研究"
                ]
            
            # 使用缺口分析模板
            template = self.analysis_templates["gap_analysis"]
            prompt = template.format(
                topic=topic,
                existing_data=data_summary,
                expected_aspects=", ".join(expected_aspects)
            )
            
            # 调用LLM分析
            response = self.llm_processor.call_llm_api_json(
                prompt,
                "你是一位专业的信息分析专家，擅长识别信息覆盖的缺口和不足。"
            )
            
            if isinstance(response, dict):
                coverage = response.get("coverage_analysis", {})
                gaps = response.get("information_gaps", [])
                
                # 计算覆盖率作为评分
                well_covered = len(coverage.get("well_covered", []))
                total_aspects = len(expected_aspects)
                coverage_score = well_covered / total_aspects if total_aspects > 0 else 0
                
                return AnalysisResult(
                    analysis_type="gap_analysis",
                    score=coverage_score,
                    details=response,
                    reasoning=f"信息覆盖率: {coverage_score:.2f}, 发现{len(gaps)}个主要缺口",
                    metadata={
                        "total_aspects": total_aspects,
                        "well_covered_count": well_covered
                    }
                )
            else:
                raise ValueError("缺口分析返回格式不正确")
                
        except Exception as e:
            print(f"❌ 缺口分析失败: {str(e)}")
            return self._fallback_gap_analysis(topic, existing_data)
    
    def _prepare_content_for_analysis(self, data: Union[List[Document], List[Dict]]) -> str:
        """准备分析用的内容数据"""
        if not data:
            return "无数据"
        
        content_parts = []
        for i, item in enumerate(data[:5]):  # 限制分析前5个项目
            if isinstance(item, Document):
                content_parts.append(f"[{i+1}] 标题: {item.title}\n来源: {item.source} ({item.source_type})\n内容: {item.content[:200]}...")
            elif isinstance(item, dict):
                title = item.get("title", "未知标题")
                content = item.get("content", item.get("summary", ""))[:200]
                source = item.get("source", "未知来源")
                content_parts.append(f"[{i+1}] 标题: {title}\n来源: {source}\n内容: {content}...")
        
        return "\n\n".join(content_parts)
    
    def _summarize_existing_data(self, existing_data: List[Union[Document, Dict]]) -> str:
        """总结已有数据"""
        if not existing_data:
            return "无已有数据"
        
        # 统计数据来源和类型
        source_types = {}
        topics_mentioned = set()
        
        for item in existing_data:
            if isinstance(item, Document):
                source_type = item.source_type
                content = item.title + " " + item.content
            else:
                source_type = item.get("source_type", "unknown")
                content = item.get("title", "") + " " + item.get("content", "")
            
            source_types[source_type] = source_types.get(source_type, 0) + 1
            
            # 简单的主题提取
            for keyword in ["技术", "市场", "应用", "发展", "挑战", "趋势", "标准", "案例"]:
                if keyword in content:
                    topics_mentioned.add(keyword + "相关内容")
        
        summary = f"共{len(existing_data)}条数据，来源分布: {dict(source_types)}"
        if topics_mentioned:
            summary += f"，涵盖主题: {', '.join(list(topics_mentioned)[:5])}"
        
        return summary
    
    # 备用分析方法
    def _fallback_quality_analysis(self, data, topic) -> AnalysisResult:
        """备用质量分析"""
        if not data:
            score = 0.0
        else:
            # 简单的启发式评分
            score = min(0.5 + len(data) * 0.1, 1.0)
        
        return AnalysisResult(
            analysis_type="quality_assessment",
            score=score,
            details={"method": "fallback", "data_count": len(data) if data else 0},
            reasoning=f"备用质量评估，基于数据数量: {len(data) if data else 0}条"
        )
    
    def _fallback_relevance_analysis(self, content, topic) -> AnalysisResult:
        """备用相关性分析"""
        # 简单的关键词匹配
        if isinstance(content, Document):
            text = content.title + " " + content.content
        else:
            text = content.get("title", "") + " " + content.get("content", "")
        
        topic_words = topic.lower().split()
        text_lower = text.lower()
        
        matches = sum(1 for word in topic_words if word in text_lower)
        score = matches / len(topic_words) if topic_words else 0
        
        return AnalysisResult(
            analysis_type="relevance_analysis",
            score=score,
            details={"method": "keyword_matching", "matches": matches},
            reasoning=f"关键词匹配评分: {matches}/{len(topic_words)}"
        )
    
    def _fallback_intent_analysis(self, user_query) -> AnalysisResult:
        """备用意图分析"""
        # 简单的意图分类
        query_lower = user_query.lower()
        
        if any(word in query_lower for word in ["怎么", "如何", "方法"]):
            intent = "寻求操作指导"
        elif any(word in query_lower for word in ["什么", "介绍", "概念"]):
            intent = "寻求概念解释"
        elif any(word in query_lower for word in ["比较", "对比", "差异"]):
            intent = "寻求比较分析"
        else:
            intent = "一般信息查询"
        
        return AnalysisResult(
            analysis_type="intent_analysis",
            score=0.7,
            details={"primary_intent": intent, "method": "keyword_based"},
            reasoning=f"基于关键词的意图识别: {intent}"
        )
    
    def _fallback_structure_parsing(self, input_text, parsing_goal) -> AnalysisResult:
        """备用结构解析"""
        # 简单的行分割
        lines = [line.strip() for line in input_text.split('\n') if line.strip()]
        
        simple_structure = {
            "lines": lines,
            "line_count": len(lines),
            "parsing_goal": parsing_goal,
            "method": "simple_line_split"
        }
        
        return AnalysisResult(
            analysis_type="structure_parsing",
            score=0.5,
            details=simple_structure,
            reasoning=f"简单行分割解析，共{len(lines)}行"
        )
    
    def _fallback_gap_analysis(self, topic, existing_data) -> AnalysisResult:
        """备用缺口分析"""
        data_count = len(existing_data) if existing_data else 0
        
        # 简单的覆盖率估算
        if data_count >= 10:
            coverage_score = 0.8
            gaps = ["深度分析不足"]
        elif data_count >= 5:
            coverage_score = 0.6
            gaps = ["信息深度不足", "案例研究缺失"]
        else:
            coverage_score = 0.3
            gaps = ["基础信息不足", "多角度分析缺失", "案例和应用场景缺失"]
        
        return AnalysisResult(
            analysis_type="gap_analysis",
            score=coverage_score,
            details={"gaps": gaps, "data_count": data_count, "method": "simple_count_based"},
            reasoning=f"基于数据量的简单缺口分析，覆盖率: {coverage_score:.1f}"
        )