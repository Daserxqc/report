#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Markdown报告标题修复工具

用于修复报告文件中的重复标题问题，删除一级标题前面重复的二级标题。
例如删除 "## 政策支持" 和 "# 智能制造政策支持深度分析" 中的 "## 政策支持"。
使用方法：python fix_md_headings.py <markdown_file_path>
"""

import re
import sys
import os
from pathlib import Path

def fix_percentage_formatting(content):
    """
    修复文本中百分比数字周围的双星号（**）问题
    
    Args:
        content (str): 文本内容
        
    Returns:
        str: 修复后的文本
    """
    # 修复数字和百分比周围的多余星号
    # 匹配模式: **数字%** 或 **数字** 
    pattern = r'\*\*(\d+(?:\.\d+)?(?:%)?)\*\*'
    
    # 查找所有匹配项
    matches = re.findall(pattern, content)
    fixed_count = 0
    
    # 替换每个匹配项
    for match in matches:
        original = f"**{match}**"
        fixed = match
        content = content.replace(original, fixed)
        fixed_count += 1
    
    if fixed_count > 0:
        print(f"修复了 {fixed_count} 处数字/百分比周围的星号问题")
    
    return content

def fix_markdown_headings_content(content):
    """
    修复Markdown内容字符串中的重复标题问题
    
    Args:
        content (str): Markdown内容字符串
        
    Returns:
        str: 修复后的内容
    """
    try:
        # 修复百分比数字周围的双星号问题
        content = fix_percentage_formatting(content)
        
        # 使用正则表达式查找模式：二级标题后紧跟着一级标题，且一级标题包含二级标题内容
        pattern = r'(## ([^\n#]+))\s*\n+# ([^\n#]+)'
        matches = re.findall(pattern, content)
        print(f"找到 {len(matches)} 处可能重复的标题")
        
        # 用于提取报告主题的正则表达式
        topic_pattern = r'^# ([^\n#]+?)(?:行业洞察|行业趋势|行业概况|研究方向|最新动态|报告).*?$'
        topic_match = re.search(topic_pattern, content, re.MULTILINE)
        topic = topic_match.group(1).strip() if topic_match else ""
        
        if topic:
            print(f"检测到报告主题: {topic}")
        
        # 处理每个匹配项
        for full_h2, h2_title, h1_title in matches:
            h2_title = h2_title.strip()
            h1_title = h1_title.strip()
            
            # 检查一级标题是否包含二级标题内容
            if h2_title in h1_title:
                print(f"检测到重复标题: '{h2_title}' 在 '{h1_title}'")
                # 直接删除二级标题行
                content = content.replace(full_h2 + "\n\n", "")
                print(f"已删除重复的二级标题: '{h2_title}'")
            
            # 特殊情况：一级标题包含主题名+二级标题（例如 "智能制造政策支持深度分析"）
            elif topic and f"{topic}{h2_title}" in h1_title or h2_title in h1_title.replace(topic, ""):
                print(f"检测到复合重复标题: '{h2_title}' 在 '{h1_title}'")
                # 直接删除二级标题行
                content = content.replace(full_h2 + "\n\n", "")
                print(f"已删除复合重复的二级标题: '{h2_title}'")
        
        return content
        
    except Exception as e:
        print(f"修复内容过程中出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return content  # 出错时返回原始内容

def fix_markdown_headings(file_path):
    """
    修复Markdown文件中的重复标题问题
    
    Args:
        file_path (str或str): Markdown文件路径或内容字符串
        
    Returns:
        bool或str: 处理文件时返回布尔值表示成功与否，处理字符串时返回修复后的内容
    """
    # 如果参数是字符串内容而不是文件路径
    if isinstance(file_path, str) and ('\n' in file_path or len(file_path) > 200):
        return fix_markdown_headings_content(file_path)
        
    try:
        # 读取原始文件内容
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # 保存原始内容的备份
        if isinstance(file_path, Path):
            backup_path = str(file_path) + '.bak'
        else:
            backup_path = file_path + '.bak'
        with open(backup_path, 'w', encoding='utf-8-sig') as f:
            f.write(content)
        
        print(f"已创建备份文件: {backup_path}")
        
        # 使用内容处理函数修复内容
        fixed_content = fix_markdown_headings_content(content)
        
        # 保存修复后的内容
        with open(file_path, 'w', encoding='utf-8-sig') as f:
            f.write(fixed_content)
        
        print(f"文件修复完成: {file_path}")
        return True
        
    except Exception as e:
        print(f"修复过程中出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def process_directory(directory_path, file_pattern="*.md"):
    """处理目录中所有匹配的Markdown文件"""
    directory = Path(directory_path)
    if not directory.exists() or not directory.is_dir():
        print(f"错误: 目录不存在或不是有效目录: {directory_path}")
        return False
    
    # 获取所有匹配的文件
    files = list(directory.glob(file_pattern))
    print(f"找到 {len(files)} 个匹配的Markdown文件")
    
    success_count = 0
    for file_path in files:
        print(f"\n处理文件: {file_path}")
        if fix_markdown_headings(file_path):
            success_count += 1
    
    print(f"\n总共处理了 {len(files)} 个文件，成功修复 {success_count} 个")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 如果提供了参数，使用参数作为文件或目录路径
        path = sys.argv[1]
        
        if os.path.isdir(path):
            print(f"正在处理目录: {path}")
            process_directory(path)
        elif os.path.isfile(path):
            print(f"正在处理文件: {path}")
            fix_markdown_headings(path)
        else:
            print(f"错误: 指定的路径既不是文件也不是目录: {path}")
    else:
        # 没有参数，使用默认目录
        default_dirs = ["reports", "output"]
        for d in default_dirs:
            if os.path.exists(d) and os.path.isdir(d):
                print(f"正在处理默认目录: {d}")
                process_directory(d)
                break
        else:
            print(f"未找到默认目录: {default_dirs}")
            print("请运行: python fix_md_headings.py <file_or_directory_path>") 