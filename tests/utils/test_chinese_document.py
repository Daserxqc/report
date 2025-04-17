import os
import sys
from datetime import datetime

def generate_test_document():
    """
    生成测试文档结构，用于验证中文内容的生成和展示
    """
    # 当前日期
    current_date = "2025-04-10"  # 固定日期用于测试
    
    # 创建文档结构
    sections = [
        {
            "id": 1,
            "title": "元宇宙产业概况与历史发展",
            "content": "本文概述了元宇宙产业的定义，梳理了其发展历程，并分析了当前的市场状况。重点介绍了这一新兴产业的演变过程和现阶段发展态势。"
        },
        {
            "id": 2,
            "title": "政策与法规支持",
            "content": "本文分析了元宇宙领域的政策环境与法规框架，重点探讨了各国政府对该产业的支持措施与发展导向。研究表明，政策法规在推动元宇宙技术创新与产业规范方面发挥着关键作用。"
        },
        {
            "id": 3,
            "title": "市场规模与增长趋势",
            "content": "该文分析了元宇宙市场的当前规模与增长趋势，并提供了未来发展的预测，重点探讨了该领域的高增长率及其潜在的市场扩张空间。"
        },
        {
            "id": 4,
            "title": "技术趋势与创新",
            "content": "该文章探讨了元宇宙领域的关键技术趋势与创新突破，重点分析了虚拟现实、区块链等核心技术的最新发展。研究揭示了元宇宙技术正在从概念验证向实际应用加速转型，为行业未来发展提供了重要方向。"
        }
    ]
    
    # 生成HTML文档
    html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>元宇宙产业研究报告</title>
    <style>
        body {
            font-family: "Microsoft YaHei", 微软雅黑, "Heiti SC", 黑体-简, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        .section {
            margin-bottom: 40px;
            border-bottom: 1px solid #eee;
            padding-bottom: 20px;
        }
        .section-title {
            font-size: 22px;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
        }
        .section-meta {
            font-size: 14px;
            color: #666;
            margin-bottom: 15px;
        }
        .section-content {
            font-size: 16px;
            color: #333;
            text-align: justify;
        }
        .links {
            display: block;
            color: #0066cc;
            margin-top: 10px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <h1>元宇宙产业研究报告</h1>
"""
    
    # 添加章节内容
    for section in sections:
        html_content += f"""
    <div class="section">
        <div class="section-title">{section["id"]}. {section["title"]}</div>
        <div class="section-meta">来源: 系统分析 | 日期: {current_date} | 作者: 行业分析</div>
        <div class="section-content">{section["content"]}</div>
        <a href="#" class="links">链接: #</a>
    </div>
"""
    
    # 关闭HTML文档
    html_content += """
</body>
</html>
"""
    
    # 保存HTML文件
    with open("test_chinese_report.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"测试文档已生成: test_chinese_report.html")

if __name__ == "__main__":
    print("开始生成测试中文文档...")
    generate_test_document()
    print("文档生成完成") 