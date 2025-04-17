import os
from pathlib import Path

def check_file_encoding():
    """
    检查文件编码问题并尝试修复
    """
    print("开始检查文件编码问题...")
    
    # 检查report.md文件
    report_path = Path("test_reports/report.md")
    
    if not report_path.exists():
        print(f"错误: 文件 {report_path} 不存在")
        return
    
    # 读取文件内容 (不指定编码)
    with open(report_path, "rb") as f:
        raw_bytes = f.read()
    
    print(f"文件大小: {len(raw_bytes)} 字节")
    print(f"文件开头16字节: {raw_bytes[:16]}")
    
    # 通过BOM检测编码
    if raw_bytes.startswith(b'\xef\xbb\xbf'):
        print("检测到UTF-8 BOM编码")
        encoding = 'utf-8-sig'
    else:
        print("未检测到BOM，尝试各种编码...")
    
    # 尝试不同的编码
    encodings = [
        'utf-8', 'gbk', 'gb2312', 'gb18030', 
        'latin1', 'cp1252', 'iso-8859-1'
    ]
    
    print("\n尝试不同编码读取文件:")
    for enc in encodings:
        try:
            with open(report_path, "r", encoding=enc) as f:
                content = f.read()
                chinese_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
                print(f"  {enc}: 检测到{chinese_count}个中文字符 (样本: {content[:30]}...)")
        except UnicodeDecodeError:
            print(f"  {enc}: 解码错误")
    
    # 尝试写入新的测试文件
    print("\n创建新的测试文件:")
    test_text = "# 元宇宙行业洞察报告\n\n这是一个测试文件，包含中文字符。"
    
    for enc in ['utf-8', 'gbk', 'gb18030']:
        test_path = Path(f"test_encoding_{enc}.txt")
        try:
            with open(test_path, "w", encoding=enc) as f:
                f.write(test_text)
            
            # 重新读取
            with open(test_path, "r", encoding=enc) as f:
                content = f.read()
            
            print(f"  {enc}编码: 写入并读取成功 (样本: {content[:30]}...)")
        except Exception as e:
            print(f"  {enc}编码: 出错 - {str(e)}")
    
    # 尝试修复report.md文件
    print("\n尝试修复report.md文件:")
    # 首先尝试用不同的编码读取
    fixed = False
    for read_enc in encodings:
        try:
            with open(report_path, "r", encoding=read_enc) as f:
                content = f.read()
                chinese_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
                if chinese_count > 0:
                    print(f"  使用{read_enc}编码成功读取，检测到{chinese_count}个中文字符")
                    
                    # 写入UTF-8编码的新文件
                    fixed_path = Path("test_reports/report_fixed.md")
                    with open(fixed_path, "w", encoding="utf-8") as f_out:
                        f_out.write(content)
                    
                    # 验证
                    with open(fixed_path, "r", encoding="utf-8") as f_check:
                        fixed_content = f_check.read()
                        fixed_chinese = sum(1 for c in fixed_content if '\u4e00' <= c <= '\u9fff')
                        
                    print(f"  修复文件已保存为: {fixed_path}")
                    print(f"  修复后中文字符: {fixed_chinese}")
                    fixed = True
                    break
        except UnicodeDecodeError:
            continue
    
    if not fixed:
        print("  无法修复文件，所有编码均解码失败")
    
    print("\n编码检查完成")

if __name__ == "__main__":
    check_file_encoding() 