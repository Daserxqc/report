#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复Markdown文件中的代码块标记问题
专门处理错误的```markdown标记导致内容被当作代码块的问题
"""

import re
import sys
from pathlib import Path

def fix_code_block_issue(content):
    """修复代码块标记问题"""
    
    print("开始修复代码块标记问题...")
    
    # 1. 移除错误的 ```markdown 标记
    # 查找所有 ```markdown 出现的位置
    markdown_blocks = re.findall(r'```markdown', content)
    print(f"发现 {len(markdown_blocks)} 个 ```markdown 标记")
    
    # 直接移除所有的 ```markdown 标记
    content = re.sub(r'```markdown\s*\n?', '', content)
    
    # 2. 移除多余的 ``` 结束标记（如果有的话）
    # 但要保留真正的代码块（通常是三个反引号加语言名称）
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 如果是单独的 ``` 行，可能是错误的结束标记
        if stripped == '```':
            # 检查前后文，如果不是真正的代码块，就移除
            # 查看前面几行是否有代码内容
            has_code_content = False
            for j in range(max(0, i-10), i):
                if lines[j].strip().startswith('```') and lines[j].strip() != '```':
                    has_code_content = True
                    break
            
            if not has_code_content:
                # 这可能是错误的结束标记，跳过
                print(f"移除可能错误的代码块结束标记：第 {i+1} 行")
                continue
        
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # 3. 修复标题格式
    # 现在这些标题应该不在代码块中了，可以正常处理
    content = re.sub(r'^####\s*', '### ', content, flags=re.MULTILINE)
    content = re.sub(r'^#####\s*', '#### ', content, flags=re.MULTILINE)
    
    # 4. 处理中文符号标题（现在应该能正常识别了）
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        original_line = line
        stripped = line.strip()
        
        if not stripped:
            fixed_lines.append('')
            continue
        
        # 跳过已经是标题的行
        if stripped.startswith('#'):
            fixed_lines.append(line)
            continue
        
        # 只处理短行的中文符号标题
        if len(stripped) <= 30:
            # 处理各种中文符号标题格式
            patterns = [
                (r'^[（(]\s*[一二三四五六七八九十]+\s*[）)]\s*(.+)$', '### '),
                (r'^[<＜]\s*[一二三四五六七八九十]+\s*[>＞]\s*(.+)$', '### '),
                (r'^[【\[]\s*[一二三四五六七八九十]+\s*[】\]]\s*(.+)$', '### '),
            ]
            
            converted = False
            for pattern, replacement in patterns:
                match = re.match(pattern, stripped)
                if match:
                    title = match.group(1).strip()
                    if title and len(title) <= 20:
                        fixed_lines.append(f"{replacement}{title}")
                        converted = True
                        break
            
            if not converted:
                fixed_lines.append(original_line)
        else:
            fixed_lines.append(original_line)
    
    content = '\n'.join(fixed_lines)
    
    # 5. 清理多余的空行
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    
    # 6. 确保标题前有空行
    content = re.sub(r'\n(#{1,6}\s[^\n]+)', r'\n\n\1', content)
    
    # 7. 移除开头的空行
    content = content.lstrip('\n')
    
    print("代码块标记问题修复完成！")
    return content

def fix_file(input_file, output_file=None):
    """修复文件"""
    
    if output_file is None:
        path = Path(input_file)
        output_file = path.parent / f"{path.stem}_code_block_fixed{path.suffix}"
    
    print(f"正在处理文件: {input_file}")
    
    # 读取文件
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # 尝试其他编码
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            content = f.read()
    
    print(f"原文件大小: {len(content)} 字符")
    
    # 修复问题
    fixed_content = fix_code_block_issue(content)
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"修复完成，输出文件: {output_file}")
    print(f"修复后大小: {len(fixed_content)} 字符")
    
    # 统计修复情况
    original_code_blocks = len(re.findall(r'```', content))
    fixed_code_blocks = len(re.findall(r'```', fixed_content))
    original_headings = len(re.findall(r'^#{1,6}\s', content, re.MULTILINE))
    fixed_headings = len(re.findall(r'^#{1,6}\s', fixed_content, re.MULTILINE))
    
    print(f"代码块标记: {original_code_blocks} → {fixed_code_blocks}")
    print(f"标题数量: {original_headings} → {fixed_headings}")

def main():
    if len(sys.argv) < 2:
        print("使用方法: python fix_code_block_issue.py <输入文件> [输出文件]")
        print("例如: python fix_code_block_issue.py reports/生成式大模型_outline_report_20250710.md")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(input_file).exists():
        print(f"错误: 文件不存在 - {input_file}")
        sys.exit(1)
    
    fix_file(input_file, output_file)

if __name__ == '__main__':
    main() 