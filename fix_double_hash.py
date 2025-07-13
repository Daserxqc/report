#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复双重#号标题问题
"""

import re
import sys
from pathlib import Path

def fix_double_hash_titles(content):
    """修复双重#号标题问题"""
    
    print("开始修复双重#号标题问题...")
    
    # 修复 ### # 标题 的格式为 ### 标题
    content = re.sub(r'^### # ', '### ', content, flags=re.MULTILINE)
    
    # 修复 ## # 标题 的格式为 ## 标题
    content = re.sub(r'^## # ', '## ', content, flags=re.MULTILINE)
    
    # 修复 #### # 标题 的格式为 #### 标题
    content = re.sub(r'^#### # ', '#### ', content, flags=re.MULTILINE)
    
    # 统计修复数量
    fixed_count = content.count('### ') - content.count('### #')
    
    print(f"修复了双重#号标题问题")
    return content

def fix_file(input_file, output_file=None):
    """修复文件"""
    
    if output_file is None:
        # 直接覆盖原文件
        output_file = input_file
    
    print(f"正在处理文件: {input_file}")
    
    # 读取文件
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复问题
    fixed_content = fix_double_hash_titles(content)
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"修复完成: {output_file}")

def main():
    if len(sys.argv) < 2:
        print("使用方法: python fix_double_hash.py <输入文件>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not Path(input_file).exists():
        print(f"错误: 文件不存在 - {input_file}")
        sys.exit(1)
    
    fix_file(input_file)

if __name__ == '__main__':
    main() 