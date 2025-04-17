from collectors.tavily_collector import TavilyCollector
import re

# 创建TavilyCollector实例
collector = TavilyCollector()

# 测试各种格式的参考资料
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

## 参考文献

"""

# 添加文档末尾包含部分内容的参考文献部分
test_content_with_refs = test_content + """
- [AI发展报告](https://example.com/report)
"""

# 添加空的参考文献部分
test_content_with_empty_refs = test_content + """

"""

# 添加带有其他格式的参考资料的测试
test_content_formats = """# 测试不同格式的参考资料

## 第一部分

这是内容。

参考资料
• 第一条参考资料
• 第二条参考资料

## 第二部分

这是更多内容。

**参考来源**:
- [来源一](http://example.com)
- [来源二](http://example.com/2)

## 第三部分

这是最后一部分内容。

参考文献
"""

# 运行测试
print("=== 测试标准格式 ===")
result1 = collector._normalize_heading_structure(test_content)

print("=== 测试带部分参考文献的格式 ===")
result2 = collector._normalize_heading_structure(test_content_with_refs)

print("=== 测试带空参考文献的格式 ===")
result3 = collector._normalize_heading_structure(test_content_with_empty_refs)

print("=== 测试不同格式的参考资料 ===")
result4 = collector._normalize_heading_structure(test_content_formats)

# 打印结果
print("\n=== 结果1: 标准格式处理 ===")
print(result1)

print("\n=== 结果2: 带部分参考文献的格式处理 ===")
print(result2)

print("\n=== 结果3: 带空参考文献的格式处理 ===")
print(result3)

print("\n=== 结果4: 不同格式的参考资料处理 ===")
print(result4) 