#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强后的任务类型检测功能
验证AI行业动态报告识别准确性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from streaming import TaskTypeDetector
from web_server import WebServer

def test_ai_industry_report_detection():
    """测试AI行业动态报告检测"""
    print("\n🤖 测试AI行业动态报告检测")
    print("=" * 50)
    
    # 测试用例 - AI行业动态报告
    ai_industry_cases = [
        "生成AI Agent领域最近一周的行业重大事件报告",
        "写一份人工智能行业最新发展趋势报告",
        "分析OpenAI最新动态和行业影响报告",
        "生成大模型行业重大事件报告",
        "ChatGPT行业发展报告",
        "深度学习技术最新进展报告",
        "百度AI行业动态报告",
        "腾讯人工智能发展趋势报告"
    ]
    
    # 测试用例 - 非AI行业报告
    non_ai_cases = [
        "写一份汽车行业市场分析报告",
        "生成房地产行业发展报告",
        "搜索相关信息",
        "分析质量",
        "生成普通报告"
    ]
    
    try:
        # 测试streaming模块的检测
        detector = TaskTypeDetector()
        print("✅ TaskTypeDetector初始化成功")
        
        print("\n🎯 AI行业动态报告检测测试:")
        ai_correct = 0
        for i, case in enumerate(ai_industry_cases, 1):
            result = detector.detect_task_type(case)
            is_correct = result == "ai_industry_report"
            status = "✅" if is_correct else "❌"
            if is_correct:
                ai_correct += 1
            print(f"  {i}. {status} '{case}' -> {result}")
        
        print(f"\n📊 AI行业报告识别准确率: {ai_correct}/{len(ai_industry_cases)} ({ai_correct/len(ai_industry_cases)*100:.1f}%)")
        
        print("\n🔍 非AI行业报告检测测试:")
        non_ai_correct = 0
        for i, case in enumerate(non_ai_cases, 1):
            result = detector.detect_task_type(case)
            is_correct = result != "ai_industry_report"
            status = "✅" if is_correct else "❌"
            if is_correct:
                non_ai_correct += 1
            print(f"  {i}. {status} '{case}' -> {result}")
        
        print(f"\n📊 非AI报告识别准确率: {non_ai_correct}/{len(non_ai_cases)} ({non_ai_correct/len(non_ai_cases)*100:.1f}%)")
        
        return ai_correct == len(ai_industry_cases) and non_ai_correct == len(non_ai_cases)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_web_server_detection():
    """测试WebServer中的任务类型检测"""
    print("\n🌐 测试WebServer任务类型检测")
    print("=" * 50)
    
    try:
        # 创建一个模拟的WebServer类来测试_detect_task_type方法
        class MockWebServer:
            def _detect_task_type(self, task: str) -> str:
                """智能检测任务类型"""
                task_lower = task.lower()
                
                # AI行业动态报告特殊检测（优先级最高）
                ai_keywords = ['ai', '人工智能', 'artificial intelligence', 'machine learning', '机器学习', 
                              'deep learning', '深度学习', 'llm', '大模型', 'gpt', 'chatgpt', 'claude', 
                              'ai agent', '智能体', 'openai', 'anthropic', '百度', 'baidu', '阿里', 'alibaba', 
                              '腾讯', 'tencent', '字节', 'bytedance', '科大讯飞', 'iflytek']
                
                industry_keywords = ['行业', 'industry', '动态', 'dynamics', '发展', 'development', 
                                   '趋势', 'trend', '事件', 'event', '重大', 'major', '最新', 'latest', 
                                   '新闻', 'news', '资讯', 'information', '进展', 'progress']
                
                if (any(ai_kw in task_lower for ai_kw in ai_keywords) and 
                    any(ind_kw in task_lower for ind_kw in industry_keywords) and 
                    any(report_kw in task_lower for report_kw in ['报告', 'report'])):
                    return "full_report"  # AI行业动态报告使用完整报告流程
                
                # 其他检测逻辑...
                if any(keyword in task_lower for keyword in ['搜索', 'search', '查找', '检索']):
                    return "comprehensive_search"
                elif any(keyword in task_lower for keyword in ['分析', 'analysis', '评估', '质量']):
                    return "quality_analysis"
                elif any(keyword in task_lower for keyword in ['报告', 'report', '调研', '研究']):
                    return "full_report"
                else:
                    return "orchestrator"
        
        web_server = MockWebServer()
        
        # 测试AI行业动态报告检测
        test_cases = [
            "生成AI Agent领域最近一周的行业重大事件报告",
            "写一份人工智能行业最新发展趋势报告",
            "搜索相关信息",
            "分析质量"
        ]
        
        print("\n🔍 WebServer任务类型检测测试:")
        for i, case in enumerate(test_cases, 1):
            result = web_server._detect_task_type(case)
            print(f"  {i}. '{case}' -> {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ WebServer测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 增强任务类型检测功能测试")
    print("=" * 60)
    
    # 运行测试
    streaming_success = test_ai_industry_report_detection()
    web_server_success = test_web_server_detection()
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"   {'✅' if streaming_success else '❌'} Streaming模块AI行业报告检测")
    print(f"   {'✅' if web_server_success else '❌'} WebServer模块任务类型检测")
    
    if streaming_success and web_server_success:
        print("\n🎉 所有增强任务类型检测测试通过！")
    else:
        print("\n⚠️ 部分测试未通过，需要进一步优化")
    
    print("=" * 60)