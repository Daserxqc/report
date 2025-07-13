#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复Mermaid图表缺少结束标记的问题
"""

import os
import sys
import re
import argparse


def fix_mermaid_syntax(content):
    """修复Mermaid图表的语法问题"""
    
    # 查找所有的 ```mermaid 开始标记
    lines = content.split('\n')
    fixed_lines = []
    in_mermaid_block = False
    mermaid_start_line = -1
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 检查是否是mermaid块的开始
        if stripped == '```mermaid':
            in_mermaid_block = True
            mermaid_start_line = i
            fixed_lines.append(line)
            continue
        
        # 如果在mermaid块中，检查是否是结束标记
        if in_mermaid_block:
            # 如果遇到结束标记
            if stripped == '```':
                in_mermaid_block = False
                fixed_lines.append(line)
                continue
            
            # 如果遇到以 # 开头的行（可能是markdown标题），说明mermaid块没有正确结束
            if stripped.startswith('#'):
                print(f"在第 {i+1} 行发现未关闭的Mermaid块（开始于第 {mermaid_start_line+1} 行）")
                print(f"在第 {i} 行插入缺失的结束标记")
                
                # 插入缺失的结束标记
                fixed_lines.append('```')
                fixed_lines.append('')  # 添加空行
                fixed_lines.append(line)
                in_mermaid_block = False
                continue
        
        fixed_lines.append(line)
    
    # 如果文件结束时仍在mermaid块中，添加结束标记
    if in_mermaid_block:
        print(f"在文件结尾发现未关闭的Mermaid块（开始于第 {mermaid_start_line+1} 行）")
        print("在文件结尾添加缺失的结束标记")
        fixed_lines.append('```')
    
    return '\n'.join(fixed_lines)


def fix_report_mermaid(file_path):
    """修复报告中的Mermaid语法问题"""
    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            original_content = f.read()
        
        print(f"📖 正在读取文件: {file_path}")
        print(f"📊 原文件大小: {len(original_content)} 字符")
        
        # 创建备份
        backup_path = file_path + '.mermaid_backup'
        with open(backup_path, 'w', encoding='utf-8-sig') as f:
            f.write(original_content)
        
        print(f"💾 已创建备份文件: {backup_path}")
        
        # 修复Mermaid语法
        print("🔧 正在修复Mermaid语法问题...")
        fixed_content = fix_mermaid_syntax(original_content)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"✅ 修复完成: {file_path}")
        print(f"📊 修复后大小: {len(fixed_content)} 字符")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复时出错: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='🔧 修复Mermaid图表语法问题',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python fix_mermaid_issue.py report.md
        """
    )
    
    parser.add_argument('file', type=str, help='要修复的报告文件路径')
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.exists(args.file):
        print(f"❌ 文件不存在: {args.file}")
        sys.exit(1)
    
    # 显示启动信息
    print("🔧 " + "=" * 50)
    print("🔧 修复Mermaid图表语法问题")
    print("🔧 " + "=" * 50)
    print(f"📄 文件: {args.file}")
    print("🔧 " + "=" * 50)
    
    # 执行修复
    if fix_report_mermaid(args.file):
        print("\n✅ 修复成功!")
    else:
        print("\n❌ 修复失败!")
        sys.exit(1)


if __name__ == "__main__":
    main() 