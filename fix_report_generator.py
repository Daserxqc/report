import os
import sys
import re
from pathlib import Path

def fix_markdown_encoding_issues():
    """
    修复主应用中Markdown报告生成的编码问题
    """
    print("\n" + "=" * 60)
    print("修复报告生成中的编码问题")
    print("=" * 60 + "\n")
    
    # 1. 修复 _format_fallback_results 方法
    print("1. 创建解决方案...")
    
    solution = """以下是解决报告生成中文显示乱码问题的方法:

1. 确保在写文件时明确指定UTF-8编码:

```python
# 写入报告文件时
with open(report_path, "w", encoding="utf-8-sig") as f:  # 使用带BOM的UTF-8
    f.write(content)
```

2. 在tavily_collector.py的_format_fallback_results方法中添加编码处理:

```python
def _format_fallback_results(self, insights_articles):
    # ... 现有代码 ...
    
    # 转换为统一的报告格式
    report_content = f"# {insights_articles[0].get('topic', '行业')}洞察报告\\n\\n"
    
    for article in insights_articles:
        report_content += f"## {article['title']}\\n\\n"
        report_content += f"**来源**: {article['source']} | **日期**: {article['published']} | **作者**: {', '.join(article['authors'])}\\n\\n"
        report_content += f"{article['content']}\\n\\n"
        report_content += f"**链接**: [{article['url']}]({article['url']})\\n\\n"
    
    # 返回前验证中文字符
    chinese_count = sum(1 for c in report_content if '\\u4e00' <= c <= '\\u9fff')
    print(f"报告中文字符数: {chinese_count}")
    
    return {
        "content": report_content,
        "sources": [{"title": article["title"], "url": article["url"]} for article in insights_articles]
    }
```

3. 在report_generator.py中保存文件时添加编码处理:

```python
def save_report(report_content, filename):
    try:
        # 确保使用UTF-8-SIG (带BOM标记)编码保存
        with open(filename, "w", encoding="utf-8-sig") as f:
            f.write(report_content)
        print(f"报告已保存: {filename}")
        
        # 验证文件内容
        with open(filename, "r", encoding="utf-8-sig") as f:
            content = f.read()
            chinese_count = sum(1 for c in content if '\\u4e00' <= c <= '\\u9fff')
            print(f"验证成功: 文件包含{chinese_count}个中文字符")
            
        return True
    except Exception as e:
        print(f"保存报告失败: {e}")
        return False
```

4. 检查现有的报告文件:

你可以使用以下代码修复现有的报告文件:

```python
def fix_existing_reports(report_dir):
    # 获取所有.md文件
    report_files = list(Path(report_dir).glob("*.md"))
    
    for file_path in report_files:
        print(f"处理文件: {file_path}")
        
        # 读取原始二进制内容
        with open(file_path, "rb") as f:
            raw_data = f.read()
            
        # 尝试不同编码读取
        for encoding in ['utf-8', 'gbk', 'gb18030', 'latin1']:
            try:
                content = raw_data.decode(encoding)
                chinese_count = sum(1 for c in content if '\\u4e00' <= c <= '\\u9fff')
                
                if chinese_count > 0:
                    print(f"  使用{encoding}解码成功，检测到{chinese_count}个中文字符")
                    
                    # 创建修复后的文件
                    fixed_path = file_path.with_name(f"{file_path.stem}_fixed.md")
                    with open(fixed_path, "w", encoding="utf-8-sig") as f:
                        f.write(content)
                        
                    print(f"  已修复并保存为: {fixed_path}")
                    break
            except UnicodeDecodeError:
                continue
```

这些修改应该能够解决中文显示乱码的问题。"""
    
    # 2. 创建修复工具
    print("2. 实现修复工具函数...")
    
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
    
    # 3. 为report_generator.py创建修复后的文件写入函数
    print("3. 创建修复后的文件写入函数...")
    
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
    
    # 4. 输出解决方案和工具函数到文件
    print("4. 保存解决方案和工具函数...")
    
    with open("report_encoding_solution.md", "w", encoding="utf-8") as f:
        f.write(solution)
    print(f"解决方案已保存到 report_encoding_solution.md")
    
    with open("report_utils.py", "w", encoding="utf-8") as f:
        f.write("""# 报告生成工具函数
import os
from pathlib import Path

def fix_existing_reports(report_dir):
    \"\"\"
    修复现有的报告文件
    
    Args:
        report_dir (str): 报告目录路径
    \"\"\"
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
                chinese_count = sum(1 for c in content if '\\u4e00' <= c <= '\\u9fff')
                
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
            
    print(f"\\n共处理了 {len(report_files)} 个文件，成功修复 {fixed_count} 个")

def safe_save_report(report_content, filename):
    \"\"\"
    安全保存报告内容到文件，确保中文字符正确编码
    
    Args:
        report_content (str): 报告内容
        filename (str): 文件名
        
    Returns:
        bool: 保存是否成功
    \"\"\"
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        
        # 验证内容中的中文字符
        chinese_count = sum(1 for c in report_content if '\\u4e00' <= c <= '\\u9fff')
        print(f"报告包含 {chinese_count} 个中文字符")
        
        # 确保使用UTF-8-SIG (带BOM标记)编码保存
        with open(filename, "w", encoding="utf-8-sig") as f:
            f.write(report_content)
        print(f"报告已保存: {filename} ({os.path.getsize(filename)} 字节)")
        
        # 验证文件内容
        with open(filename, "r", encoding="utf-8-sig") as f:
            content = f.read()
            read_chinese = sum(1 for c in content if '\\u4e00' <= c <= '\\u9fff')
            print(f"验证成功: 写入{chinese_count}个中文字符，读取到{read_chinese}个中文字符")
            
        return True
    except Exception as e:
        print(f"保存报告失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False
""")
    print(f"工具函数已保存到 report_utils.py")
    
    # 5. 测试工具函数
    print("\n5. 测试修复功能...")
    reports_dir = Path("test_reports")
    if reports_dir.exists():
        fix_existing_reports("test_reports")
    else:
        print(f"目录 {reports_dir} 不存在，跳过测试")
    
    print("\n解决方案已完成，您可以:")
    print("1. 在您的主应用中导入并使用 report_utils.py 中的函数")
    print("2. 参考 report_encoding_solution.md 中的建议修改代码")
    print("3. 使用 fix_existing_reports() 函数修复已生成的报告文件")
    
if __name__ == "__main__":
    fix_markdown_encoding_issues() 