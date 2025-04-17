from collectors.tavily_collector import TavilyCollector
import re

# 创建TavilyCollector实例
collector = TavilyCollector()

# 模拟一些包含参考资料和参考文献的Markdown内容，使格式与截图中的一致
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
• 【产业政策】2024 年人工智能政策年度盘点与 2025 年展望 - 知乎 (Web): https://zhuanlan.zhihu.com/p/17348192185

## 技术趋势

多模态大模型正成为行业发展新方向。

### 计算能力提升
算力成本持续下降，专用芯片加速发展。

## 未来展望

行业仍处于快速发展阶段，未来五年市场规模将持续增长。

参考资料:
• 探讨人工智能的未来发展与挑战 - 知乎 - 知乎专栏 (Web): https://zhuanlan.zhihu.com/p/667800015
• 展望AI的未来十年【2023-2024】 - 知乎专栏 (Web): https://zhuanlan.zhihu.com/p/680499596
• 人工智能的未来发展趋势（2025-2035年） - Csdn博客 (Web): https://blog.csdn.net/weixin_42412297/article/details/146154985

## 参考文献

"""

# 测试算法最简单的版本
import re

def manual_normalize(content):
    """简单直接的规范化函数"""
    lines = content.split('\n')
    result_lines = []
    references = []
    
    # 先提取所有参考资料
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 如果是参考资料行，收集下面的条目
        if line.startswith('参考资料:'):
            i += 1
            # 收集直到下一个标题或结束
            while i < len(lines) and not lines[i].strip().startswith('#'):
                if lines[i].strip().startswith('•'):
                    references.append(lines[i].strip())
                i += 1
            continue
            
        # 跳过空的参考文献部分
        if line.startswith('## 参考文献') and (i + 1 >= len(lines) or not any(lines[j].strip() for j in range(i+1, len(lines)))):
            i += 1
            continue
            
        result_lines.append(lines[i])
        i += 1
    
    # 重建内容并添加参考文献
    result = '\n'.join(result_lines)
    if references:
        result = result.rstrip() + '\n\n## 参考文献\n\n'
        for ref in references:
            result += ref + '\n'
    
    return result

# 使用简单的手动规范化函数
normalized_content = manual_normalize(test_content)

# 再使用collector中的规范化函数
collector_normalized = collector._normalize_heading_structure(test_content)

# 打印结果
print("\n=== 原始内容 ===")
print(test_content)
print("\n=== 简单手动规范化后的内容 ===")
print(normalized_content)
print("\n=== Collector规范化后的内容 ===")
print(collector_normalized) 