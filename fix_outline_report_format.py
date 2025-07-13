#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大纲报告Markdown格式修复脚本

专门用于修复AI生成的大纲报告中的Markdown格式问题，
采用保守的方法，只修复明确的格式问题。

使用方法：
python fix_outline_report_format.py input_file.md [output_file.md]
"""

import os
import re
import sys
import argparse
from pathlib import Path

def clean_invisible_characters(text):
    """清理文本中的不可见字符和特殊空格"""
    # 替换各种空格字符为标准空格
    text = re.sub(r'[\u00A0\u1680\u2000-\u200B\u202F\u205F\u3000\uFEFF]', ' ', text)
    
    # 移除零宽度字符
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
    
    # 标准化换行符
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    return text

def fix_simple_heading_format(text):
    """修复简单的标题格式问题 - 采用保守方法"""
    lines = text.split('\n')
    fixed_lines = []
    
    for line in lines:
        original_line = line
        stripped = line.strip()
        
        if not stripped:
            fixed_lines.append('')
            continue
        
        # 只处理明确的中文符号标题格式，且这些行看起来确实像标题
        # 1. 检查是否是独立的一行（前后有空行或者很短）
        # 2. 不包含过多的标点符号
        # 3. 长度适中（不超过50个字符）
        
        is_likely_heading = (
            len(stripped) <= 50 and  # 不太长
            stripped.count('，') <= 2 and  # 不包含太多逗号
            stripped.count('。') <= 1 and  # 不包含太多句号
            not stripped.startswith('*') and  # 不是列表项
            not stripped.startswith('-') and  # 不是列表项
            not stripped.startswith('####') and  # 不是已经处理过的标题
            not stripped.startswith('###') and   # 不是已经处理过的标题
            not stripped.startswith('##') and    # 不是已经处理过的标题
            not stripped.startswith('#')         # 不是已经处理过的标题
        )
        
        if is_likely_heading:
            # 只处理非常明确的中文符号标题格式
            heading_patterns = [
                (r'^[（(]\s*[一二三四五六七八九十]+\s*[）)]\s*(.+)$', '###'),  # （一）标题
                (r'^[<＜]\s*[一二三四五六七八九十]+\s*[>＞]\s*(.+)$', '###'),  # <一>标题
                (r'^[【\[]\s*[一二三四五六七八九十]+\s*[】\]]\s*(.+)$', '###'),  # 【一】标题
            ]
            
            converted = False
            for pattern, level in heading_patterns:
                match = re.match(pattern, stripped)
                if match:
                    title = match.group(1).strip()
                    # 只有当标题内容合理时才转换
                    if title and not title.startswith('*') and len(title) <= 30:
                        fixed_lines.append(f"{level} {title}")
                        converted = True
                        break
            
            if not converted:
                fixed_lines.append(original_line)
        else:
            fixed_lines.append(original_line)
    
    return '\n'.join(fixed_lines)

def fix_spacing_issues(text):
    """修复空行和间距问题"""
    # 移除行尾空格
    text = re.sub(r' +$', '', text, flags=re.MULTILINE)
    
    # 标准化多个连续空行为最多两个空行
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    
    # 确保标题前有空行（但不要过多）
    text = re.sub(r'\n(#{1,6}\s[^\n]+)', r'\n\n\1', text)
    
    # 移除文件开头的多余空行
    text = text.lstrip('\n')
    
    return text

def fix_markdown_report(input_file, output_file=None):
    """修复Markdown报告格式 - 保守方法"""
    
    # 确定输出文件
    if output_file is None:
        path = Path(input_file)
        output_file = path.parent / f"{path.stem}_fixed{path.suffix}"
    
    print(f"正在处理文件: {input_file}")
    
    try:
        # 读取原文件
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        print(f"原文件大小: {len(content)} 字符")
        
        # 创建备份
        backup_file = str(Path(input_file).with_suffix('.bak'))
        with open(backup_file, 'w', encoding='utf-8-sig') as f:
            f.write(content)
        print(f"已创建备份: {backup_file}")
        
        # 应用修复步骤 - 保守方法
        print("1. 清理不可见字符...")
        content = clean_invisible_characters(content)
        
        print("2. 修复明确的标题格式...")
        content = fix_simple_heading_format(content)
        
        print("3. 修复空行和间距...")
        content = fix_spacing_issues(content)
        
        # 确保文件以换行符结束
        if not content.endswith('\n'):
            content += '\n'
        
        # 写入修复后的文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"修复完成: {output_file}")
        print(f"修复后大小: {len(content)} 字符")
        
        # 简单验证
        validate_markdown(content)
        
        return True
        
    except Exception as e:
        print(f"修复过程中出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def validate_markdown(content):
    """验证Markdown格式是否正确"""
    lines = content.split('\n')
    heading_count = 0
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#'):
            heading_count += 1
    
    print(f"✅ 检测到 {heading_count} 个标题")
    
    # 检查是否有明显的格式问题
    if '####' in content and content.count('####') > content.count('###'):
        print("⚠️ 注意：检测到较多四级标题，请检查是否过度处理")
    else:
        print("✅ 基本格式验证通过")

def main():
    parser = argparse.ArgumentParser(
        description='修复AI生成的大纲报告Markdown格式（保守方法）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python fix_outline_report_format.py report.md
  python fix_outline_report_format.py report.md fixed_report.md
  python fix_outline_report_format.py reports/*.md
        """
    )
    
    parser.add_argument('input_files', nargs='+', help='输入的Markdown文件')
    parser.add_argument('-o', '--output', help='输出文件名（仅当输入单个文件时有效）')
    parser.add_argument('--in-place', action='store_true', help='直接修改原文件')
    
    args = parser.parse_args()
    
    if len(args.input_files) == 1 and not args.in_place:
        # 单个文件处理
        input_file = args.input_files[0]
        output_file = args.output if args.output else None
        
        if not os.path.exists(input_file):
            print(f"错误: 文件不存在 - {input_file}")
            sys.exit(1)
        
        success = fix_markdown_report(input_file, output_file)
        sys.exit(0 if success else 1)
        
    else:
        # 批量处理或原地修改
        success_count = 0
        total_count = len(args.input_files)
        
        for input_file in args.input_files:
            if not os.path.exists(input_file):
                print(f"跳过不存在的文件: {input_file}")
                continue
            
            print(f"\n处理文件 {success_count + 1}/{total_count}: {input_file}")
            
            if args.in_place:
                output_file = input_file
            else:
                path = Path(input_file)
                output_file = path.parent / f"{path.stem}_fixed{path.suffix}"
            
            if fix_markdown_report(input_file, output_file):
                success_count += 1
        
        print(f"\n处理完成: {success_count}/{total_count} 个文件成功修复")

if __name__ == '__main__':
    main() 