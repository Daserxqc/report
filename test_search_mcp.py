#!/usr/bin/env python3
"""
SearchMcp测试和演示文件
展示如何使用统一的搜索MCP进行多源并行搜索
"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入SearchMcp
from collectors.search_mcp import SearchMcp, Document


def test_basic_search():
    """测试基础搜索功能"""
    print("🧪 测试1: 基础并行搜索")
    print("=" * 50)
    
    # 初始化SearchMcp
    search_mcp = SearchMcp()
    
    # 检查可用数据源
    available_sources = search_mcp.get_available_sources()
    print("📊 可用数据源:")
    for category, sources in available_sources.items():
        print(f"  {category}: {sources}")
    
    # 执行搜索
    queries = [
        "生成式人工智能最新发展",
        "ChatGPT GPT-4技术原理",
        "大语言模型商业应用"
    ]
    
    results = search_mcp.parallel_search(
        queries=queries,
        max_results_per_query=3,
        days_back=30,
        max_workers=4
    )
    
    print(f"\n📋 搜索结果统计:")
    print(f"  总结果数: {len(results)}")
    print(f"  去重URL数: {len(set(doc.url for doc in results))}")
    
    # 按数据源类型统计
    source_stats = {}
    for doc in results:
        source_stats[doc.source_type] = source_stats.get(doc.source_type, 0) + 1
    
    print(f"  按类型统计:")
    for source_type, count in source_stats.items():
        print(f"    {source_type}: {count}条")
    
    # 显示前3个结果
    print(f"\n🔍 前3个搜索结果:")
    for i, doc in enumerate(results[:3]):
        print(f"\n[{i+1}] 标题: {doc.title}")
        print(f"    来源: {doc.source} ({doc.source_type})")
        print(f"    URL: {doc.url}")
        print(f"    内容: {doc.content[:100]}...")
        if doc.authors:
            print(f"    作者: {', '.join(doc.authors)}")
        if doc.publish_date:
            print(f"    发布时间: {doc.publish_date}")


def test_category_search():
    """测试按类别搜索"""
    print("\n\n🧪 测试2: 按类别搜索")
    print("=" * 50)
    
    search_mcp = SearchMcp()
    
    # 测试学术搜索
    print("📚 学术搜索测试:")
    academic_results = search_mcp.search_by_category(
        queries=["machine learning transformer attention mechanism"],
        category='academic',
        max_results_per_query=2,
        days_back=365
    )
    
    print(f"  学术搜索结果: {len(academic_results)}条")
    for doc in academic_results[:2]:
        print(f"    - {doc.title} ({doc.source})")
        if doc.authors:
            print(f"      作者: {', '.join(doc.authors[:3])}...")
    
    # 测试新闻搜索
    print("\n📰 新闻搜索测试:")
    news_results = search_mcp.search_by_category(
        queries=["人工智能最新动态", "AI行业发展"],
        category='news',
        max_results_per_query=2,
        days_back=7
    )
    
    print(f"  新闻搜索结果: {len(news_results)}条")
    for doc in news_results[:2]:
        print(f"    - {doc.title} ({doc.source})")
        if doc.publish_date:
            print(f"      发布时间: {doc.publish_date}")


def test_fallback_search():
    """测试降级搜索"""
    print("\n\n🧪 测试3: 降级搜索测试")
    print("=" * 50)
    
    search_mcp = SearchMcp()
    
    # 使用降级搜索
    results = search_mcp.search_with_fallback(
        queries=["量子计算最新突破", "quantum computing breakthrough"],
        preferred_sources=['tavily', 'brave'],  # 首选网络搜索
        fallback_sources=['arxiv', 'academic'],  # 备选学术搜索
        max_results_per_query=3,
        days_back=30
    )
    
    print(f"📊 降级搜索结果: {len(results)}条")
    
    # 统计数据源分布
    source_distribution = {}
    for doc in results:
        source_distribution[doc.source] = source_distribution.get(doc.source, 0) + 1
    
    print("📈 数据源分布:")
    for source, count in source_distribution.items():
        print(f"  {source}: {count}条")


def test_document_standardization():
    """测试Document标准化"""
    print("\n\n🧪 测试4: Document对象标准化")
    print("=" * 50)
    
    # 创建示例Document
    doc = Document(
        title="生成式AI的未来发展趋势",
        content="生成式人工智能正在快速发展，包括文本生成、图像生成、代码生成等多个领域...",
        url="https://example.com/ai-future",
        source="tavily",
        source_type="web",
        publish_date="2024-01-15",
        authors=["张三", "李四"],
        venue="AI Research Journal",
        score=0.95
    )
    
    print("📋 Document对象示例:")
    print(f"  标题: {doc.title}")
    print(f"  来源: {doc.source} ({doc.source_type})")
    print(f"  域名: {doc.domain}")
    print(f"  作者: {', '.join(doc.authors)}")
    print(f"  发布时间: {doc.publish_date}")
    print(f"  相关性评分: {doc.score}")
    
    # 转换为字典
    doc_dict = doc.to_dict()
    print(f"\n📄 转换为字典后的键: {list(doc_dict.keys())}")


def demonstrate_integration_potential():
    """演示与现有agent的集成潜力"""
    print("\n\n🚀 集成潜力演示")
    print("=" * 50)
    
    print("📝 SearchMcp可以替代现有agent中的以下搜索逻辑:")
    
    integration_examples = {
        "generate_outline_report.py": [
            "OutlineDataCollector类中的并行搜索",
            "_execute_single_query方法",
            "多收集器管理逻辑"
        ],
        "generate_news_report_parallel.py": [
            "ParallelDataCollector类",
            "parallel_comprehensive_search方法",
            "多渠道搜索合并逻辑"
        ],
        "generate_insights_report_updated_copy.py": [
            "ParallelInsightsCollector类",
            "parallel_collect_section_queries方法",
            "搜索结果去重逻辑"
        ],
        "intent_search_agent.py": [
            "parallel_content_search方法",
            "_execute_single_search方法",
            "_deduplicate_results方法"
        ],
        "proposal_report_agent.py": [
            "search_academic_content方法",
            "_search_academic_papers方法",
            "_search_section_content方法"
        ]
    }
    
    for agent_file, components in integration_examples.items():
        print(f"\n🔧 {agent_file}:")
        for component in components:
            print(f"  ✅ {component}")
    
    print(f"\n💡 集成优势:")
    print(f"  🎯 统一接口: 所有agent使用相同的搜索API")
    print(f"  ⚡ 并行优化: 内置线程池管理和错误处理")
    print(f"  🔄 自动去重: URL级别的去重机制")
    print(f"  📊 标准化: 统一的Document数据结构")
    print(f"  🛡️ 容错机制: 自动降级和错误恢复")
    print(f"  📈 可扩展: 易于添加新的数据源")


def main():
    """运行所有测试"""
    print("🚀 SearchMcp 统一搜索系统测试")
    print("=" * 60)
    
    try:
        # 基础功能测试
        test_basic_search()
        
        # 类别搜索测试
        test_category_search()
        
        # 降级搜索测试
        test_fallback_search()
        
        # Document标准化测试
        test_document_standardization()
        
        # 集成潜力演示
        demonstrate_integration_potential()
        
        print(f"\n🎉 所有测试完成!")
        
    except KeyboardInterrupt:
        print(f"\n❌ 用户中断了测试")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 