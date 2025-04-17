import os
import sys
from pathlib import Path
import argparse

def fix_markdown_encoding(input_file, output_dir=None):
    """
    修复Markdown文件的编码问题，确保中文显示正常
    
    Args:
        input_file (str): 输入Markdown文件路径
        output_dir (str, optional): 输出目录，默认为当前目录
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"错误: 文件不存在: {input_file}")
        return False
    
    # 设置输出目录
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
    else:
        output_path = input_path.parent
    
    # 读取原始二进制数据
    with open(input_path, "rb") as f:
        raw_data = f.read()
    
    print(f"原始文件: {input_path}")
    print(f"文件大小: {len(raw_data)} 字节")
    
    # 尝试不同的编码读取文件
    encodings = ['utf-8', 'gbk', 'gb18030', 'latin1']
    md_content = None
    used_encoding = None
    
    for enc in encodings:
        try:
            content = raw_data.decode(enc)
            chinese_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
            print(f"尝试 {enc} 编码: 检测到 {chinese_count} 个中文字符")
            
            if chinese_count > 0:
                md_content = content
                used_encoding = enc
                break
        except UnicodeDecodeError:
            print(f"尝试 {enc} 编码: 解码失败")
    
    if not md_content:
        print("错误: 所有编码尝试均失败，无法读取文件内容")
        return False
    
    print(f"成功使用 {used_encoding} 编码读取文件")
    
    # 生成UTF-8编码的Markdown文件
    md_output_path = output_path / f"{input_path.stem}_fixed.md"
    with open(md_output_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"已生成修复后的Markdown文件: {md_output_path}")
    
    # 生成HTML文件
    try:
        import markdown
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{input_path.stem}</title>
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
{markdown.markdown(md_content)}
</body>
</html>
"""
        html_output_path = output_path / f"{input_path.stem}_fixed.html"
        with open(html_output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"已生成HTML文件: {html_output_path}")
    except ImportError:
        print("警告: 未安装markdown模块，跳过HTML生成")
        print("提示: 可通过运行 'pip install markdown' 安装")
    
    # 生成纯文本文件
    txt_output_path = output_path / f"{input_path.stem}_fixed.txt"
    with open(txt_output_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"已生成文本文件: {txt_output_path}")
    print("文件修复完成")
    return True

def main():
    parser = argparse.ArgumentParser(description="修复Markdown文件的编码问题")
    parser.add_argument("input_file", help="输入Markdown文件路径")
    parser.add_argument("-o", "--output-dir", help="输出目录，默认为与输入文件相同的目录")
    args = parser.parse_args()
    
    success = fix_markdown_encoding(args.input_file, args.output_dir)
    if success:
        print("处理成功")
    else:
        print("处理失败")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 没有参数时，自动处理测试文件
        print("未提供参数，使用默认测试文件")
        test_file = "test_reports/report.md"
        if Path(test_file).exists():
            fix_markdown_encoding(test_file)
        else:
            print(f"测试文件不存在: {test_file}")
    else:
        main() 