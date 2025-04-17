from collectors.tavily_collector import TavilyCollector
from generators.report_generator import ReportGenerator
import datetime

def test_report_with_references():
    """
    测试报告生成流程，关注参考文献处理
    """
    print("=== 测试报告生成中的参考文献处理 ===")
    
    # 创建模拟数据
    mock_articles = []
    # 创建模拟的行业洞察数据
    topic = "人工智能"
    
    # 创建TavilyCollector实例，获取行业洞察
    collector = TavilyCollector()
    
    # 准备包含参考资料的测试内容
    test_content = """# 人工智能行业洞察报告

这是一段简介文字。

## 行业概况

人工智能是通过计算机系统模拟人类智能的技术，具备感知环境、传感器等硬件捕捉数据；认知层依托算法模型解析信息；决策层等功能。

### 核心技术组成

人工智能的核心技术包括机器学习、深度学习、自然语言处理等。

## 政策支持

我国政府高度重视人工智能发展，陆续出台多项支持政策。

参考资料:
• 人工智能 (AI) 市场规模和份额分析 - Mordor Intelligence (Web): https://www.mordorintelligence.com/zh-CN/industry-reports/global-artificial-intelligence-market
• 2025年中国人工智能行业全景图谱》 (附市场规模 - 新浪财经 (Web): https://finance.sina.com.cn/roll/2025-02-12/doc-inekevpe2463354.shtml

## 技术趋势

多模态大模型正成为行业发展新方向。

**参考来源**:
- [AI技术趋势报告](https://example.com/tech-trends)
- [机器学习进展](https://example.com/ml-progress)

### 计算能力提升
算力成本持续下降，专用芯片加速发展。

## 未来展望

行业仍处于快速发展阶段，未来五年市场规模将持续增长。

参考来源:
- 探讨人工智能的未来发展与挑战 - 知乎 - 知乎专栏 (Web): https://zhuanlan.zhihu.com/p/667800015
- 展望AI的未来十年【2023-2024】 - 知乎专栏 (Web): https://zhuanlan.zhihu.com/p/680499596
"""
    
    # 规范化标题结构和引用
    normalized_content = collector._normalize_heading_structure(test_content)
    
    # 创建模拟文章
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    article = {
        'title': f"{topic}行业洞察报告",
        'authors': ['系统生成'],
        'summary': f"{topic}行业的详细分析",
        'published': current_date,
        'url': 'https://example.com/report',
        'source': '系统分析',
        'content': normalized_content,
        'structured_section': True  # 标记为结构化章节
    }
    
    mock_articles.append(article)
    
    # 准备section_articles数据结构
    section_articles = {
        "行业洞察": mock_articles,
        "行业最新动态": [],
        "研究方向": []
    }
    
    # 创建ReportGenerator实例
    generator = ReportGenerator()
    
    # 生成报告
    report = generator.generate_full_report(topic, section_articles)
    
    # 打印生成的报告
    print("\n=== 生成的报告 ===")
    print(report)
    
    # 检查报告中参考文献部分的数量
    reference_count = report.count("参考文献")
    print(f"\n在报告中找到 {reference_count} 个'参考文献'出现")
    
    # 检查是否只有一个参考文献部分
    if reference_count > 1:
        print("警告: 在报告中发现多个参考文献部分！")
    else:
        print("成功: 报告中只有一个参考文献部分")

if __name__ == "__main__":
    test_report_with_references() 