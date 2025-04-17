from collectors.tavily_collector import TavilyCollector

# 创建TavilyCollector实例
collector = TavilyCollector()

# 模拟一些包含不同标题格式的Markdown内容
test_content = """# 人工智能行业洞察报告

这是一段简介文字。

# 行业概况

人工智能是通过计算机系统模拟人类智能的技术，具备感知环境、传感器等硬件捕捉数据；认知层依托算法模型解析信息；决策层等功能。

**核心技术组成**

人工智能的核心技术包括机器学习、深度学习、自然语言处理等。

**主要应用领域**：医疗健康、金融科技、智能制造。

**来源**: AI产业报告 | **日期**: 2023-05-01 | **作者**: 张三, 李四

# 政策支持

我国政府高度重视人工智能发展，陆续出台多项支持政策。

**2017年国务院发布《新一代人工智能发展规划》**

该规划提出了到2030年分三步走的战略目标。

**参考来源**:
- [国务院政策文件库](https://www.gov.cn)
- [人工智能发展报告](https://example.com)

# 技术趋势

多模态大模型正成为行业发展新方向。

**计算能力提升**
算力成本持续下降，专用芯片加速发展。

**人才培养需求**：行业发展面临人才短缺问题，需要加强培养。

## 未来展望

行业仍处于快速发展阶段，未来五年市场规模将持续增长。

**参考来源**:
- [行业趋势报告](https://example.com/trends)
- [AI发展白皮书](https://example.com/whitepaper)

**链接**: [行业研究报告](https://example.com/report)

## 参考文献

"""

# 应用标题规范化函数
normalized_content = collector._normalize_heading_structure(test_content)

# 打印结果
print("=== 原始内容 ===")
print(test_content)
print("\n=== 规范化后的内容 ===")
print(normalized_content) 