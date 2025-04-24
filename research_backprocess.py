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
    修复文件中的引用链接格式，将链接整合放到每个数字段落（研究方向）的末尾
    
    参数:
    input_file -- 输入文件路径
    output_file -- 输出文件路径，如果不提供，将使用默认命名规则
    """
    # 读取文件内容
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到"未来展望与发展趋势"的位置
    future_outlook_pos = content.find("# 未来展望与发展趋势")
    if future_outlook_pos == -1:
        print("无法识别研究方向格式。")
        return
    
    # 分割内容，只处理前半部分
    first_part = content[:future_outlook_pos]
    second_part = content[future_outlook_pos:]
    
    # 用数字标题将第一部分分割成不同段落
    # 查找所有形如"1. **标题**"的段落标题
    headings = re.findall(r'\n\d+\.\s+\*\*.*?\*\*.*?\n', first_part)
    
    if not headings:
        print("无法识别研究方向段落。")
        return
    
    # 使用段落标题分割文本
    sections = re.split(r'(\n\d+\.\s+\*\*.*?\*\*.*?\n)', first_part)
    
    # 处理每个部分
    fixed_parts = []
    for i in range(len(sections)):
        part = sections[i]
        
        # 如果是段落标题，直接添加
        if part in headings:
            fixed_parts.append(part)
        # 如果是段落内容
        elif i > 0 and sections[i-1] in headings:
            # 查找并收集所有链接
            links = re.findall(r'\[来源\]\((.*?)\)', part)
            
            # 从文本中移除链接
            cleaned_part = re.sub(r'\[来源\]\((.*?)\)', '', part)
            
            # 如果有链接，添加到段落末尾
            if links:
                # 确保段落末尾有换行
                if not cleaned_part.endswith('\n'):
                    cleaned_part += '\n'
                
                # 添加统一的链接段落
                cleaned_part += "\n参考文献: " + ", ".join(links) + "\n"
            
            fixed_parts.append(cleaned_part)
        else:
            fixed_parts.append(part)
    
    # 合并修改后的第一部分
    fixed_first_part = ''.join(fixed_parts)
    
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