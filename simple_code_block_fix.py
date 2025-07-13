#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的代码块修复脚本 - 只移除错误的代码块标记
"""

import os
import sys
import re
import argparse


def fix_code_blocks_only(content):
    """只修复代码块标记问题，不修改其他格式"""
    
    # 1. 移除错误的 ```markdown 标记
    content = re.sub(r'^```markdown\s*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^`````markdown\s*$', '', content, flags=re.MULTILINE)
    
    # 2. 移除孤立的 ``` 标记（不是真正的代码块）
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 如果是孤立的 ``` 行
        if stripped in ['```', '`````']:
            # 检查前后是否有真正的代码内容
            has_code_before = False
            has_code_after = False
            
            # 检查前面10行
            for j in range(max(0, i-10), i):
                prev_line = lines[j].strip()
                if prev_line.startswith('```') and prev_line not in ['```', '`````']:
                    has_code_before = True
                    break
            
            # 检查后面10行
            for j in range(i+1, min(len(lines), i+11)):
                next_line = lines[j].strip()
                if next_line.startswith('```') and next_line not in ['```', '`````']:
                    has_code_after = True
                    break
            
            # 如果不是真正的代码块，就移除
            if not (has_code_before or has_code_after):
                print(f"移除孤立的代码块标记：第 {i+1} 行 '{stripped}'")
                continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def fix_report_simple(file_path):
    """简单修复报告 - 只处理代码块问题"""
    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            original_content = f.read()
        
        print(f"📖 正在读取文件: {file_path}")
        print(f"📊 原文件大小: {len(original_content)} 字符")
        
        # 创建备份
        backup_path = file_path + '.backup'
        with open(backup_path, 'w', encoding='utf-8-sig') as f:
            f.write(original_content)
        
        print(f"💾 已创建备份文件: {backup_path}")
        
        # 只修复代码块问题
        print("🔧 正在移除错误的代码块标记...")
        fixed_content = fix_code_blocks_only(original_content)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"✅ 修复完成: {file_path}")
        print(f"📊 修复后大小: {len(fixed_content)} 字符")
        
        # 统计变化
        original_lines = len(original_content.splitlines())
        fixed_lines = len(fixed_content.splitlines())
        print(f"📋 行数变化: {original_lines} → {fixed_lines}")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复时出错: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='🔧 简单修复代码块标记问题',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python simple_code_block_fix.py report.md
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
    print("🔧 简单修复代码块标记问题")
    print("🔧 " + "=" * 50)
    print(f"📄 文件: {args.file}")
    print("🔧 " + "=" * 50)
    
    # 执行修复
    if fix_report_simple(args.file):
        print("\n✅ 修复成功!")
    else:
        print("\n❌ 修复失败!")
        sys.exit(1)


if __name__ == "__main__":
    main() 