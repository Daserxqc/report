#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用于将文本中的"来源链接"替换为研究方向末尾的统一链接的简单脚本
"""

import re
import argparse
import os

def fix_source_links(input_file, output_file=None):
    """
    修复文件中的引用链接格式，将链接整合到每个数字段落（研究方向）的末尾
    
    参数:
    input_file -- 输入文件路径
    output_file -- 输出文件路径，如果不提供，将使用默认命名规则
    """
    # 读取文件内容
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到"未来展望与发展趋势"的位置
    future_pos = content.find("## 未来展望与发展趋势")
    if future_pos == -1:
        # 尝试查找替代标题
        future_pos = content.find("# AI_Agent领域核心发展趋势与未来展望")
        if future_pos == -1:
            print("无法识别研究方向段落")
            return content
    
    # 分割内容
    first_part = content[:future_pos]
    second_part = content[future_pos:]
    
    # 使用段落标题分割文本
    # 先查找所有形如"### 1. **标题**"的段落标题
    sections = re.split(r'(?=###\s+\d+\.\s+\*\*.*?\*\*)', first_part)
    
    # 处理每个部分
    processed_parts = []
    section_count = 0
    
    for part in sections:
        if not part.strip():
            continue
            
        section_count += 1
        
        # 提取当前部分的所有引用和链接
        # 匹配形如[来源1](http://...)的格式
        citations = re.findall(r'\[来源(\d+)\]\((https?://[^\)]+)\)', part)
        
        # 创建引用映射
        url_map = {}
        for cite_num, url in citations:
            url_map[cite_num] = url
        
        # 替换文中的引用格式
        processed_part = part
        
        # 替换所有[来源X](URL)为[X]
        for cite_num in sorted(url_map.keys(), key=int):
            processed_part = re.sub(
                r'\[来源' + cite_num + r'\]\([^\)]+\)',
                f'[{cite_num}]',
                processed_part
            )
        
        # 移除旧的参考文献部分
        processed_part = re.sub(r'\n*---\n*参考文献:[\s\S]*?(?=###|\Z)', '', processed_part)
        
        # 清理引用格式
        processed_part = re.sub(r'\[\[(\d+)\]\]', r'[\1]', processed_part)  # 修复双括号
        processed_part = re.sub(r'\[(\d+)\[', r'[\1]', processed_part)  # 修复缺失右括号
        processed_part = re.sub(r'\](\d+)\]', r'][\1]', processed_part)  # 修复连续引用
        processed_part = re.sub(r'\[\s*\]', '', processed_part)  # 移除空引用
        
        # 在每个段落末尾添加参考文献（如果有引用）
        if url_map:
            # 确保在段落末尾添加分隔符和参考文献
            if not processed_part.endswith('\n'):
                processed_part += '\n'
            processed_part += '\n---\n\n参考文献:\n'
            # 按引用编号排序
            for cite_num in sorted(url_map.keys(), key=int):
                processed_part += f"[{cite_num}]: {url_map[cite_num]}\n"
            processed_part += '\n'
        
        processed_parts.append(processed_part)
    
    # 合并修改后的第一部分
    fixed_first_part = ''.join(processed_parts)
    
    # 合并修复后的内容
    fixed_content = fixed_first_part + second_part
    
    # 如果没有指定输出文件，则生成一个默认名称
    if output_file is None:
        base_name = os.path.basename(input_file)
        name, ext = os.path.splitext(base_name)
        output_file = os.path.join(os.path.dirname(input_file), f"{name}_fixed{ext}")
    
    # 写入修复后的内容
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"文件已修复并保存至: {output_file}")
    return output_file

def main():
    parser = argparse.ArgumentParser(description='修复研究报告中的引用链接格式。')
    parser.add_argument('input_file', help='输入文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径（可选）')
    
    args = parser.parse_args()
    fix_source_links(args.input_file, args.output)

if __name__ == "__main__":
    main()