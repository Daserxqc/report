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

def fix_directory_encoding(directory_path, file_pattern="*.md", add_bom=True):
    """
    修复目录中所有文件的编码问题
    
    Args:
        directory_path (str): 要处理的目录路径 
        file_pattern (str): 文件匹配模式，默认处理所有markdown文件
        add_bom (bool): 是否添加BOM标记
        
    Returns:
        dict: 处理结果统计
    """
    print(f"正在处理目录: {directory_path} 中的 {file_pattern} 文件")
    
    directory = Path(directory_path)
    if not directory.exists() or not directory.is_dir():
        print(f"错误: 目录不存在或不是有效目录: {directory_path}")
        return {"error": "目录不存在", "processed": 0, "fixed": 0}
    
    # 获取所有匹配的文件
    files = list(directory.glob(file_pattern))
    print(f"找到 {len(files)} 个匹配的文件")
    
    results = {
        "processed": len(files),
        "fixed": 0,
        "already_good": 0,
        "failed": 0,
        "details": []
    }
    
    for file_path in files:
        print(f"处理文件: {file_path.name}")
        
        # 读取原始二进制内容
        with open(file_path, "rb") as f:
            raw_data = f.read()
        
        # 检查是否已有BOM
        has_bom = raw_data.startswith(b'\xef\xbb\xbf')
        
        # 如果已有BOM且不需要修改，则跳过
        if has_bom and not add_bom:
            print(f"  文件已有BOM标记，跳过处理: {file_path.name}")
            results["already_good"] += 1
            results["details"].append({
                "file": str(file_path),
                "status": "skipped",
                "reason": "already has BOM"
            })
            continue
        
        # 尝试不同编码读取
        success = False
        for encoding in ['utf-8', 'gbk', 'gb18030', 'latin1']:
            try:
                content = raw_data.decode(encoding)
                chinese_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
                
                # 创建备份
                backup_path = file_path.with_name(f"{file_path.stem}_backup{file_path.suffix}")
                with open(backup_path, "wb") as f:
                    f.write(raw_data)
                
                # 使用UTF-8-SIG重新保存
                with open(file_path, "w", encoding="utf-8-sig" if add_bom else "utf-8") as f:
                    f.write(content)
                
                # 验证
                with open(file_path, "r", encoding="utf-8-sig" if add_bom else "utf-8") as f:
                    verified_content = f.read()
                    verified_chinese = sum(1 for c in verified_content if '\u4e00' <= c <= '\u9fff')
                
                print(f"  成功使用 {encoding} 解码并重新保存，中文字符: {chinese_count} -> {verified_chinese}")
                results["fixed"] += 1
                results["details"].append({
                    "file": str(file_path),
                    "status": "fixed",
                    "original_encoding": encoding,
                    "chinese_chars": chinese_count,
                    "verified_chars": verified_chinese
                })
                success = True
                break
            except UnicodeDecodeError:
                continue
        
        if not success:
            print(f"  无法修复文件 {file_path.name}，所有编码尝试均失败")
            results["failed"] += 1
            results["details"].append({
                "file": str(file_path),
                "status": "failed",
                "reason": "encoding detection failed"
            })
    
    print(f"\n处理完成: 总共 {results['processed']} 个文件")
    print(f"  - 已修复: {results['fixed']} 个")
    print(f"  - 无需修复: {results['already_good']} 个")
    print(f"  - 修复失败: {results['failed']} 个")
    
    return results

if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) > 1:
        # 如果提供了参数，使用参数作为报告目录路径
        report_dir = sys.argv[1]
        print(f"正在处理目录: {report_dir}")
        fix_directory_encoding(report_dir)
    else:
        # 没有参数，使用默认目录
        default_dirs = ["reports", "output"]
        for d in default_dirs:
            if Path(d).exists():
                print(f"正在处理默认目录: {d}")
                fix_directory_encoding(d)
                break
        else:
            print(f"未找到默认目录: {default_dirs}")
            print("请运行: python report_utils.py <reports_directory>")
