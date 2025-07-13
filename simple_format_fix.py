#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单直接的Markdown格式修复脚本
专门处理AI生成报告中的格式问题
"""

import re
import sys
from pathlib import Path

def fix_markdown_format(content):
    """直接修复Markdown格式问题"""
    
    # 1. 移除多余的####标记（超过4个#的都改成###）
    content = re.sub(r'^#{5,}\s*', '### ', content, flags=re.MULTILINE)
    
    # 2. 标准化####标记为###标记
    content = re.sub(r'^####\s*', '### ', content, flags=re.MULTILINE)
    
    # 3. 处理中文符号标题 - 只处理明确的标题行
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        original_line = line
        stripped = line.strip()
        
        # 跳过空行
        if not stripped:
            fixed_lines.append('')
            continue
        
        # 跳过已经是标题的行
        if stripped.startswith('#'):
            fixed_lines.append(line)
            continue
        
        # 只处理很明确的中文符号标题，且行长度不超过30字符
        if len(stripped) <= 30:
            # 处理 （一）、（二）等格式
            match = re.match(r'^[（(]\s*[一二三四五六七八九十]+\s*[）)]\s*(.+)$', stripped)
            if match:
                title = match.group(1).strip()
                fixed_lines.append(f"### {title}")
                continue
            
            # 处理 <一>、<二>等格式
            match = re.match(r'^[<＜]\s*[一二三四五六七八九十]+\s*[>＞]\s*(.+)$', stripped)
            if match:
                title = match.group(1).strip()
                fixed_lines.append(f"### {title}")
                continue
            
            # 处理 【一】、【二】等格式
            match = re.match(r'^[【\[]\s*[一二三四五六七八九十]+\s*[】\]]\s*(.+)$', stripped)
            if match:
                title = match.group(1).strip()
                fixed_lines.append(f"### {title}")
                continue
        
        # 其他情况保持原样
        fixed_lines.append(original_line)
    
    content = '\n'.join(fixed_lines)
    
    # 4. 清理多余的空行
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    
    # 5. 确保标题前有空行
    content = re.sub(r'\n(#{1,6}\s[^\n]+)', r'\n\n\1', content)
    
    # 6. 移除开头的空行
    content = content.lstrip('\n')
    
    return content

def fix_file(input_file, output_file=None):
    """修复文件格式"""
    
    if output_file is None:
        path = Path(input_file)
        output_file = path.parent / f"{path.stem}_simple_fixed{path.suffix}"
    
    print(f"修复文件: {input_file}")
    
    # 读取文件
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"原文件大小: {len(content)} 字符")
    
    # 修复格式
    fixed_content = fix_markdown_format(content)
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"修复完成: {output_file}")
    print(f"修复后大小: {len(fixed_content)} 字符")
    
    # 统计修复情况
    original_headings = len(re.findall(r'^#{1,6}\s', content, re.MULTILINE))
    fixed_headings = len(re.findall(r'^#{1,6}\s', fixed_content, re.MULTILINE))
    
    print(f"标题数量: {original_headings} → {fixed_headings}")

def main():
    if len(sys.argv) < 2:
        print("使用方法: python simple_format_fix.py <输入文件> [输出文件]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(input_file).exists():
        print(f"错误: 文件不存在 - {input_file}")
        sys.exit(1)
    
    fix_file(input_file, output_file)

if __name__ == '__main__':
    main() 