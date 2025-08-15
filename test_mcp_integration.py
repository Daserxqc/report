#!/usr/bin/env python3
"""
MCP组件集成测试和演示
展示SearchMcp、QueryGenerationMcp、AnalysisMcp、SummaryWriterMcp、OutlineWriterMcp、
DetailedContentWriterMcp、UserInteractionMcp的完整整合使用
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入所有MCP组件
from collectors.search_mcp import SearchMcp, Document
from collectors.query_generation_mcp import QueryGenerationMcp
from collectors.analysis_mcp import AnalysisMcp
from collectors.summary_writer_mcp import SummaryWriterMcp, SummaryConfig
from collectors.outline_writer_mcp import OutlineWriterMcp
from collectors.detailed_content_writer_mcp import DetailedContentWriterMcp, ContentWritingConfig
from collectors.user_interaction_mcp import UserInteractionMcp


class IntegratedReportGenerator:
    """
    整合的报告生成器
    演示六个MCP组件的协同工作
    """
    
    def __init__(self, enable_user_interaction: bool = True):
        """初始化所有MCP组件"""
        print("🚀 初始化MCP组件集成系统...")
        
        # 初始化所有MCP组件
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
        
        print("✅ 所有MCP组件初始化完成")
    
    def generate_comprehensive_report(self, topic: str, report_type: str = "comprehensive") -> str:
        """
        生成综合报告的完整流程
        
        Args:
            topic: 报告主题
            report_type: 报告类型
            
        Returns:
            str: 生成的报告路径
        """
        print(f"\n🎯 开始生成'{topic}'的{report_type}报告")
        print("=" * 60)
        
        # 步骤1: 生成初始搜索查询
        print("\n📝 步骤1: 生成搜索查询")
        initial_queries = self.query_mcp.generate_queries(
            topic=topic,
            strategy="initial",
            context=f"为{report_type}报告收集基础信息"
        )
        print(f"✅ 生成了{len(initial_queries)}个初始查询")
        
        # 步骤2: 执行并行搜索
        print("\n🔍 步骤2: 并行搜索收集数据")
        initial_search_results = self.search_mcp.parallel_search(
            queries=initial_queries,
            max_results_per_query=5,
            days_back=30,
            max_workers=4
        )
        print(f"✅ 收集到{len(initial_search_results)}条初始数据")
        
        # 步骤3: 分析数据质量和缺口
        print("\n📊 步骤3: 分析数据质量")
        quality_analysis = self.analysis_mcp.analyze_quality(
            data=initial_search_results,
            topic=topic
        )
        print(f"✅ 数据质量评分: {quality_analysis.score:.2f}")
        
        # 如果质量不够，生成补充查询
        if quality_analysis.score < 0.7:
            print("\n🔄 数据质量不足，生成补充查询")
            gap_analysis = self.analysis_mcp.analyze_gaps(
                topic=topic,
                existing_data=initial_search_results
            )
            
            # 生成迭代查询
            iterative_queries = self.query_mcp.generate_queries(
                topic=topic,
                strategy="iterative",
                context=f"质量评分: {quality_analysis.score}, 覆盖率: {gap_analysis.score}"
            )
            
            # 补充搜索
            additional_results = self.search_mcp.parallel_search(
                queries=iterative_queries,
                max_results_per_query=3,
                days_back=30
            )
            
            # 合并结果
            all_search_results = initial_search_results + additional_results
            print(f"✅ 补充收集到{len(additional_results)}条数据，总计{len(all_search_results)}条")
        else:
            all_search_results = initial_search_results
        
        # 步骤4: 创建报告大纲
        print("\n📋 步骤4: 创建报告大纲")
        outline = self.outline_mcp.create_outline(
            topic=topic,
            report_type=report_type,
            reference_data=all_search_results[:5]  # 使用前5个结果作为参考
        )
        print(f"✅ 大纲创建完成，包含{len(outline.subsections)}个主章节")
        
        # 用户交互：审查大纲
        if self.interaction_mcp:
            print("\n👤 用户交互: 审查大纲")
            outline_review = self.interaction_mcp.interactive_outline_review(outline.to_dict())
            
            if not outline_review["approved"]:
                print("🔧 用户要求修改大纲...")
                if outline_review["modifications"]:
                    # 根据用户反馈优化大纲
                    feedback = "; ".join([
                        f"{mod['section']}: {mod['suggestion']}" 
                        for mod in outline_review["modifications"]
                    ])
                    outline = self.outline_mcp.refine_outline(outline, feedback)
                    print("✅ 大纲已根据用户反馈优化")
        
        # 步骤5: 为每个章节收集针对性数据
        print("\n🎯 步骤5: 为各章节收集针对性数据")
        section_data = {}
        
        for section in outline.subsections:
            section_title = section.title
            
            # 生成针对性查询
            targeted_queries = self.query_mcp.generate_queries(
                topic=topic,
                strategy="targeted",
                context=f"{section_title}|{section.description}"
            )
            
            # 搜索章节特定数据
            section_results = self.search_mcp.parallel_search(
                queries=targeted_queries,
                max_results_per_query=4,
                days_back=30
            )
            
            section_data[section_title] = section_results
            print(f"  📝 {section_title}: {len(section_results)}条数据")
        
        # 步骤6: 生成章节内容
        print("\n✍️ 步骤6: 生成详细内容")
        
        # 配置内容写作参数
        writing_config = ContentWritingConfig(
            writing_style="professional",
            target_audience="通用",
            tone="objective",
            depth_level="detailed",
            include_examples=True,
            include_citations=True,
            max_section_length=2000,
            min_section_length=800
        )
        
        # 准备整体上下文
        overall_context = f"关于{topic}的{report_type}报告，包含{len(outline.subsections)}个主要章节"
        
        # 并行生成章节内容
        sections_for_writing = []
        for section in outline.subsections:
            sections_for_writing.append({
                "title": section.title,
                "content_data": section_data.get(section.title, [])
            })
        
        section_contents = self.content_mcp.write_multiple_sections(
            sections=sections_for_writing,
            overall_context=overall_context,
            config=writing_config
        )
        
        print(f"✅ 生成了{len(section_contents)}个章节的详细内容")
        
        # 步骤7: 生成执行摘要
        print("\n📄 步骤7: 生成执行摘要")
        
        # 收集所有内容用于摘要
        all_content_for_summary = []
        for title, content in section_contents.items():
            all_content_for_summary.append({
                "title": title,
                "content": content[:500]  # 限制长度用于摘要
            })
        
        executive_summary = self.summary_mcp.write_summary(
            content_data=all_content_for_summary,
            length_constraint="300-400字",
            format="executive",
            target_audience="决策者"
        )
        
        print("✅ 执行摘要生成完成")
        
        # 步骤8: 组装完整报告
        print("\n📑 步骤8: 组装完整报告")
        full_report = self._assemble_full_report(
            topic=topic,
            report_type=report_type,
            executive_summary=executive_summary,
            outline=outline,
            section_contents=section_contents,
            all_search_results=all_search_results
        )
        
        # 步骤9: 保存报告
        report_path = self._save_report(full_report, topic, report_type)
        
        print(f"✅ 报告生成完成: {report_path}")
        return report_path
    
    def _assemble_full_report(self, topic: str, report_type: str, executive_summary: str,
                             outline, section_contents: dict, all_search_results: list) -> str:
        """组装完整报告"""
        from datetime import datetime
        
        report_parts = []
        
        # 报告标题
        report_parts.append(f"# {topic} - {report_type.upper()}报告\n")
        
        # 报告信息
        report_parts.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_parts.append(f"**数据来源**: {len(all_search_results)}条搜索结果")
        report_parts.append(f"**报告章节**: {len(section_contents)}个主要章节\n")
        
        # 执行摘要
        report_parts.append("## 执行摘要\n")
        report_parts.append(executive_summary)
        report_parts.append("\n")
        
        # 目录
        report_parts.append("## 目录\n")
        for i, section in enumerate(outline.subsections, 1):
            report_parts.append(f"{i}. [{section.title}](#{self._anchor_link(section.title)})")
        report_parts.append("\n")
        
        # 章节内容
        for section in outline.subsections:
            section_title = section.title
            content = section_contents.get(section_title, "内容生成中...")
            
            report_parts.append(f"## {section_title}\n")
            report_parts.append(content)
            report_parts.append("\n")
        
        # 数据来源统计
        report_parts.append("## 数据来源统计\n")
        source_stats = {}
        for result in all_search_results:
            source_type = result.source_type if hasattr(result, 'source_type') else 'unknown'
            source_stats[source_type] = source_stats.get(source_type, 0) + 1
        
        for source_type, count in source_stats.items():
            report_parts.append(f"- {source_type}: {count}条")
        
        report_parts.append("\n---\n")
        report_parts.append("*本报告由MCP组件集成系统自动生成*")
        
        return '\n'.join(report_parts)
    
    def _anchor_link(self, title: str) -> str:
        """生成锚点链接"""
        import re
        # 简化处理，实际应用中可能需要更复杂的逻辑
        return re.sub(r'[^\w\s-]', '', title).replace(' ', '-').lower()
    
    def _save_report(self, report_content: str, topic: str, report_type: str) -> str:
        """保存报告"""
        from datetime import datetime
        
        # 创建报告目录
        os.makedirs("reports", exist_ok=True)
        
        # 生成文件名
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_topic}_{report_type}_{date_str}.md"
        filepath = os.path.join("reports", filename)
        
        # 保存文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return filepath


def demo_individual_mcp_components():
    """演示各个MCP组件的独立功能"""
    print("\n🧪 MCP组件独立功能演示")
    print("=" * 60)
    
    topic = "人工智能在教育中的应用"
    
    # 1. QueryGenerationMcp演示
    print("\n1️⃣ QueryGenerationMcp演示")
    query_mcp = QueryGenerationMcp()
    queries = query_mcp.generate_multi_strategy_queries(
        topic=topic,
        strategies=["initial", "academic", "news"]
    )
    for strategy, query_list in queries.items():
        print(f"  {strategy}: {len(query_list)}个查询")
    
    # 2. SearchMcp演示
    print("\n2️⃣ SearchMcp演示")
    search_mcp = SearchMcp()
    results = search_mcp.parallel_search(
        queries=queries["initial"][:3],  # 使用前3个查询
        max_results_per_query=2,
        max_workers=2
    )
    print(f"  搜索结果: {len(results)}条")
    
    # 3. AnalysisMcp演示
    print("\n3️⃣ AnalysisMcp演示")
    analysis_mcp = AnalysisMcp()
    
    if results:
        quality = analysis_mcp.analyze_quality(results, topic)
        print(f"  质量分析: {quality.score:.2f}")
        
        relevance = analysis_mcp.analyze_relevance(results[0], topic)
        print(f"  相关性分析: {relevance.score:.2f}")
    
    # 4. SummaryWriterMcp演示
    print("\n4️⃣ SummaryWriterMcp演示")
    summary_mcp = SummaryWriterMcp()
    
    if results:
        multi_summary = summary_mcp.write_multi_level_summary(
            content_data=results[:3],
            levels=["executive", "paragraph", "bullet_points"]
        )
        print(f"  多层次摘要: {len(multi_summary)}种格式")
    
    # 5. OutlineWriterMcp演示
    print("\n5️⃣ OutlineWriterMcp演示")
    outline_mcp = OutlineWriterMcp()
    outline = outline_mcp.create_outline(
        topic=topic,
        report_type="academic",
        reference_data=results[:3] if results else None
    )
    print(f"  大纲创建: {len(outline.subsections)}个主章节")
    
    # 6. DetailedContentWriterMcp演示
    print("\n6️⃣ DetailedContentWriterMcp演示")
    content_mcp = DetailedContentWriterMcp()
    
    if outline.subsections and results:
        section = outline.subsections[0]
        content = content_mcp.write_section_content(
            section_title=section.title,
            content_data=results[:2],
            overall_report_context=f"关于{topic}的学术报告"
        )
        print(f"  章节内容: {len(content)}字符")
    
    # 7. UserInteractionMcp演示
    print("\n7️⃣ UserInteractionMcp演示")
    interaction_mcp = UserInteractionMcp()
    
    # 演示不同类型的交互（在非交互环境中显示示例）
    print("  支持的交互类型:")
    print("    - 选择题 (get_user_choice)")
    print("    - 文本输入 (get_user_input)") 
    print("    - 确认对话 (get_confirmation)")
    print("    - 评分 (get_rating)")
    print("    - 多选 (get_multi_choice)")
    print("    - 内容审查 (review_and_modify)")


def main():
    """主函数"""
    print("🚀 MCP组件集成系统测试")
    print("=" * 60)
    
    # 检查是否在交互环境中
    interactive_mode = "--interactive" in sys.argv
    
    try:
        # 演示独立组件功能
        demo_individual_mcp_components()
        
        if interactive_mode:
            print("\n" + "=" * 60)
            print("🎯 完整报告生成演示")
            
            # 创建集成报告生成器
            generator = IntegratedReportGenerator(enable_user_interaction=True)
            
            # 生成完整报告
            topic = "生成式人工智能的发展与应用"
            report_path = generator.generate_comprehensive_report(
                topic=topic,
                report_type="comprehensive"
            )
            
            print(f"\n✅ 演示完成！报告已保存至: {report_path}")
        else:
            print("\n💡 提示: 添加 --interactive 参数体验完整的交互式报告生成")
            
            # 非交互模式的简化演示
            generator = IntegratedReportGenerator(enable_user_interaction=False)
            print("\n🔄 运行简化的报告生成流程...")
            
            # 可以在这里添加简化的演示逻辑
            print("✅ 简化演示完成")
        
    except KeyboardInterrupt:
        print("\n❌ 用户中断了演示")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 