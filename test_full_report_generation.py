#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整报告生成测试脚本
测试增强后的MCP工具生成完整报告并保存到本地文件
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_tools import content_writer_mcp, get_tool_registry
from streaming import StreamingProgressReporter
from search_manager import SearchEngineManager

def test_full_report_generation():
    """
    测试完整报告生成功能
    """
    print("=" * 60)
    print("开始测试完整报告生成功能")
    print("=" * 60)
    
    # 初始化搜索引擎管理器
    print("\n🚀 初始化搜索引擎管理器...")
    search_manager = SearchEngineManager()
    tool_registry = get_tool_registry(search_manager)
    print("✅ 搜索引擎管理器初始化完成\n")
    
    # 测试主题
    test_topic = "人工智能在医疗诊断中的应用与发展趋势"
    
    # 创建进度报告器
    class TestProgressReporter(StreamingProgressReporter):
        def report_progress(self, stage, message, progress_percentage=None, details=None):
            if progress_percentage:
                print(f"[{progress_percentage}%] {stage}: {message}")
            else:
                print(f"[进行中] {stage}: {message}")
    
    reporter = TestProgressReporter()
    
    try:
        print(f"\n测试主题: {test_topic}")
        print("开始生成报告...\n")
        
        # 调用增强的MCP工具生成报告
        result = content_writer_mcp(
            topic=test_topic,
            search_results=None,  # 让工具自己搜索
            session_id="test_session_001",
            content_style="enhanced",  # 使用增强模式
            min_word_count=8000  # 最小字数要求
        )
        
        if result and result.get('success'):
            content = result.get('content', '')
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"AI医疗诊断报告_{timestamp}.md"
            filepath = os.path.join(os.path.dirname(__file__), filename)
            
            # 保存报告到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 统计信息
            word_count = len(content)
            line_count = content.count('\n') + 1
            section_count = content.count('##')
            
            print("\n" + "=" * 60)
            print("报告生成完成！")
            print("=" * 60)
            print(f"文件保存位置: {filepath}")
            print(f"报告总字数: {word_count:,} 字符")
            print(f"报告总行数: {line_count:,} 行")
            print(f"章节数量: {section_count} 个")
            
            # 显示报告开头部分
            print("\n报告内容预览:")
            print("-" * 40)
            preview_lines = content.split('\n')[:20]
            for line in preview_lines:
                print(line)
            if len(content.split('\n')) > 20:
                print("...")
                print(f"(还有 {len(content.split('\n')) - 20} 行内容)")
            
            # 质量评估
            quality_score = assess_report_quality(content)
            print(f"\n报告质量评分: {quality_score}/10")
            
            return True
            
        else:
            print("报告生成失败!")
            if result:
                print(f"错误信息: {result.get('error', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def assess_report_quality(content):
    """
    评估报告质量
    """
    score = 0
    
    # 长度评分 (0-3分)
    word_count = len(content)
    if word_count >= 8000:
        score += 3
    elif word_count >= 5000:
        score += 2
    elif word_count >= 3000:
        score += 1
    
    # 结构评分 (0-2分)
    section_count = content.count('##')
    if section_count >= 8:
        score += 2
    elif section_count >= 5:
        score += 1
    
    # 内容深度评分 (0-3分)
    depth_indicators = ['分析', '趋势', '挑战', '机遇', '风险', '建议', '数据', '市场']
    depth_score = sum(1 for indicator in depth_indicators if indicator in content)
    if depth_score >= 6:
        score += 3
    elif depth_score >= 4:
        score += 2
    elif depth_score >= 2:
        score += 1
    
    # 专业性评分 (0-2分)
    professional_terms = ['技术', '行业', '发展', '应用', '创新', '解决方案']
    prof_score = sum(1 for term in professional_terms if term in content)
    if prof_score >= 4:
        score += 2
    elif prof_score >= 2:
        score += 1
    
    return min(score, 10)

def main():
    """
    主函数
    """
    success = test_full_report_generation()
    
    if success:
        print("\n✅ 测试成功完成！")
        print("请查看生成的报告文件以验证内容质量。")
    else:
        print("\n❌ 测试失败！")
        print("请检查错误信息并修复相关问题。")

if __name__ == "__main__":
    main()