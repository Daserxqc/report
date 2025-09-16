#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的MCP功能
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import orchestrator_mcp

def test_complete_mcp():
    """测试完整的MCP功能"""
    print("🧪 测试完整的MCP功能")
    print("=" * 60)
    
    # 测试参数
    task = "生成式人工智能+教育洞察分析报告"
    task_type = "insight_report"
    topic = "生成式人工智能+教育"
    
    print(f"📋 任务: {task}")
    print(f"📋 任务类型: {task_type}")
    print(f"📋 主题: {topic}")
    print()
    
    try:
        # 调用orchestrator_mcp函数，设置参数只生成大纲
        print("🚀 开始调用orchestrator_mcp函数...")
        result = orchestrator_mcp(
            task=task,
            task_type=task_type,
            topic=topic,
            report_type="insight_report",
            user_requirements="",
            max_sections=6,
            enable_parallel=False,
            debug_mode=True,
            auto_confirm=True,  # 自动确认，避免交互
            max_iterations=1,   # 限制迭代次数
            days=1             # 限制搜索范围
        )
        
        print("✅ MCP调用完成!")
        print(f"🔍 返回结果类型: {type(result)}")
        
        if isinstance(result, str):
            print("📋 返回的文本内容（前500字符）:")
            print(result[:500] + "..." if len(result) > 500 else result)
        elif isinstance(result, dict):
            print("📋 返回的字典内容:")
            for key, value in result.items():
                print(f"  {key}: {str(value)[:100]}...")
        
        print("\n🎉 测试完成!")
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_complete_mcp()