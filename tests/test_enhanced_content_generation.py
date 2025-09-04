import os
import json
from datetime import datetime
from pathlib import Path

def simulate_report_generation():
    """
    模拟从搜索结果到最终Markdown报告的生成过程，以定位内容丢失点
    """
    print("=" * 60)
    print("开始模拟报告生成过程...")
    print("=" * 60)
    
    # 1. 创建模拟的搜索结果数据
    print("\n1. 创建模拟搜索结果...")
    topic = "元宇宙"
    search_results = [
        {
            "title": "元宇宙概念解析",
            "content": "元宇宙(Metaverse)是人们可以在基于互联网的虚拟世界中通过数字形象进行交流的空间，它融合了虚拟现实、增强现实和物联网等技术。",
            "url": "https://example.com/metaverse-concept",
            "source": "行业研究报告",
            "section": "行业概况"
        },
        {
            "title": "元宇宙政策框架",
            "content": "随着元宇宙概念的火热，各国政府正在制定相关政策框架，包括数字资产监管、隐私保护和内容审核等方面。中国也出台了促进元宇宙健康发展的指导意见。",
            "url": "https://example.com/metaverse-policy",
            "source": "政策分析",
            "section": "政策支持"
        },
        {
            "title": "元宇宙市场规模分析",
            "content": "据估计，全球元宇宙市场规模将从2022年的约600亿美元增长到2030年的约1.5万亿美元，年复合增长率约为40%。游戏、社交和企业协作是主要应用领域。",
            "url": "https://example.com/metaverse-market",
            "source": "市场研究",
            "section": "市场规模"
        },
        {
            "title": "元宇宙技术发展趋势",
            "content": "元宇宙的核心技术包括VR/AR、区块链、AI和高速网络。未来发展趋势包括更轻便的设备、更真实的感官体验、跨平台互操作性以及去中心化基础设施。",
            "url": "https://example.com/metaverse-tech",
            "source": "技术分析",
            "section": "技术趋势"
        }
    ]
    
    # 2. 打印搜索结果统计
    print(f"搜索结果：{len(search_results)}条")
    for i, result in enumerate(search_results):
        print(f"  结果{i+1}: {result['title']} (章节: {result['section']})")
    
    # 3. 按章节整合内容 - 模拟_direct_integrate_results方法的核心功能
    print("\n2. 按章节整合内容...")
    sections = {}
    all_sources = []
    
    # 将结果按章节分类
    for result in search_results:
        section = result.get("section", "其他信息")
        if section not in sections:
            sections[section] = []
        
        # 提取并添加内容
        sections[section].append({
            "title": result.get("title", ""),
            "content": result.get("content", ""),
            "url": result.get("url", "#")
        })
        
        # 记录来源
        source_info = {
            "title": result.get("title", ""),
            "url": result.get("url", "#")
        }
        if source_info not in all_sources:
            all_sources.append(source_info)
    
    print(f"整理出{len(sections)}个章节:")
    for section_name in sections:
        print(f"  {section_name}: {len(sections[section_name])}个条目")
    
    # 4. 生成最终报告内容
    print("\n3. 生成报告内容...")
    
    markdown_content = f"# {topic}行业洞察报告\n\n"
    
    section_count = 0
    for section_name, section_items in sections.items():
        section_count += 1
        markdown_content += f"## {section_count}. {section_name}\n\n"
        
        for item in section_items:
            title = item["title"]
            content = item["content"]
            url = item["url"]
            
            markdown_content += f"### {title}\n\n"
            markdown_content += f"{content}\n\n"
            markdown_content += f"**来源**: [{url}]({url})\n\n"
    
    # 添加参考来源
    if all_sources:
        markdown_content += "## 参考来源\n\n"
        for i, source in enumerate(all_sources, 1):
            markdown_content += f"{i}. [{source['title']}]({source['url']})\n"
    
    # 5. 输出最终内容长度信息
    total_chars = len(markdown_content)
    chinese_chars = sum(1 for c in markdown_content if '\u4e00' <= c <= '\u9fff')
    print(f"生成的Markdown内容长度: {total_chars}字符")
    print(f"中文字符数: {chinese_chars} ({chinese_chars/total_chars*100:.1f}%)")
    
    # 6. 写入文件并测试不同格式
    output_dir = Path("test_reports")
    output_dir.mkdir(exist_ok=True)
    
    print("\n4. 保存文件:")
    
    # a. 保存为Markdown文件 (重要: 显式指定UTF-8编码)
    md_path = output_dir / "fixed_report.md"
    try:
        # 确保使用UTF-8编码，并设置BOM标记
        with open(md_path, "w", encoding="utf-8-sig") as f:
            f.write(markdown_content)
        md_size = os.path.getsize(md_path)
        print(f"  Markdown文件已保存: {md_path}, 大小: {md_size} 字节")
        
        # 验证文件内容
        with open(md_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
            read_chinese = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
            print(f"  ✓ 文件验证成功: 读取到 {read_chinese} 个中文字符 (应有: {chinese_chars})")
    except Exception as e:
        print(f"  ✗ 保存Markdown文件失败: {str(e)}")
    
    # b. 保存为文本文件（纯文本格式）
    txt_path = output_dir / "fixed_report.txt"
    try:
        with open(txt_path, "w", encoding="utf-8-sig") as f:
            f.write(markdown_content)
        print(f"  文本文件已保存: {txt_path}, 大小: {os.path.getsize(txt_path)} 字节")
    except Exception as e:
        print(f"  ✗ 保存文本文件失败: {str(e)}")
    
    # c. 保存为JSON格式（可用于调试）
    json_content = {
        "title": f"{topic}行业洞察报告",
        "sections": sections,
        "sources": all_sources,
        "raw_markdown": markdown_content
    }
    json_path = output_dir / "fixed_report.json"
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_content, f, ensure_ascii=False, indent=2)
        print(f"  JSON文件已保存: {json_path}, 大小: {os.path.getsize(json_path)} 字节")
    except Exception as e:
        print(f"  ✗ 保存JSON文件失败: {str(e)}")
    
    # d. 生成HTML预览（用于检查渲染效果）
    try:
        # 不使用markdown库，直接生成简单HTML
        # 将Markdown格式的标题转换为HTML标题
        html_lines = []
        for line in markdown_content.split('\n'):
            if line.startswith('# '):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith('## '):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith('### '):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith('**') and line.endswith('**'):
                html_lines.append(f"<strong>{line[2:-2]}</strong>")
            elif line.startswith('- '):
                html_lines.append(f"<li>{line[2:]}</li>")
            elif '**' in line:
                # 简单处理粗体
                line = line.replace('**', '<strong>', 1)
                line = line.replace('**', '</strong>', 1)
                html_lines.append(f"<p>{line}</p>")
            elif line.strip():
                html_lines.append(f"<p>{line}</p>")
            else:
                html_lines.append("")
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic}行业洞察报告</title>
    <style>
        body {{ 
            font-family: "Microsoft YaHei", 微软雅黑, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1, h2, h3 {{ margin-top: 1.5em; }}
        a {{ color: #0066cc; }}
    </style>
</head>
<body>
{os.linesep.join(html_lines)}
</body>
</html>
"""
        html_path = output_dir / "fixed_report.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"  HTML预览已保存: {html_path}, 大小: {os.path.getsize(html_path)} 字节")
    except Exception as e:
        print(f"  ✗ 保存HTML预览失败: {str(e)}")
    
    # 7. 列出生成的文件
    print("\n5. 生成的文件列表:")
    try:
        files = list(output_dir.glob("fixed_*"))
        for file in files:
            print(f"  - {file.name} ({os.path.getsize(file)} 字节)")
    except Exception as e:
        print(f"  ✗ 列出文件失败: {str(e)}")
    
    print("\n" + "=" * 60)
    print("报告生成测试完成！正确编码的文件已保存在test_reports目录下")
    print("=" * 60)

if __name__ == "__main__":
    simulate_report_generation()