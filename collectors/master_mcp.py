import json
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import time
from datetime import datetime

# 导入所有MCP组件
from collectors.search_mcp_old import SearchMcp, Document
from collectors.query_generation_mcp import QueryGenerationMcp
from collectors.analysis_mcp import AnalysisMcp, AnalysisResult
from collectors.summary_writer_mcp import SummaryWriterMcp, SummaryConfig
from collectors.outline_writer_mcp import OutlineWriterMcp, OutlineNode
from collectors.detailed_content_writer_mcp import DetailedContentWriterMcp, ContentWritingConfig
from collectors.user_interaction_mcp import UserInteractionMcp
from collectors.llm_processor import LLMProcessor


class TaskType(Enum):
    """任务类型枚举"""
    INSIGHT_GENERATION = "insight_generation"      # 洞察生成
    RESEARCH_REPORT = "research_report"           # 研究报告
    NEWS_ANALYSIS = "news_analysis"               # 新闻分析
    MARKET_RESEARCH = "market_research"           # 市场研究
    ACADEMIC_REPORT = "academic_report"           # 学术报告
    BUSINESS_ANALYSIS = "business_analysis"       # 商业分析
    TECHNICAL_DOCUMENTATION = "technical_doc"     # 技术文档
    CONTENT_SUMMARIZATION = "summarization"       # 内容摘要
    DATA_ANALYSIS = "data_analysis"               # 数据分析
    CUSTOM_TASK = "custom_task"                   # 自定义任务


@dataclass
class TaskConfig:
    """任务配置"""
    task_type: TaskType
    topic: str
    requirements: str = ""
    output_format: str = "markdown"
    quality_threshold: float = 0.7
    enable_user_interaction: bool = True
    max_search_iterations: int = 3
    custom_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_params is None:
            self.custom_params = {}


@dataclass
class TaskResult:
    """任务结果"""
    task_type: TaskType
    topic: str
    success: bool
    output_content: str
    output_path: str = ""
    metadata: Dict[str, Any] = None
    execution_time: float = 0.0
    quality_score: float = 0.0
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MasterMcp:
    """
    主控MCP (Master Model Context Protocol)
    
    用途：统一管理和调度所有MCP组件，根据用户意图自动选择和调用相应的子MCP。
    
    职责：
    - 理解用户意图并映射到具体任务类型
    - 自动选择和调用相应的MCP组件
    - 管理整个工作流程和数据流
    - 提供统一的入口点和结果输出
    - 处理错误和异常情况
    
    输入：用户查询、任务配置
    输出：完整的任务结果
    """
    
    def __init__(self, enable_user_interaction: bool = True):
        """初始化MasterMcp和所有子MCP组件"""
        print("🚀 初始化MasterMcp统一管理系统...")
        
        # 初始化所有子MCP组件
        self.search_mcp = SearchMcp()
        self.query_mcp = QueryGenerationMcp()
        self.analysis_mcp = AnalysisMcp()
        self.summary_mcp = SummaryWriterMcp()
        self.outline_mcp = OutlineWriterMcp()
        self.content_mcp = DetailedContentWriterMcp()
        
        # 用户交互组件（可选）
        if enable_user_interaction:
            self.interaction_mcp = UserInteractionMcp(interface_type="cli")
        else:
            self.interaction_mcp = None
        
        # LLM处理器用于意图理解
        try:
            self.llm_processor = LLMProcessor()
            self.has_llm = True
        except:
            self.has_llm = False
            print("⚠️ LLM处理器初始化失败，将使用规则基础的意图识别")
        
        # 任务执行历史
        self.execution_history = []
        
        # 预定义的任务模板
        self.task_templates = self._load_task_templates()
        
        print("✅ MasterMcp初始化完成，所有子MCP组件就绪")
    
    def execute_task(self, user_query: str, task_config: TaskConfig = None) -> TaskResult:
        """
        执行任务的主入口
        
        Args:
            user_query: 用户查询
            task_config: 任务配置（可选，会自动推断）
            
        Returns:
            TaskResult: 任务执行结果
        """
        start_time = time.time()
        
        try:
            print(f"\n🎯 MasterMcp开始执行任务")
            print(f"用户查询: {user_query}")
            print("=" * 60)
            
            # 步骤1: 理解用户意图
            if task_config is None:
                task_config = self._understand_user_intent(user_query)
            
            print(f"📋 识别任务类型: {task_config.task_type.value}")
            print(f"📋 提取主题: {task_config.topic}")
            
            # 步骤2: 执行具体任务
            result = self._execute_specific_task(task_config)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            # 记录执行历史
            self.execution_history.append({
                "timestamp": datetime.now().isoformat(),
                "user_query": user_query,
                "task_config": task_config,
                "result": result,
                "execution_time": execution_time
            })
            
            print(f"\n✅ 任务执行完成！")
            print(f"⏱️ 执行时间: {execution_time:.2f}秒")
            print(f"📊 质量评分: {result.quality_score:.2f}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ 任务执行失败: {str(e)}")
            
            return TaskResult(
                task_type=task_config.task_type if task_config else TaskType.CUSTOM_TASK,
                topic=task_config.topic if task_config else "未知主题",
                success=False,
                output_content=f"任务执行失败: {str(e)}",
                execution_time=execution_time
            )
    
    def _understand_user_intent(self, user_query: str) -> TaskConfig:
        """理解用户意图并生成任务配置"""
        print("\n🧠 分析用户意图...")
        
        # 使用LLM进行意图理解
        if self.has_llm:
            return self._llm_intent_understanding(user_query)
        else:
            return self._rule_based_intent_understanding(user_query)
    
    def _llm_intent_understanding(self, user_query: str) -> TaskConfig:
        """使用LLM理解用户意图"""
        prompt = f"""
请分析以下用户查询，识别任务类型、主题和要求：

用户查询: "{user_query}"

可用任务类型：
1. insight_generation - 洞察生成（分析趋势、发现模式、提供见解）
2. research_report - 研究报告（全面的研究分析报告）
3. news_analysis - 新闻分析（分析最新新闻和事件）
4. market_research - 市场研究（市场分析和竞争研究）
5. academic_report - 学术报告（学术研究和论文）
6. business_analysis - 商业分析（商业策略和决策分析）
7. technical_doc - 技术文档（技术说明和文档）
8. summarization - 内容摘要（总结和摘要生成）
9. data_analysis - 数据分析（数据处理和分析）
10. custom_task - 自定义任务（其他特殊需求）

请按以下JSON格式输出：
```json
{{
    "task_type": "选择的任务类型",
    "topic": "提取的主题",
    "requirements": "具体要求和偏好",
    "output_format": "markdown",
    "quality_threshold": 0.7,
    "reasoning": "选择理由"
}}
```
"""
        
        try:
            response = self.llm_processor.call_llm_api_json(
                prompt,
                "你是一位专业的任务分析专家，擅长理解用户需求并将其转化为具体的任务配置。"
            )
            
            if isinstance(response, dict):
                task_type_str = response.get("task_type", "custom_task")
                task_type = TaskType(task_type_str) if task_type_str in [t.value for t in TaskType] else TaskType.CUSTOM_TASK
                
                config = TaskConfig(
                    task_type=task_type,
                    topic=response.get("topic", "未指定主题"),
                    requirements=response.get("requirements", ""),
                    output_format=response.get("output_format", "markdown"),
                    quality_threshold=response.get("quality_threshold", 0.7)
                )
                
                print(f"💡 LLM分析结果: {response.get('reasoning', '无推理说明')}")
                return config
            else:
                raise ValueError("LLM返回格式不正确")
                
        except Exception as e:
            print(f"⚠️ LLM意图理解失败: {str(e)}，使用规则基础方法")
            return self._rule_based_intent_understanding(user_query)
    
    def _rule_based_intent_understanding(self, user_query: str) -> TaskConfig:
        """基于规则的意图理解"""
        query_lower = user_query.lower()
        
        # 关键词映射
        intent_keywords = {
            TaskType.INSIGHT_GENERATION: ["洞察", "insights", "趋势", "分析", "发现", "模式", "见解"],
            TaskType.RESEARCH_REPORT: ["研究报告", "research", "调研", "全面分析", "深入研究"],
            TaskType.NEWS_ANALYSIS: ["新闻", "news", "最新", "事件", "时事", "动态"],
            TaskType.MARKET_RESEARCH: ["市场", "market", "竞争", "行业", "商业模式"],
            TaskType.ACADEMIC_REPORT: ["学术", "academic", "论文", "理论", "研究方法"],
            TaskType.BUSINESS_ANALYSIS: ["商业", "business", "策略", "决策", "经营"],
            TaskType.TECHNICAL_DOCUMENTATION: ["技术", "技术文档", "technical", "开发", "实现"],
            TaskType.CONTENT_SUMMARIZATION: ["摘要", "总结", "summary", "概括"],
            TaskType.DATA_ANALYSIS: ["数据", "data", "统计", "分析数据"]
        }
        
        # 匹配任务类型
        best_match = TaskType.CUSTOM_TASK
        max_matches = 0
        
        for task_type, keywords in intent_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in query_lower)
            if matches > max_matches:
                max_matches = matches
                best_match = task_type
        
        # 提取主题（简单实现）
        topic = self._extract_topic_from_query(user_query)
        
        return TaskConfig(
            task_type=best_match,
            topic=topic,
            requirements=user_query
        )
    
    def _extract_topic_from_query(self, user_query: str) -> str:
        """从查询中提取主题"""
        # 移除常见的任务词汇，保留主题词汇
        stop_words = [
            "生成", "分析", "报告", "研究", "写", "创建", "制作", "总结", 
            "帮我", "给我", "我想", "请", "能否", "可以", "如何"
        ]
        
        words = user_query.split()
        topic_words = [word for word in words if word not in stop_words and len(word) > 1]
        
        if topic_words:
            return " ".join(topic_words[:5])  # 取前5个词作为主题
        else:
            return "未指定主题"
    
    def _execute_specific_task(self, task_config: TaskConfig) -> TaskResult:
        """执行具体任务"""
        task_type = task_config.task_type
        
        # 根据任务类型调用相应的处理方法
        task_handlers = {
            TaskType.INSIGHT_GENERATION: self._handle_insight_generation,
            TaskType.RESEARCH_REPORT: self._handle_research_report,
            TaskType.NEWS_ANALYSIS: self._handle_news_analysis,
            TaskType.MARKET_RESEARCH: self._handle_market_research,
            TaskType.ACADEMIC_REPORT: self._handle_academic_report,
            TaskType.BUSINESS_ANALYSIS: self._handle_business_analysis,
            TaskType.TECHNICAL_DOCUMENTATION: self._handle_technical_documentation,
            TaskType.CONTENT_SUMMARIZATION: self._handle_content_summarization,
            TaskType.DATA_ANALYSIS: self._handle_data_analysis,
            TaskType.CUSTOM_TASK: self._handle_custom_task
        }
        
        handler = task_handlers.get(task_type, self._handle_custom_task)
        return handler(task_config)
    
    def _handle_insight_generation(self, task_config: TaskConfig) -> TaskResult:
        """处理洞察生成任务"""
        print("\n🔍 执行洞察生成任务...")
        
        # 1. 生成多角度查询
        print("📝 生成多角度搜索查询...")
        queries = self.query_mcp.generate_multi_strategy_queries(
            topic=task_config.topic,
            strategies=["initial", "news", "academic"],
            context="为洞察生成收集多维度信息"
        )
        
        all_queries = []
        for strategy_queries in queries.values():
            all_queries.extend(strategy_queries)
        
        # 2. 执行并行搜索
        print("🔍 执行并行搜索...")
        search_results = self.search_mcp.parallel_search(
            queries=all_queries[:10],  # 限制查询数量
            max_results_per_query=5,
            days_back=30,
            max_workers=4
        )
        
        # 3. 数据质量分析
        print("📊 分析数据质量...")
        quality_analysis = self.analysis_mcp.analyze_quality(
            data=search_results,
            topic=task_config.topic
        )
        
        # 4. 如果质量不足，进行补充搜索
        if quality_analysis.score < task_config.quality_threshold:
            print("🔄 数据质量不足，执行补充搜索...")
            gap_analysis = self.analysis_mcp.analyze_gaps(
                topic=task_config.topic,
                existing_data=search_results
            )
            
            # 生成补充查询
            additional_queries = self.query_mcp.generate_queries(
                topic=task_config.topic,
                strategy="iterative",
                context=f"质量评分: {quality_analysis.score}, 需要补充信息"
            )
            
            additional_results = self.search_mcp.parallel_search(
                queries=additional_queries,
                max_results_per_query=3,
                days_back=30
            )
            
            search_results.extend(additional_results)
        
        # 5. 生成洞察内容
        print("💡 生成洞察分析...")
        
        # 创建洞察报告大纲
        outline = self.outline_mcp.create_outline(
            topic=task_config.topic,
            report_type="comprehensive",
            user_requirements=f"重点关注洞察和趋势分析。{task_config.requirements}",
            reference_data=search_results[:5]
        )
        
        # 生成各章节内容，重点关注洞察
        writing_config = ContentWritingConfig(
            writing_style="analytical",
            target_audience="决策者和分析师",
            tone="analytical",
            depth_level="detailed",
            include_examples=True,
            include_citations=True
        )
        
        sections_for_writing = []
        for section in outline.subsections:
            sections_for_writing.append({
                "title": section.title,
                "content_data": search_results[:8]  # 为每个章节提供相同的数据池
            })
        
        section_contents = self.content_mcp.write_multiple_sections(
            sections=sections_for_writing,
            overall_context=f"关于{task_config.topic}的洞察分析报告，重点发现趋势和模式",
            config=writing_config
        )
        
        # 6. 生成执行摘要（洞察总结）
        print("📄 生成洞察摘要...")
        insight_summary = self.summary_mcp.write_summary(
            content_data=list(section_contents.values()),
            length_constraint="400-500字",
            format="executive",
            target_audience="决策者",
            focus_areas=["关键洞察", "趋势分析", "战略建议"]
        )
        
        # 7. 组装最终报告
        final_content = self._assemble_insight_report(
            task_config=task_config,
            insight_summary=insight_summary,
            outline=outline,
            section_contents=section_contents,
            quality_score=quality_analysis.score,
            data_sources=len(search_results)
        )
        
        # 8. 保存报告
        output_path = self._save_report(
            final_content, 
            task_config.topic, 
            "insight_analysis"
        )
        
        return TaskResult(
            task_type=TaskType.INSIGHT_GENERATION,
            topic=task_config.topic,
            success=True,
            output_content=final_content,
            output_path=output_path,
            quality_score=quality_analysis.score,
            metadata={
                "data_sources": len(search_results),
                "sections_generated": len(section_contents),
                "queries_used": len(all_queries)
            }
        )
    
    def _handle_research_report(self, task_config: TaskConfig) -> TaskResult:
        """处理研究报告任务"""
        print("\n📚 执行研究报告任务...")
        
        # 使用学术导向的方法
        queries = self.query_mcp.generate_queries(
            topic=task_config.topic,
            strategy="academic",
            context="为学术研究报告收集权威信息"
        )
        
        search_results = self.search_mcp.parallel_search(
            queries=queries,
            max_results_per_query=6,
            days_back=90,  # 更长的时间范围
            max_workers=4
        )
        
        outline = self.outline_mcp.create_outline(
            topic=task_config.topic,
            report_type="academic",
            user_requirements=task_config.requirements
        )
        
        writing_config = ContentWritingConfig(
            writing_style="academic",
            target_audience="研究人员",
            tone="objective",
            depth_level="detailed",
            include_citations=True
        )
        
        # 继续执行类似的流程...
        return self._generate_standard_report(task_config, "research_report", queries, outline, writing_config)
    
    def _handle_news_analysis(self, task_config: TaskConfig) -> TaskResult:
        """处理新闻分析任务"""
        print("\n📰 执行新闻分析任务...")
        
        # 使用新闻导向的查询
        queries = self.query_mcp.generate_queries(
            topic=task_config.topic,
            strategy="news",
            context="分析最新新闻和事件"
        )
        
        search_results = self.search_mcp.parallel_search(
            queries=queries,
            max_results_per_query=5,
            days_back=7,  # 最近一周的新闻
            max_workers=4
        )
        
        # 新闻分析特定的大纲
        outline = self.outline_mcp.create_outline(
            topic=task_config.topic,
            report_type="comprehensive",
            user_requirements=f"重点分析新闻事件和影响。{task_config.requirements}"
        )
        
        writing_config = ContentWritingConfig(
            writing_style="professional",
            target_audience="公众和决策者",
            tone="objective",
            include_examples=True
        )
        
        return self._generate_standard_report(task_config, "news_analysis", queries, outline, writing_config)
    
    def _generate_standard_report(self, task_config: TaskConfig, report_suffix: str, 
                                 queries: List[str], outline: OutlineNode, 
                                 writing_config: ContentWritingConfig) -> TaskResult:
        """生成标准报告的通用方法"""
        
        # 搜索数据
        search_results = self.search_mcp.parallel_search(
            queries=queries,
            max_results_per_query=5,
            days_back=30,
            max_workers=4
        )
        
        # 质量分析
        quality_analysis = self.analysis_mcp.analyze_quality(
            data=search_results,
            topic=task_config.topic
        )
        
        # 生成内容
        sections_for_writing = []
        for section in outline.subsections:
            sections_for_writing.append({
                "title": section.title,
                "content_data": search_results[:6]
            })
        
        section_contents = self.content_mcp.write_multiple_sections(
            sections=sections_for_writing,
            overall_context=f"关于{task_config.topic}的{report_suffix}报告",
            config=writing_config
        )
        
        # 生成摘要
        summary = self.summary_mcp.write_summary(
            content_data=list(section_contents.values()),
            length_constraint="300-400字",
            format="executive"
        )
        
        # 组装报告
        final_content = self._assemble_standard_report(
            task_config, summary, outline, section_contents, 
            quality_analysis.score, len(search_results)
        )
        
        # 保存报告
        output_path = self._save_report(final_content, task_config.topic, report_suffix)
        
        return TaskResult(
            task_type=task_config.task_type,
            topic=task_config.topic,
            success=True,
            output_content=final_content,
            output_path=output_path,
            quality_score=quality_analysis.score,
            metadata={
                "data_sources": len(search_results),
                "sections_generated": len(section_contents)
            }
        )
    
    # 其他任务处理方法的简化实现
    def _handle_market_research(self, task_config: TaskConfig) -> TaskResult:
        return self._generate_standard_report(
            task_config, "market_research",
            self.query_mcp.generate_queries(task_config.topic, "initial"),
            self.outline_mcp.create_outline(task_config.topic, "business"),
            ContentWritingConfig(writing_style="business")
        )
    
    def _handle_academic_report(self, task_config: TaskConfig) -> TaskResult:
        return self._generate_standard_report(
            task_config, "academic_report",
            self.query_mcp.generate_queries(task_config.topic, "academic"),
            self.outline_mcp.create_outline(task_config.topic, "academic"),
            ContentWritingConfig(writing_style="academic")
        )
    
    def _handle_business_analysis(self, task_config: TaskConfig) -> TaskResult:
        return self._generate_standard_report(
            task_config, "business_analysis",
            self.query_mcp.generate_queries(task_config.topic, "initial"),
            self.outline_mcp.create_outline(task_config.topic, "business"),
            ContentWritingConfig(writing_style="business")
        )
    
    def _handle_technical_documentation(self, task_config: TaskConfig) -> TaskResult:
        return self._generate_standard_report(
            task_config, "technical_doc",
            self.query_mcp.generate_queries(task_config.topic, "initial"),
            self.outline_mcp.create_outline(task_config.topic, "technical"),
            ContentWritingConfig(writing_style="technical")
        )
    
    def _handle_content_summarization(self, task_config: TaskConfig) -> TaskResult:
        """处理内容摘要任务"""
        print("\n📄 执行内容摘要任务...")
        
        # 为摘要任务搜索相关内容
        queries = self.query_mcp.generate_queries(task_config.topic, "initial")
        search_results = self.search_mcp.parallel_search(queries, max_results_per_query=10)
        
        # 生成多层次摘要
        summaries = self.summary_mcp.write_multi_level_summary(
            content_data=search_results,
            levels=["executive", "detailed", "bullet_points"]
        )
        
        # 组装摘要报告
        final_content = f"# {task_config.topic} - 内容摘要\n\n"
        final_content += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for level, content in summaries.items():
            final_content += f"## {level.replace('_', ' ').title()}摘要\n\n{content}\n\n"
        
        output_path = self._save_report(final_content, task_config.topic, "summary")
        
        return TaskResult(
            task_type=TaskType.CONTENT_SUMMARIZATION,
            topic=task_config.topic,
            success=True,
            output_content=final_content,
            output_path=output_path,
            metadata={"summary_levels": list(summaries.keys())}
        )
    
    def _handle_data_analysis(self, task_config: TaskConfig) -> TaskResult:
        """处理数据分析任务"""
        print("\n📊 执行数据分析任务...")
        
        # 搜索相关数据和分析
        queries = self.query_mcp.generate_queries(
            task_config.topic, "initial", 
            context="收集数据分析相关信息"
        )
        search_results = self.search_mcp.parallel_search(queries)
        
        # 分析数据质量和相关性
        analysis_results = []
        for result in search_results[:5]:
            relevance = self.analysis_mcp.analyze_relevance(result, task_config.topic)
            analysis_results.append(relevance)
        
        # 生成分析报告
        final_content = f"# {task_config.topic} - 数据分析报告\n\n"
        final_content += "## 数据质量分析\n\n"
        
        for i, analysis in enumerate(analysis_results):
            final_content += f"### 数据源 {i+1}\n"
            final_content += f"- 相关性评分: {analysis.score:.2f}\n"
            final_content += f"- 分析结果: {analysis.reasoning}\n\n"
        
        output_path = self._save_report(final_content, task_config.topic, "data_analysis")
        
        return TaskResult(
            task_type=TaskType.DATA_ANALYSIS,
            topic=task_config.topic,
            success=True,
            output_content=final_content,
            output_path=output_path
        )
    
    def _handle_custom_task(self, task_config: TaskConfig) -> TaskResult:
        """处理自定义任务"""
        print("\n🔧 执行自定义任务...")
        
        # 用户交互获取更多信息
        if self.interaction_mcp:
            task_details = self.interaction_mcp.get_user_input(
                "请描述您希望执行的具体任务:",
                required=True
            )
            task_config.requirements += f" {task_details}"
        
        # 使用通用方法处理
        return self._generate_standard_report(
            task_config, "custom_task",
            self.query_mcp.generate_queries(task_config.topic, "initial"),
            self.outline_mcp.create_outline(task_config.topic, "comprehensive"),
            ContentWritingConfig()
        )
    
    def _assemble_insight_report(self, task_config: TaskConfig, insight_summary: str,
                                outline: OutlineNode, section_contents: Dict[str, str],
                                quality_score: float, data_sources: int) -> str:
        """组装洞察报告"""
        report_parts = []
        
        # 报告标题
        report_parts.append(f"# {task_config.topic} - 洞察分析报告\n")
        
        # 报告信息
        report_parts.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_parts.append(f"**数据质量评分**: {quality_score:.2f}")
        report_parts.append(f"**数据来源**: {data_sources}条")
        report_parts.append(f"**分析维度**: {len(section_contents)}个\n")
        
        # 核心洞察摘要
        report_parts.append("## 🔍 核心洞察摘要\n")
        report_parts.append(insight_summary)
        report_parts.append("\n")
        
        # 详细分析章节
        report_parts.append("## 📊 详细分析\n")
        for section in outline.subsections:
            section_title = section.title
            content = section_contents.get(section_title, "内容生成中...")
            
            report_parts.append(f"### {section_title}\n")
            report_parts.append(content)
            report_parts.append("\n")
        
        # 结论和建议
        report_parts.append("## 💡 结论与建议\n")
        report_parts.append("基于以上分析，我们识别出以下关键洞察和建议：\n")
        report_parts.append("1. **趋势洞察**: 从数据中识别的主要趋势\n")
        report_parts.append("2. **机会识别**: 发现的潜在机会和增长点\n") 
        report_parts.append("3. **风险预警**: 需要关注的潜在风险\n")
        report_parts.append("4. **行动建议**: 基于洞察的具体建议\n\n")
        
        report_parts.append("---\n")
        report_parts.append("*本报告由MasterMcp智能生成*")
        
        return '\n'.join(report_parts)
    
    def _assemble_standard_report(self, task_config: TaskConfig, summary: str,
                                 outline: OutlineNode, section_contents: Dict[str, str],
                                 quality_score: float, data_sources: int) -> str:
        """组装标准报告"""
        report_parts = []
        
        # 报告标题
        task_name = task_config.task_type.value.replace('_', ' ').title()
        report_parts.append(f"# {task_config.topic} - {task_name}\n")
        
        # 报告信息
        report_parts.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_parts.append(f"**数据质量**: {quality_score:.2f}")
        report_parts.append(f"**数据来源**: {data_sources}条\n")
        
        # 执行摘要
        report_parts.append("## 执行摘要\n")
        report_parts.append(summary)
        report_parts.append("\n")
        
        # 详细内容
        for section in outline.subsections:
            section_title = section.title
            content = section_contents.get(section_title, "内容生成中...")
            
            report_parts.append(f"## {section_title}\n")
            report_parts.append(content)
            report_parts.append("\n")
        
        report_parts.append("---\n")
        report_parts.append("*本报告由MasterMcp系统自动生成*")
        
        return '\n'.join(report_parts)
    
    def _save_report(self, content: str, topic: str, task_type: str) -> str:
        """保存报告文件"""
        import os
        from datetime import datetime
        
        # 创建报告目录
        os.makedirs("reports", exist_ok=True)
        
        # 生成文件名
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_topic}_{task_type}_{date_str}.md"
        filepath = os.path.join("reports", filename)
        
        # 保存文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def _load_task_templates(self) -> Dict[str, Dict]:
        """加载任务模板"""
        return {
            "insight_generation": {
                "description": "生成深度洞察分析",
                "default_config": {
                    "quality_threshold": 0.8,
                    "search_strategies": ["initial", "news", "academic"],
                    "analysis_focus": ["趋势", "模式", "机会", "风险"]
                }
            },
            "research_report": {
                "description": "生成全面研究报告",
                "default_config": {
                    "quality_threshold": 0.85,
                    "search_strategies": ["academic", "initial"],
                    "writing_style": "academic"
                }
            }
            # 可以继续添加其他模板...
        }
    
    def get_execution_history(self) -> List[Dict]:
        """获取执行历史"""
        return self.execution_history.copy()
    
    def get_available_task_types(self) -> List[str]:
        """获取可用的任务类型"""
        return [task_type.value for task_type in TaskType]