# 报告生成工具函数
import os
from pathlib import Path

def fix_existing_reports(report_dir):
    """
    修复现有的报告文件
    
    Args:
        report_dir (str): 报告目录路径
    """
    # 获取所有.md文件
    report_dir = Path(report_dir)
    report_files = list(report_dir.glob("*.md"))
    
    if not report_files:
        print(f"未在 {report_dir} 中找到任何.md文件")
        return
    
    print(f"找到 {len(report_files)} 个Markdown文件")
    
    fixed_count = 0
    for file_path in report_files:
        if "fixed" in file_path.name:
            print(f"跳过已修复的文件: {file_path.name}")
            continue
            
        print(f"处理文件: {file_path.name}")
        
        # 读取原始二进制内容
        with open(file_path, "rb") as f:
            raw_data = f.read()
            
        # 尝试不同编码读取
        success = False
        for encoding in ['utf-8', 'gbk', 'gb18030', 'latin1']:
            try:
                content = raw_data.decode(encoding)
                chinese_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
                
                if chinese_count > 0:
                    print(f"  使用{encoding}解码成功，检测到{chinese_count}个中文字符")
                    
                    # 创建修复后的文件
                    fixed_path = file_path.with_name(f"{file_path.stem}_fixed.md")
                    with open(fixed_path, "w", encoding="utf-8-sig") as f:
                        f.write(content)
                        
                    print(f"  已修复并保存为: {fixed_path}")
                    fixed_count += 1
                    success = True
                    break
            except UnicodeDecodeError:
                continue
        
        if not success:
            print(f"  无法修复文件 {file_path.name}，所有编码尝试均失败")
            
    print(f"\n共处理了 {len(report_files)} 个文件，成功修复 {fixed_count} 个")

def safe_save_report(report_content, filename):
    """
    安全保存报告内容到文件，确保中文字符正确编码
    
    Args:
        report_content (str): 报告内容
        filename (str): 文件名
        
    Returns:
        bool: 保存是否成功
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        
        # 验证内容中的中文字符
        chinese_count = sum(1 for c in report_content if '\u4e00' <= c <= '\u9fff')
        print(f"报告包含 {chinese_count} 个中文字符")
        
        # 确保使用UTF-8-SIG (带BOM标记)编码保存
        with open(filename, "w", encoding="utf-8-sig") as f:
            f.write(report_content)
        print(f"报告已保存: {filename} ({os.path.getsize(filename)} 字节)")
        
        # 验证文件内容
        with open(filename, "r", encoding="utf-8-sig") as f:
            content = f.read()
            read_chinese = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
            print(f"验证成功: 写入{chinese_count}个中文字符，读取到{read_chinese}个中文字符")
            
        return True
    except Exception as e:
        print(f"保存报告失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False
