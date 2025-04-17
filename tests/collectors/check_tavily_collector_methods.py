from collectors.tavily_collector import TavilyCollector
import os
from pathlib import Path

def check_report_generation_methods():
    """
    检查Tavily收集器中处理报告生成的关键方法
    """
    print("\n" + "=" * 60)
    print("检查Tavily收集器中报告生成相关的方法")
    print("=" * 60 + "\n")
    
    # 1. 创建实例
    print("1. 创建TavilyCollector实例...")
    collector = TavilyCollector()
    
    # 2. 检查有哪些关键方法
    print("\n2. 检查关键方法:")
    methods = [method for method in dir(collector) if not method.startswith('_') or method == '_direct_integrate_results']
    for method in methods:
        print(f"  - {method}")
    
    # 3. 测试行业洞察生成
    print("\n3. 测试行业洞察生成:")
    topic = "元宇宙"
    
    # 先生成备用内容 (不使用API)
    print("  生成备用内容...")
    insights = collector.generate_industry_insights_fallback(topic)
    print(f"  生成了 {len(insights)} 条内容")
    
    # 检查返回的内容格式
    for item in insights[:2]:  # 只打印前两条
        print(f"  · 标题: {item.get('title', 'N/A')}")
        content_preview = item.get('content', '')[:50] + '...' if item.get('content') else 'N/A'
        print(f"    内容: {content_preview}")
    
    # 4. 测试格式化方法
    print("\n4. 测试_format_fallback_results方法:")
    output_dir = Path("test_reports")
    output_dir.mkdir(exist_ok=True)
    
    # 调用格式化方法
    formatted_result = collector._format_fallback_results(insights)
    print(f"  返回格式: {type(formatted_result)}")
    print(f"  内容类型: {list(formatted_result.keys())}")
    
    # 5. 保存结果到文件
    print("\n5. 保存结果到文件:")
    markdown_content = formatted_result.get('content', '')
    chinese_chars = sum(1 for c in markdown_content if '\u4e00' <= c <= '\u9fff')
    print(f"  内容长度: {len(markdown_content)} 字符")
    print(f"  中文字符: {chinese_chars} 个")
    
    # 直接保存UTF-8文件
    file_path = output_dir / "collector_generated.md"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"  文件已保存: {file_path}, 大小: {os.path.getsize(file_path)} 字节")
    except Exception as e:
        print(f"  保存失败: {str(e)}")
    
    # 6. 读取保存的文件
    print("\n6. 验证保存的文件:")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        read_chinese = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
        print(f"  读取文件长度: {len(content)} 字符")
        print(f"  中文字符数量: {read_chinese} 个")
        if read_chinese == chinese_chars:
            print("  ✓ 文件内容完整性验证成功")
        else:
            print(f"  ✗ 文件内容可能损坏 (写入: {chinese_chars}, 读取: {read_chinese})")
    except Exception as e:
        print(f"  读取失败: {str(e)}")
    
    print("\n检查完成")

if __name__ == "__main__":
    check_report_generation_methods() 