import os
from datetime import datetime

def test_markdown_generation():
    """
    测试生成带有中文内容的Markdown文件
    """
    print("开始测试Markdown生成...")
    
    # 创建一些示例内容
    current_date = datetime.now().strftime('%Y-%m-%d')
    topic = "元宇宙"
    
    # 构建Markdown内容
    markdown_content = f"""# {topic}行业洞察报告

## 1. 元宇宙产业概况与历史发展

**来源**: 系统分析 | **日期**: {current_date} | **作者**: 行业分析

本文概述了元宇宙产业的定义，梳理了其发展历程，并分析了当前的市场状况。重点介绍了这一新兴产业的演变过程和现阶段发展态势。

**链接**: [#](#)

## 2. 政策与法规支持

**来源**: 系统分析 | **日期**: {current_date} | **作者**: 行业分析

本文分析了元宇宙领域的政策环境与法规框架，重点探讨了各国政府对该产业的支持措施与发展导向。研究表明，政策法规在推动元宇宙技术创新与产业规范方面发挥着关键作用。

**链接**: [#](#)

## 3. 市场规模与增长趋势

**来源**: 系统分析 | **日期**: {current_date} | **作者**: 行业分析

该文分析了元宇宙市场的当前规模与增长趋势，并提供了未来发展的预测，重点探讨了该领域的高增长率及其潜在的市场扩张空间。

**链接**: [#](#)

## 4. 技术趋势与创新

**来源**: 系统分析 | **日期**: {current_date} | **作者**: 行业分析

该文章探讨了元宇宙领域的关键技术趋势与创新突破，重点分析了虚拟现实、区块链等核心技术的最新发展。研究揭示了元宇宙技术正在从概念验证向实际应用加速转型，为行业未来发展提供了重要方向。

**链接**: [#](#)

## 参考来源

1. [元宇宙产业概况与历史发展](#)
2. [政策与法规支持](#)
3. [市场规模与增长趋势](#)
4. [技术趋势与创新](#)
"""

    # 1. 使用UTF-8编码写入文件
    print("使用UTF-8编码写入Markdown文件...")
    with open("test_report_utf8.md", "w", encoding="utf-8") as f:
        f.write(markdown_content)
    print(f"已写入UTF-8文件: test_report_utf8.md, 大小: {os.path.getsize('test_report_utf8.md')} 字节")
    
    # 2. 检查文件内容是否正确写入
    with open("test_report_utf8.md", "r", encoding="utf-8") as f:
        content = f.read()
        chars_count = len(content)
        chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
        print(f"读取文件内容，总字符数: {chars_count}, 中文字符数: {chinese_chars}")
    
    # 3. 尝试不同的编码
    encodings = ["gbk", "gb2312", "gb18030"]
    for encoding in encodings:
        try:
            with open(f"test_report_{encoding}.md", "w", encoding=encoding) as f:
                f.write(markdown_content)
            print(f"已写入{encoding.upper()}文件: test_report_{encoding}.md, 大小: {os.path.getsize(f'test_report_{encoding}.md')} 字节")
        except Exception as e:
            print(f"使用{encoding.upper()}编码写入文件失败: {str(e)}")
    
    print("Markdown生成测试完成")

if __name__ == "__main__":
    test_markdown_generation() 