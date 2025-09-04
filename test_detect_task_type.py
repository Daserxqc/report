#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试_detect_task_type函数的行为
"""

def _detect_task_type(task: str) -> str:
    """智能检测任务类型"""
    task_lower = task.lower()
    
    # 单个MCP工具关键词检测
    if any(keyword in task_lower for keyword in ['搜索', 'search', '查找', '检索']):
        if any(keyword in task_lower for keyword in ['并行', 'parallel', '多渠道']):
            return "parallel_search"
        else:
            return "comprehensive_search"
    
    elif any(keyword in task_lower for keyword in ['分析', 'analysis', '评估', '质量']):
        if any(keyword in task_lower for keyword in ['意图', 'intent']):
            return "intent_analysis"
        elif any(keyword in task_lower for keyword in ['质量', 'quality']):
            return "quality_analysis"
        elif any(keyword in task_lower for keyword in ['缺口', 'gap']):
            return "gap_analysis"
        else:
            return "quality_analysis"  # 默认质量分析
    
    elif any(keyword in task_lower for keyword in ['大纲', 'outline', '结构']):
        return "outline_generation"
    
    elif any(keyword in task_lower for keyword in ['摘要', 'summary', '总结']):
        return "summary_generation"
    
    elif any(keyword in task_lower for keyword in ['内容', 'content', '写作']):
        return "content_generation"
    
    elif any(keyword in task_lower for keyword in ['查询生成', 'query generation']):
        return "query_generation"
    
    # 如果包含报告相关关键词，则为完整报告
    elif any(keyword in task_lower for keyword in ['报告', 'report', '完整', '全面', '综合', 'news_report']):
        return "full_report"
    
    # 默认为完整报告
    return "full_report"

if __name__ == "__main__":
    # 测试不同的输入
    test_cases = [
        "news_report",
        "生成AI Agent领域最近一周的行业重大事件报告",
        "搜索相关信息",
        "分析质量",
        "生成报告"
    ]
    
    print("🧪 测试_detect_task_type函数")
    print("=" * 50)
    
    for test_case in test_cases:
        result = _detect_task_type(test_case)
        print(f"输入: '{test_case}' -> 输出: '{result}'")
    
    print("\n🔍 详细分析 'news_report':")
    task_lower = "news_report".lower()
    print(f"task_lower: '{task_lower}'")
    
    # 检查每个条件
    search_keywords = ['搜索', 'search', '查找', '检索']
    analysis_keywords = ['分析', 'analysis', '评估', '质量']
    report_keywords = ['报告', 'report', '完整', '全面', '综合', 'news_report']
    
    print(f"搜索关键词匹配: {any(keyword in task_lower for keyword in search_keywords)}")
    print(f"分析关键词匹配: {any(keyword in task_lower for keyword in analysis_keywords)}")
    print(f"报告关键词匹配: {any(keyword in task_lower for keyword in report_keywords)}")
    
    for keyword in report_keywords:
        if keyword in task_lower:
            print(f"匹配的关键词: '{keyword}'")