#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP工具模块
集中管理所有MCP工具函数，提供统一的工具接口
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# 导入配置和核心模块
from config_manager import config_manager
from search_manager import SearchEngineManager, SearchQueryGenerator
from streaming import StreamingProgressReporter, session_manager, task_detector

# 导入分析和生成组件
from collectors.analysis_mcp import AnalysisMcp
from collectors.outline_writer_mcp import OutlineWriterMcp
from collectors.summary_writer_mcp import SummaryWriterMcp
from collectors.detailed_content_writer_mcp import DetailedContentWriterMcp
from collectors.query_generation_mcp import QueryGenerationMcp
from collectors.user_interaction_mcp import UserInteractionMcp
from collectors.search_mcp import SearchMcp
from collectors.master_mcp import MasterMcp
from collectors.llm_processor import LLMProcessor

# 全局变量
search_engine_manager = None

# 全局工具注册表实例（延迟初始化）
tool_registry = None


class MCPToolRegistry:
    """MCP工具注册表"""
    
    def __init__(self, search_manager: SearchEngineManager = None):
        self.tools = {}
        self.tool_descriptions = {}
        self.search_manager = search_manager
        # 设置全局变量供函数使用
        global search_engine_manager
        search_engine_manager = search_manager
        
    def initialize_components(self):
        """初始化组件"""
        # 搜索组件已在SearchEngineManager构造函数中初始化
        self._register_all_tools()
    
    def _register_all_tools(self):
        """注册所有MCP工具"""
        # 搜索相关工具
        self.register_tool("comprehensive_search", comprehensive_search, "执行全面的多引擎搜索")
        self.register_tool("parallel_search", parallel_search, "执行并行针对性搜索")
        self.register_tool("query_generation_mcp", query_generation_mcp_tool, "生成智能搜索查询")
        
        # 分析和生成工具
        self.register_tool("analysis_mcp", analysis_mcp_tool, "分析报告质量和内容")
        self.register_tool("outline_writer_mcp", outline_writer_mcp, "生成报告大纲")
        self.register_tool("summary_writer_mcp", summary_writer_mcp, "生成内容摘要")
        self.register_tool("content_writer_mcp", content_writer_mcp, "生成详细内容")
        
        # 编排工具
        self.register_tool("orchestrator_mcp_streaming", orchestrator_mcp_streaming, "流式报告生成编排")
        self.register_tool("orchestrator_mcp_simple", orchestrator_mcp_simple, "简化报告生成编排")
        self.register_tool("orchestrator_mcp", orchestrator_mcp, "完整报告生成编排")
        self.register_tool("master_mcp", master_mcp_tool, "主控MCP任务执行")
        
        # 交互工具
        self.register_tool("user_interaction_mcp", user_interaction_mcp_tool, "用户交互和反馈收集")
    
    def register_tool(self, name: str, func: callable, description: str):
        """注册工具"""
        self.tools[name] = func
        self.tool_descriptions[name] = description
    
    def get_tool(self, name: str) -> Optional[callable]:
        """获取工具函数"""
        return self.tools.get(name)
    
    def list_tools(self) -> Dict[str, str]:
        """列出所有工具"""
        return self.tool_descriptions.copy()
    
    def execute_tool(self, name: str, **kwargs) -> Any:
        """执行工具"""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"工具 '{name}' 不存在")
        
        try:
            return tool(**kwargs)
        except Exception as e:
            error_msg = f"执行工具 '{name}' 时发生错误: {str(e)}"
            print(f"❌ {error_msg}")
            raise
    
    def register_tools(self, mcp_server):
        """注册工具到MCP服务器"""
        for name, func in self.tools.items():
            mcp_server.tool()(func)


# 初始化组件
analysis_mcp = AnalysisMcp()
outline_writer = OutlineWriterMcp()
summary_writer = SummaryWriterMcp()
content_writer = DetailedContentWriterMcp()
query_generation_mcp = QueryGenerationMcp()
user_interaction_mcp = UserInteractionMcp()
search_mcp = SearchMcp()
master_mcp = MasterMcp()
# LLMProcessor将在需要时动态创建，以便传递reporter参数
query_generator = SearchQueryGenerator()

def initialize_tools():
    """初始化所有工具和管理器"""
    global search_engine_manager, tool_registry
    
    # 1. 初始化搜索引擎管理器
    if search_engine_manager is None:
        search_engine_manager = SearchEngineManager()
        print("✅ 搜索引擎管理器初始化完成")

    # 2. 初始化工具注册表
    if tool_registry is None:
        tool_registry = MCPToolRegistry(search_manager=search_engine_manager)
        tool_registry.initialize_components()
        print("✅ MCP工具注册表初始化完成")



def comprehensive_search(
    topic: str,
    days: int = 7,
    max_results: int = 5,
    session_id: str = None
) -> Dict[str, Any]:
    """执行全面的多引擎搜索"""
    reporter = StreamingProgressReporter(session_id)
    
    try:
        reporter.report_progress("started", f"开始全面搜索: {topic}")
        
        # 尝试并行搜索
        if search_engine_manager and hasattr(search_engine_manager, 'parallel_data_collector') and search_engine_manager.parallel_data_collector:
            reporter.report_progress("searching", "使用多引擎并行搜索", progress_percentage=20)
            
            try:
                results = search_engine_manager.parallel_data_collector.parallel_comprehensive_search(
                    topic=topic,
                    days=days,
                    max_workers=3
                )
                
                if results and results.get('total_count', 0) > 0:
                    reporter.report_progress("completed", f"并行搜索完成，获得 {results['total_count']} 个结果", progress_percentage=100)
                    return {
                        "search_results": results,
                        "search_method": "parallel_multi_engine",
                        "engines_used": search_engine_manager.get_available_engines(),
                        "session_id": reporter.session_id
                    }
            except Exception as e:
                reporter.report_progress("warning", f"并行搜索失败，切换到单引擎模式: {str(e)}", progress_percentage=30)
        
        # 降级到单引擎搜索
        reporter.report_progress("searching", "使用单引擎搜索模式", progress_percentage=40)
        
        if not search_engine_manager:
            raise Exception("搜索引擎管理器未初始化")
            
        available_engines = search_engine_manager.get_available_engines()
        if not available_engines:
            raise Exception("没有可用的搜索引擎")
        
        # 使用第一个可用引擎
        engine_name = available_engines[0]
        engine = getattr(search_engine_manager, f"{engine_name.lower()}_collector", None)
        
        if not engine:
            raise Exception(f"搜索引擎 {engine_name} 不可用")
        
        reporter.report_progress("searching", f"使用 {engine_name} 引擎搜索", progress_percentage=60)
        
        # 执行搜索
        if hasattr(engine, 'search_news'):
            results = engine.search_news(topic, days=days, max_results=max_results)
        else:
            results = engine.search(topic, max_results=max_results)
        
        reporter.report_progress("completed", f"单引擎搜索完成，获得 {len(results) if isinstance(results, list) else 'N/A'} 个结果", progress_percentage=100)
        
        return {
            "search_results": results,
            "search_method": "single_engine",
            "engine_used": engine_name,
            "session_id": reporter.session_id
        }
        
    except Exception as e:
        error_msg = f"搜索过程中发生错误: {str(e)}"
        reporter.report_error(error_msg)
        return {
            "error": error_msg,
            "search_method": "failed",
            "session_id": reporter.session_id
        }


def parallel_search(
    topic: str,
    search_queries: List[str] = None,
    days: int = 7,
    max_results: int = 3,
    session_id: str = None
) -> Dict[str, Any]:
    """执行并行针对性搜索"""
    reporter = StreamingProgressReporter(session_id)
    
    try:
        reporter.report_progress("started", f"开始并行搜索: {topic}")
        
        # 生成搜索查询（如果未提供）
        if not search_queries:
            reporter.report_progress("generating", "生成智能搜索查询", progress_percentage=10)
            try:
                query_result = query_generator.generate_intelligent_queries(topic)
                search_queries = query_result.get('queries', [topic])
            except Exception as e:
                reporter.report_progress("warning", f"查询生成失败，使用默认查询: {str(e)}")
                search_queries = [topic]
        
        reporter.report_progress("searching", f"使用 {len(search_queries)} 个查询进行并行搜索", progress_percentage=30)
        
        # 尝试并行搜索
        if search_engine_manager.parallel_data_collector:
            try:
                results = search_engine_manager.parallel_data_collector.parallel_targeted_search(
                    queries=search_queries,
                    topic=topic,
                    max_workers=3
                )
                
                if results and results.get('针对性搜索结果'):
                    reporter.report_progress("completed", f"并行搜索完成，获得 {len(results['针对性搜索结果'])} 个结果", progress_percentage=100)
                    return {
                        "search_results": results,
                        "search_method": "parallel_targeted",
                        "queries_used": search_queries,
                        "engines_used": search_engine_manager.get_available_engines(),
                        "session_id": reporter.session_id
                    }
            except Exception as e:
                reporter.report_progress("warning", f"并行搜索失败，切换到单引擎模式: {str(e)}", progress_percentage=50)
        
        # 降级到单引擎搜索
        reporter.report_progress("searching", "使用单引擎搜索模式", progress_percentage=60)
        
        available_engines = search_engine_manager.get_available_engines()
        if not available_engines:
            raise Exception("没有可用的搜索引擎")
        
        engine_name = available_engines[0]
        engine = getattr(search_engine_manager, f"{engine_name.lower()}_collector", None)
        
        if not engine:
            raise Exception(f"搜索引擎 {engine_name} 不可用")
        
        # 对每个查询执行搜索
        all_results = []
        for i, query in enumerate(search_queries):
            reporter.report_progress("searching", f"搜索查询 {i+1}/{len(search_queries)}: {query}", progress_percentage=60 + (30 * i / len(search_queries)))
            
            try:
                if hasattr(engine, 'search_news'):
                    query_results = engine.search_news(query, days=days, max_results=max_results)
                else:
                    query_results = engine.search(query, max_results=max_results)
                
                if isinstance(query_results, list):
                    all_results.extend(query_results)
                elif isinstance(query_results, dict) and 'results' in query_results:
                    all_results.extend(query_results['results'])
            except Exception as e:
                reporter.report_progress("warning", f"查询 '{query}' 搜索失败: {str(e)}")
        
        reporter.report_progress("completed", f"单引擎搜索完成，获得 {len(all_results)} 个结果", progress_percentage=100)
        
        return {
            "search_results": all_results,
            "search_method": "single_engine_multiple_queries",
            "queries_used": search_queries,
            "engine_used": engine_name,
            "session_id": reporter.session_id
        }
        
    except Exception as e:
        error_msg = f"并行搜索过程中发生错误: {str(e)}"
        reporter.report_error(error_msg)
        return {
            "error": error_msg,
            "search_method": "failed",
            "session_id": reporter.session_id
        }


def query_generation_mcp_tool(topic: str, strategy: str = "initial", context: str = "", **kwargs) -> Dict:
    """
    生成搜索查询
    
    Args:
        topic: 主题
        strategy: 策略 (initial, iterative, targeted)
        context: 上下文信息
    
    Returns:
        Dict: 查询生成结果
    """
    try:
        queries = query_generation_mcp.generate_queries(
            topic=topic,
            strategy=strategy,
            context=context,
            **kwargs
        )
        return {
            "success": True,
            "queries": queries,
            "strategy": strategy,
            "topic": topic
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "queries": []
        }


def query_generation_mcp(
    topic: str,
    num_queries: int = 5,
    session_id: str = None
) -> Dict[str, Any]:
    """生成智能搜索查询"""
    reporter = StreamingProgressReporter(session_id)
    
    try:
        reporter.report_progress("started", f"开始生成搜索查询: {topic}")
        
        result = query_generator.generate_intelligent_queries(
            topic=topic,
            num_queries=num_queries
        )
        
        reporter.report_progress("completed", f"成功生成 {len(result.get('queries', []))} 个搜索查询", progress_percentage=100)
        
        return {
            "queries": result.get('queries', []),
            "generation_method": result.get('method', 'unknown'),
            "session_id": reporter.session_id
        }
        
    except Exception as e:
        error_msg = f"查询生成过程中发生错误: {str(e)}"
        reporter.report_error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "session_id": reporter.session_id
        }


def outline_writer_mcp(
    topic: str,
    search_results: List[Dict] = None,
    session_id: str = None,
    days: int = 7,
    **kwargs
) -> Dict[str, Any]:
    """生成报告大纲"""
    # 使用传递进来的reporter，如果没有则创建新的
    reporter = kwargs.get('reporter', StreamingProgressReporter(session_id))
    
    try:
        reporter.report_progress("started", f"开始生成大纲: {topic}")
        
        # 如果没有提供搜索结果，先执行搜索
        if not search_results:
            reporter.report_progress("searching", "获取相关信息", progress_percentage=20)
            search_result = comprehensive_search(topic, days=days, session_id=session_id)
            search_results = search_result.get('search_results', [])
        
        reporter.report_progress("generating", "生成报告大纲", progress_percentage=60)
        
        # 确保reference_data是正确的格式
        reference_data = []
        if isinstance(search_results, dict):
            # 如果是字典，提取实际的搜索结果
            if '针对性搜索结果' in search_results:
                reference_data = search_results['针对性搜索结果']
            elif 'search_results' in search_results:
                reference_data = search_results['search_results']
            else:
                # 尝试从字典中提取列表数据
                for key, value in search_results.items():
                    if isinstance(value, list):
                        reference_data = value
                        break
        elif isinstance(search_results, list):
            reference_data = search_results
        
        outline = outline_writer.create_outline(
            topic=topic,
            report_type="comprehensive",
            reference_data=reference_data
        )
        
        reporter.report_progress("completed", "大纲生成完成", progress_percentage=100)
        
        # 将 OutlineNode 对象转换为字典格式以支持 JSON 序列化
        outline_dict = outline.to_dict() if hasattr(outline, 'to_dict') else outline
        
        return {
            "outline": outline_dict,
            "topic": topic,
            "session_id": reporter.session_id
        }
        
    except Exception as e:
        error_msg = f"大纲生成过程中发生错误: {str(e)}"
        reporter.report_error(error_msg)
        return {
            "error": error_msg,
            "session_id": reporter.session_id
        }


def summary_writer_mcp(
    content: str,
    max_length: int = 500,
    session_id: str = None
) -> Dict[str, Any]:
    """生成内容摘要"""
    reporter = StreamingProgressReporter(session_id)
    
    try:
        reporter.report_progress("started", "开始生成摘要")
        
        summary = summary_writer.write_summary(
            content_data=content,
            length_constraint=f"{max_length}字",
            format="paragraph"
        )
        
        reporter.report_progress("completed", "摘要生成完成", progress_percentage=100)
        
        return {
            "summary": summary,
            "original_length": len(content),
            "summary_length": len(summary),
            "session_id": reporter.session_id
        }
        
    except Exception as e:
        error_msg = f"摘要生成过程中发生错误: {str(e)}"
        reporter.report_error(error_msg)
        return {
            "error": error_msg,
            "session_id": reporter.session_id
        }


def content_writer_mcp(
    topic: str,
    outline: Dict = None,
    search_results: List[Dict] = None,
    session_id: str = None,
    content_style: str = "enhanced",  # 新增：内容风格选择
    min_word_count: int = 30000,      # 更新：提高最小字数要求至30000
    max_sections: int = 10,           # 新增：最大章节数
    **kwargs
) -> Dict[str, Any]:
    """生成详细内容
    
    Args:
        topic: 主题
        outline: 大纲（可选，如果不提供会自动生成）
        search_results: 搜索结果（可选，如果不提供会自动搜索）
        session_id: 会话ID
        content_style: 内容风格 ("enhanced" 使用增强模式, "original" 使用原始模式)
        min_word_count: 最小字数要求（默认30000字符）
        max_sections: 最大章节数
    """
    # 使用传递进来的reporter，如果没有则创建新的
    reporter = kwargs.get('reporter', StreamingProgressReporter(session_id))
    
    # 创建带有reporter的LLMProcessor实例
    llm_processor = LLMProcessor(reporter=reporter)
    
    # 创建带有reporter的DetailedContentWriterMcp实例
    content_writer_with_reporter = DetailedContentWriterMcp(llm_processor=llm_processor)
    
    try:
        reporter.report_progress("started", f"开始生成内容: {topic} (风格: {content_style})")
        
        # 如果没有提供搜索结果，先执行搜索
        if not search_results:
            reporter.report_progress("searching", "获取相关信息", progress_percentage=20)
            search_result = comprehensive_search(topic, max_results=15, session_id=session_id)  # 增加搜索结果数量
            search_results = search_result.get('search_results', [])
        
        reporter.report_progress("writing", f"生成详细内容 (目标字数: {min_word_count}+)", progress_percentage=40)
        
        # 准备内容数据
        content_data = []
        if search_results:
            # 导入Document类
            from collectors.search_mcp import Document
            
            for result in search_results:
                if isinstance(result, dict):
                    # 将字典转换为Document对象
                    doc = Document(
                        title=result.get('title', '未知标题'),
                        content=result.get('content', result.get('snippet', '')),
                        url=result.get('url', result.get('link', '')),
                        published_date=result.get('published_date', result.get('date', '')),
                        source=result.get('source', '未知来源')
                    )
                    content_data.append(doc)
                else:
                    content_data.append(result)
        
        # 使用新的增强生成方法
        if content_style == "enhanced":
            # 调用新的集成方法生成完整报告
            try:
                # 直接使用同步方法，避免协程问题
                content = content_writer_with_reporter.generate_full_report_sync(topic, content_data)
            except AttributeError:
                # 如果没有同步方法，使用异步方法但在新线程中运行
                try:
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        def run_async():
                            return asyncio.run(content_writer_with_reporter.generate_full_report(topic, content_data))
                        future = executor.submit(run_async)
                        content = future.result(timeout=300)  # 5分钟超时
                except Exception as async_error:
                    # 如果异步调用失败，回退到同步方法
                    reporter.report_progress("warning", f"异步调用失败，回退到同步方法: {str(async_error)}")
                    from collectors.detailed_content_writer_mcp import ContentWritingConfig
                    config = ContentWritingConfig(
                        writing_style="professional",
                        target_audience="行业专家和决策者",
                        tone="objective",
                        depth_level="detailed",
                        include_examples=True,
                        include_citations=True,
                        max_section_length=16000,
                        min_section_length=8000
                    )
                    content = content_writer_with_reporter.write_section_content(
                        section_title=topic,
                        content_data=content_data,
                        overall_report_context=f"关于{topic}的详细行业洞察报告",
                        config=config
                    )
            except Exception as e:
                # 最终回退方案
                reporter.report_progress("warning", f"增强模式失败，使用基础模式: {str(e)}")
                from collectors.detailed_content_writer_mcp import ContentWritingConfig
                config = ContentWritingConfig(
                    writing_style="professional",
                    target_audience="行业专家和决策者",
                    tone="objective",
                    depth_level="detailed",
                    include_examples=True,
                    include_citations=True,
                    max_section_length=16000,
                    min_section_length=8000
                )
                content = content_writer_with_reporter.write_section_content(
                    section_title=topic,
                    content_data=content_data,
                    overall_report_context=f"关于{topic}的详细行业洞察报告",
                    config=config
                )
        else:
            # 使用原始的生成方法（作为备选）
            from collectors.detailed_content_writer_mcp import ContentWritingConfig
            config = ContentWritingConfig(
                writing_style="professional",
                target_audience="行业专家和决策者",
                tone="objective",
                depth_level="detailed",
                include_examples=True,
                include_citations=True,
                max_section_length=16000,
                min_section_length=8000
            )
            content = content_writer_with_reporter.write_section_content(
                section_title=topic,
                content_data=content_data,
                overall_report_context=f"关于{topic}的详细行业洞察报告",
                config=config
            )
        
        # 内容质量检查
        content_length = len(content.replace(' ', '').replace('\n', ''))
        quality_score = "高" if content_length >= min_word_count else "中" if content_length >= min_word_count // 2 else "低"
        
        reporter.report_progress("completed", f"内容生成完成 (字数: {content_length}, 质量: {quality_score})", progress_percentage=100)
        
        return {
            "success": True,
            "content": content,
            "topic": topic,
            "content_length": content_length,
            "quality_score": quality_score,
            "content_style": content_style,
            "data_sources_count": len(content_data),
            "session_id": reporter.session_id
        }
        
    except Exception as e:
        error_msg = f"内容生成过程中发生错误: {str(e)}"
        reporter.report_error(error_msg)
        return {
            "error": error_msg,
            "session_id": reporter.session_id
        }


def orchestrator_mcp_streaming(
    topic: str,
    report_type: str = "comprehensive",
    session_id: str = None,
    days: int = 30,
    **kwargs
) -> Dict[str, Any]:
    """流式报告生成编排 - 增强错误处理和恢复能力"""
    if not session_id:
        session_id = session_manager.create_session(topic, task_detector.detect_task_type(topic))
    
    # 使用传递进来的reporter，如果没有则创建新的
    reporter = kwargs.get('reporter', StreamingProgressReporter(session_id))
    
    # 初始化结果容器
    search_results = []
    outline = {}
    content = ""
    summary = ""
    errors = []
    
    try:
        reporter.report_progress("started", f"开始流式生成报告: {topic}")
        
        # 步骤1: 搜索信息 - 增强错误恢复
        reporter.report_progress("searching", "收集相关信息", progress_percentage=10)
        try:
            search_result = comprehensive_search(topic, session_id=session_id)
            
            if 'error' in search_result:
                errors.append(f"搜索警告: {search_result['error']}")
                reporter.report_progress("warning", f"搜索遇到问题，尝试备用方案: {search_result['error']}")
                
                # 备用搜索方案
                try:
                    backup_search = parallel_search(topic, days=days, session_id=session_id)
                    if 'error' not in backup_search:
                        search_results = backup_search.get('search_results', [])
                        reporter.report_progress("info", "备用搜索方案成功")
                    else:
                        search_results = []
                        errors.append("备用搜索也失败")
                except Exception as backup_e:
                    search_results = []
                    errors.append(f"备用搜索异常: {str(backup_e)}")
            else:
                search_results = search_result.get('search_results', [])
                
        except Exception as search_e:
            errors.append(f"搜索异常: {str(search_e)}")
            reporter.report_progress("warning", f"搜索步骤失败，将使用空结果继续: {str(search_e)}")
            search_results = []
        
        # 步骤2: 生成大纲 - 增强错误恢复
        reporter.report_progress("outlining", "生成报告大纲", progress_percentage=30)
        try:
            outline_result = outline_writer_mcp(topic, search_results, session_id, reporter=reporter)
            
            if 'error' in outline_result:
                errors.append(f"大纲生成警告: {outline_result['error']}")
                reporter.report_progress("warning", f"大纲生成遇到问题，使用默认结构: {outline_result['error']}")
                
                # 使用默认大纲结构
                outline = {
                    "1": "背景介绍",
                    "2": "主要内容",
                    "3": "分析总结",
                    "4": "结论建议"
                }
            else:
                outline = outline_result.get('outline', {})
                
        except Exception as outline_e:
            errors.append(f"大纲生成异常: {str(outline_e)}")
            reporter.report_progress("warning", f"大纲生成失败，使用默认结构: {str(outline_e)}")
            outline = {
                "1": "背景介绍",
                "2": "主要内容", 
                "3": "分析总结",
                "4": "结论建议"
            }
        
        # 步骤3: 生成内容 - 增强错误恢复
        reporter.report_progress("writing", "生成详细内容", progress_percentage=60)
        try:
            content_result = content_writer_mcp(topic, outline, search_results, session_id, reporter=reporter)
            
            if 'error' in content_result:
                errors.append(f"内容生成警告: {content_result['error']}")
                reporter.report_progress("warning", f"内容生成遇到问题，生成简化版本: {content_result['error']}")
                
                # 生成简化内容
                content = f"# {topic}\n\n基于可用信息生成的简化报告内容。\n\n"
                if search_results:
                    content += "## 相关信息\n\n"
                    for i, result in enumerate(search_results[:3], 1):
                        content += f"{i}. {result.get('title', '无标题')}\n{result.get('content', '无内容')[:200]}...\n\n"
                else:
                    content += "由于搜索结果有限，无法提供详细分析。"
            else:
                content = content_result.get('content', "")
                
        except Exception as content_e:
            errors.append(f"内容生成异常: {str(content_e)}")
            reporter.report_progress("warning", f"内容生成失败，生成基础版本: {str(content_e)}")
            content = f"# {topic}\n\n由于技术问题，无法生成详细内容。请稍后重试。"
        
        # 步骤4: 生成摘要 - 非关键步骤，失败不影响整体
        reporter.report_progress("summarizing", "生成报告摘要", progress_percentage=80)
        try:
            summary_result = summary_writer_mcp(content, session_id=session_id)
            
            if 'error' in summary_result:
                errors.append(f"摘要生成警告: {summary_result['error']}")
                reporter.report_progress("warning", f"摘要生成失败: {summary_result['error']}")
                summary = "摘要生成失败，请查看详细内容"
            else:
                summary = summary_result.get('summary', "")
                
        except Exception as summary_e:
            errors.append(f"摘要生成异常: {str(summary_e)}")
            reporter.report_progress("warning", f"摘要生成异常: {str(summary_e)}")
            summary = "摘要生成异常，请查看详细内容"
        
        # 完成报告 - 即使有部分错误也生成报告
        final_report = {
            "topic": topic,
            "report_type": report_type,
            "summary": summary,
            "outline": outline,
            "content": content,
            "search_results": search_results,
            "generated_at": datetime.now().isoformat(),
            "session_id": session_id,
            "errors": errors,  # 包含所有警告和错误信息
            "status": "completed_with_warnings" if errors else "completed"
        }
        
        # 保存报告到本地文件
        try:
            import os
            # 创建报告目录（使用绝对路径）
            current_dir = os.path.dirname(os.path.abspath(__file__))
            reports_dir = os.path.join(current_dir, "reports")
            os.makedirs(reports_dir, exist_ok=True)
            
            # 生成文件名
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip()
            # 确保主题不为空，如果为空则使用默认名称
            if not safe_topic:
                safe_topic = "report"
            filename = f"{safe_topic}_{report_type}_{date_str}.md"
            filepath = os.path.join(reports_dir, filename)
            
            # 组装完整的Markdown报告内容
            full_report_content = f"""# {topic}

## 报告摘要

{summary}

## 报告大纲

"""
            
            # 添加大纲内容
            if isinstance(outline, dict):
                for key, value in outline.items():
                    full_report_content += f"{key}. {value}\n"
            else:
                full_report_content += str(outline)
            
            full_report_content += f"\n\n## 详细内容\n\n{content}\n\n"
            
            # 添加生成信息
            full_report_content += f"""## 生成信息

- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **报告类型**: {report_type}
- **搜索结果数量**: {len(search_results)}
- **会话ID**: {session_id}
"""
            
            if errors:
                full_report_content += f"\n- **警告信息**: {len(errors)} 个警告\n"
                for i, error in enumerate(errors, 1):
                    full_report_content += f"  {i}. {error}\n"
            
            # 保存文件，确保正确处理中文字符
            with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                # 清理可能导致编码问题的字符
                clean_content = full_report_content.encode('utf-8', errors='ignore').decode('utf-8')
                f.write(clean_content)
            
            # 验证文件是否真的保存了
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                final_report["output_path"] = filepath
                reporter.report_progress("file_saved", f"报告已保存到: {filepath} (大小: {file_size} 字节)")
            else:
                error_msg = f"文件保存验证失败: {filepath}"
                errors.append(error_msg)
                reporter.report_progress("warning", error_msg)
            
        except Exception as save_e:
            error_msg = f"保存报告文件失败: {str(save_e)}"
            errors.append(error_msg)
            reporter.report_progress("warning", error_msg)
            final_report["errors"] = errors
        
        if errors:
            reporter.report_progress("completed_with_warnings", f"报告生成完成，但有 {len(errors)} 个警告", progress_percentage=100)
        else:
            reporter.report_progress("completed", "流式报告生成完成", progress_percentage=100)
            
        session_manager.complete_session(session_id, final_report)
        
        return final_report
        
    except Exception as e:
        # 最后的异常处理 - 尝试生成最小可用报告
        error_msg = f"流式报告生成过程中发生严重错误: {str(e)}"
        reporter.report_error(error_msg)
        
        # 尝试生成最小报告
        minimal_report = {
            "topic": topic,
            "report_type": report_type,
            "summary": "由于系统错误，无法生成完整摘要",
            "outline": {"1": "系统错误", "2": "请稍后重试"},
            "content": f"# {topic}\n\n系统遇到错误，无法生成完整报告。\n\n错误信息: {str(e)}",
            "search_results": search_results,  # 使用已收集的搜索结果
            "generated_at": datetime.now().isoformat(),
            "session_id": session_id,
            "errors": errors + [error_msg],
            "status": "failed_with_partial_results"
        }
        
        session_manager.error_session(session_id, {"message": error_msg, "timestamp": datetime.now().isoformat()})
        
        return minimal_report


def orchestrator_mcp_simple(
    topic: str,
    session_id: str = None
) -> Dict[str, Any]:
    """简化报告生成编排"""
    reporter = StreamingProgressReporter(session_id)
    
    try:
        reporter.report_progress("started", f"开始简化报告生成: {topic}")
        
        # 只执行搜索和内容生成
        search_result = comprehensive_search(topic, session_id=session_id)
        
        if 'error' in search_result:
            raise Exception(f"搜索失败: {search_result['error']}")
        
        reporter.report_progress("completed", "简化报告生成完成", progress_percentage=100)
        
        return {
            "topic": topic,
            "search_results": search_result.get('search_results', []),
            "generated_at": datetime.now().isoformat(),
            "session_id": reporter.session_id
        }
        
    except Exception as e:
        error_msg = f"简化报告生成过程中发生错误: {str(e)}"
        reporter.report_error(error_msg)
        return {
            "error": error_msg,
            "session_id": reporter.session_id
        }


def orchestrator_mcp(
    topic: str,
    report_type: str = "comprehensive",
    include_analysis: bool = True,
    session_id: str = None,
    days: int = 30,
    **kwargs
) -> Dict[str, Any]:
    """完整报告生成编排"""
    reporter = StreamingProgressReporter(session_id)
    
    try:
        reporter.report_progress("started", f"开始完整报告生成: {topic}")
        
        # 使用流式编排作为基础
        result = orchestrator_mcp_streaming(topic, report_type, session_id, days, **kwargs)
        
        if 'error' in result:
            return result
        
        # 如果需要分析，添加分析步骤
        if include_analysis:
            reporter.report_progress("analyzing", "执行深度分析", progress_percentage=90)
            
            try:
                # 获取完整报告内容进行质量分析
                search_results = result.get('search_results', [])
                content = result.get('content', '')
                summary = result.get('summary', '')
                outline = result.get('outline', {})
                
                # 为final_report模式准备完整报告内容
                report_content = f"""报告摘要：
{summary}

报告大纲：
{str(outline)}

报告内容：
{content}"""
                
                # 计算报告长度和章节数
                report_length = len(report_content)
                section_count = len(outline.get('sections', [])) if isinstance(outline, dict) else 1
                
                analysis_result = analysis_mcp.analyze_quality(
                    data=search_results,
                    topic=topic,
                    evaluation_mode="final_report",
                    report_content=report_content,
                    report_type=report_type,
                    report_length=report_length,
                    section_count=section_count
                )
                # 将 AnalysisResult 对象转换为字典格式以支持 JSON 序列化
                analysis_dict = analysis_result.to_dict() if hasattr(analysis_result, 'to_dict') else analysis_result
                result['analysis'] = analysis_dict
            except Exception as e:
                reporter.report_progress("warning", f"分析步骤失败: {str(e)}")
                result['analysis'] = {"error": str(e)}
        
        reporter.report_progress("completed", "完整报告生成完成", progress_percentage=100)
        
        return result
        
    except Exception as e:
        error_msg = f"完整报告生成过程中发生错误: {str(e)}"
        reporter.report_error(error_msg)
        return {
            "error": error_msg,
            "session_id": reporter.session_id
        }


def analysis_mcp_tool(
    data: List[Dict] = None,
    topic: str = None,
    evaluation_mode: str = "data_quality",
    report_content: str = None,
    report_type: str = "comprehensive",
    report_length: int = None,
    section_count: int = None,
    session_id: str = None
) -> Dict[str, Any]:
    """分析报告质量和内容"""
    reporter = StreamingProgressReporter(session_id)
    
    try:
        reporter.report_progress("started", f"开始分析: {topic or '数据质量'}")
        
        # 调用分析组件
        analysis_result = analysis_mcp.analyze_quality(
            data=data or [],
            topic=topic or "未指定主题",
            evaluation_mode=evaluation_mode,
            report_content=report_content,
            report_type=report_type,
            report_length=report_length,
            section_count=section_count
        )
        
        # 将 AnalysisResult 对象转换为字典格式
        analysis_dict = analysis_result.to_dict() if hasattr(analysis_result, 'to_dict') else analysis_result
        
        reporter.report_progress("completed", "分析完成", progress_percentage=100)
        
        return {
            "analysis": analysis_dict,
            "topic": topic,
            "evaluation_mode": evaluation_mode,
            "session_id": reporter.session_id
        }
        
    except Exception as e:
        error_msg = f"分析过程中发生错误: {str(e)}"
        reporter.report_error(error_msg)
        return {
            "error": error_msg,
            "session_id": reporter.session_id
        }


def master_mcp_tool(user_query: str, task_type: str = None, requirements: str = "", **kwargs) -> Dict:
    """
    主控MCP任务执行
    
    Args:
        user_query: 用户查询
        task_type: 任务类型
        requirements: 需求描述
    
    Returns:
        Dict: 任务执行结果
    """
    try:
        from collectors.master_mcp import TaskConfig, TaskType
        
        # 如果指定了任务类型，创建任务配置
        if task_type:
            try:
                task_config = TaskConfig(
                    task_type=TaskType(task_type),
                    topic=user_query,
                    requirements=requirements,
                    **kwargs
                )
            except ValueError:
                # 如果任务类型无效，让 MasterMcp 自动识别
                task_config = None
        else:
            task_config = None
        
        result = master_mcp.execute_task(user_query, task_config)
        
        return {
            "success": result.success,
            "task_type": result.task_type.value,
            "topic": result.topic,
            "output_content": result.output_content,
            "output_path": result.output_path,
            "quality_score": result.quality_score,
            "execution_time": result.execution_time,
            "metadata": result.metadata or {}
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "task_type": task_type or "unknown",
            "topic": user_query
        }


def user_interaction_mcp_tool(interaction_type: str, prompt: str, options: List[str] = None, **kwargs) -> Dict:
    """
    用户交互和反馈收集
    
    Args:
        interaction_type: 交互类型 (choice, input, confirmation, rating)
        prompt: 提示信息
        options: 选项列表
    
    Returns:
        Dict: 交互结果
    """
    try:
        if interaction_type == "choice":
            result = user_interaction_mcp.get_user_choice(prompt, options, **kwargs)
        elif interaction_type == "input":
            result = user_interaction_mcp.get_user_input(prompt, **kwargs)
        elif interaction_type == "confirmation":
            result = user_interaction_mcp.get_confirmation(prompt, **kwargs)
        elif interaction_type == "rating":
            result = user_interaction_mcp.get_rating(prompt, **kwargs)
        else:
            result = user_interaction_mcp.get_user_input(prompt, **kwargs)
        
        return {
            "success": True,
            "result": result,
            "interaction_type": interaction_type
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "result": None
        }


def user_interaction_mcp(
    user_input: str,
    context: Dict = None,
    session_id: str = None
) -> Dict[str, Any]:
    """用户交互处理"""
    reporter = StreamingProgressReporter(session_id)
    
    try:
        reporter.report_progress("started", "处理用户交互")
        
        # 检测用户意图
        task_type = task_detector.detect_task_type(user_input)
        
        # 根据任务类型选择合适的处理方式
        if task_type in ['market_report', 'news_report', 'research_report', 'insight_report', 'comprehensive_report']:
            result = orchestrator_mcp_streaming(user_input, task_type, session_id)
        elif task_type in ['news_search', 'academic_search', 'web_search']:
            result = comprehensive_search(user_input, session_id=session_id)
        elif task_type == 'analysis':
            if context and 'content' in context:
                result = analysis_mcp.analyze_content(context['content'], user_input)
            else:
                result = {"error": "分析任务需要提供内容"}
        elif task_type == 'summarization':
            if context and 'content' in context:
                result = summary_writer_mcp(context['content'], session_id=session_id)
            else:
                result = {"error": "摘要任务需要提供内容"}
        else:
            # 默认处理：尝试搜索
            result = comprehensive_search(user_input, session_id=session_id)
        
        reporter.report_progress("completed", "用户交互处理完成", progress_percentage=100)
        
        return {
            "user_input": user_input,
            "detected_task_type": task_type,
            "result": result,
            "session_id": reporter.session_id
        }
        
    except Exception as e:
        error_msg = f"用户交互处理过程中发生错误: {str(e)}"
        reporter.report_error(error_msg)
        return {
            "error": error_msg,
            "user_input": user_input,
            "session_id": reporter.session_id
        }


# 创建全局工具注册表
def get_tool_registry(search_manager: SearchEngineManager = None) -> MCPToolRegistry:
    """获取或创建工具注册表实例"""
    global tool_registry
    if tool_registry is None:
        tool_registry = MCPToolRegistry(search_manager)
        # 总是初始化组件，即使没有search_manager
        tool_registry.initialize_components()
    return tool_registry


if __name__ == "__main__":
    # 测试模块
    print("\n🔧 MCP工具模块状态报告:")
    test_registry = get_tool_registry()
    tools = test_registry.list_tools()
    for name, description in tools.items():
        print(f"   ✅ {name}: {description}")
    print(f"\n📊 总计: {len(tools)} 个MCP工具")
else:
    print("✅ MCP工具模块初始化完成")