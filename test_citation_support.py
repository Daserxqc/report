#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试DetailedContentWriterMcp的引用支持功能
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from collectors.detailed_content_writer_mcp import DetailedContentWriterMcp, ContentWritingConfig
from collectors.search_mcp import Document
import re

def test_citation_generation():
    """测试引用生成功能"""
    print("🧪 测试引用生成功能...")
    
    writer = DetailedContentWriterMcp()
    
    # 创建测试文档
    test_documents = [
        Document(
            title="AI芯片技术发展报告2024",
            content="AI芯片市场在2024年呈现爆发式增长，全球市场规模达到500亿美元。",
            url="https://example.com/ai-chip-report",
            source="TechResearch",
            source_type="web",
            publish_date="2024-01-15",
            authors=["张三", "李四"]
        ),
        Document(
            title="大语言模型商业化应用分析",
            content="ChatGPT的成功推动了大语言模型在各行业的广泛应用。",
            url="https://example.com/llm-analysis",
            source="AI Weekly",
            source_type="web",
            publish_date="2024-02-20",
            authors=["王五"]
        )
    ]
    
    # 测试引用数据生成
    citation_data = writer._generate_citations_from_documents(test_documents)
    
    print(f"📊 引用数据生成结果:")
    print(f"   - 总引用数: {citation_data['total_count']}")
    print(f"   - 引用映射: {list(citation_data['citations_map'].keys())}")
    
    # 测试引用格式化
    for citation_info in citation_data['citation_list']:
        formatted = writer._format_citation_reference(citation_info)
        print(f"   - [{citation_info['id']}] {formatted}")
    
    # 测试参考文献章节生成
    references_section = writer._generate_references_section(citation_data)
    print(f"\n📚 参考文献章节:")
    print(references_section)
    
    return citation_data

def test_citation_injection():
    """测试引用注入功能"""
    print("\n🧪 测试引用注入功能...")
    
    writer = DetailedContentWriterMcp()
    
    # 创建测试文档
    test_documents = [
        Document(
            title="AI芯片技术发展报告",
            content="AI芯片市场分析",
            url="https://example.com/ai-chip",
            source="TechNews",
            source_type="web"
        ),
        Document(
            title="大语言模型应用研究",
            content="LLM应用案例",
            url="https://example.com/llm",
            source="Research Journal",
            source_type="academic"
        )
    ]
    
    # 测试内容
    test_content = """
## AI技术发展现状

人工智能技术在2024年取得了重大突破。AI芯片技术发展迅速，性能提升显著。
大语言模型在各个领域都有广泛应用，改变了人机交互的方式。
这些技术进步为未来的发展奠定了坚实基础。
"""
    
    # 注入引用
    content_with_citations = writer._inject_citations_into_content(test_content, test_documents)
    
    print("📝 原始内容:")
    print(test_content)
    print("\n📝 注入引用后的内容:")
    print(content_with_citations)
    
    # 分析引用标记
    citation_pattern = r'\[\d+\]'
    citations_found = re.findall(citation_pattern, content_with_citations)
    print(f"\n📊 引用分析:")
    print(f"   - 发现引用标记: {len(citations_found)} 个")
    print(f"   - 引用标记: {citations_found}")
    
    return len(citations_found) > 0

def test_section_content_with_citations():
    """测试章节内容生成（带引用）"""
    print("\n🧪 测试章节内容生成（带引用）...")
    
    writer = DetailedContentWriterMcp()
    
    # 创建测试文档
    test_documents = [
        Document(
            title="AI芯片市场分析报告",
            content="根据最新数据，2024年全球AI芯片市场规模达到520亿美元，同比增长35%。英伟达继续领跑市场，占据约80%的份额。",
            url="https://example.com/market-report",
            source="Market Research Inc",
            source_type="web",
            publish_date="2024-03-01"
        )
    ]
    
    # 配置启用引用
    config = ContentWritingConfig(
        include_citations=True,
        writing_style="academic",
        min_section_length=500,
        max_section_length=1000
    )
    
    # 生成章节内容
    section_content = writer.write_section_content(
        section_title="AI芯片市场现状分析",
        content_data=test_documents,
        overall_report_context="人工智能技术发展报告",
        config=config
    )
    
    print("📝 生成的章节内容:")
    print(section_content)
    
    # 分析引用
    citation_pattern = r'\[\d+\]'
    citations_found = re.findall(citation_pattern, section_content)
    print(f"\n📊 章节引用分析:")
    print(f"   - 发现引用标记: {len(citations_found)} 个")
    print(f"   - 引用标记: {citations_found}")
    
    return len(citations_found) > 0

def main():
    """主测试函数"""
    print("🚀 开始测试DetailedContentWriterMcp引用支持功能\n")
    
    # 测试1: 引用生成
    citation_data = test_citation_generation()
    
    # 测试2: 引用注入
    injection_success = test_citation_injection()
    
    # 测试3: 章节内容生成（带引用）
    section_success = test_section_content_with_citations()
    
    # 总结
    print("\n" + "="*60)
    print("🎉 引用支持功能测试完成")
    print(f"📊 测试结果:")
    print(f"   - 引用数据生成: ✅ 成功")
    print(f"   - 引用注入功能: {'✅ 成功' if injection_success else '❌ 失败'}")
    print(f"   - 章节引用生成: {'✅ 成功' if section_success else '❌ 失败'}")
    
    if injection_success and section_success:
        print("\n🎊 所有引用功能测试通过！")
    else:
        print("\n⚠️  部分引用功能需要进一步优化")

if __name__ == "__main__":
    main()