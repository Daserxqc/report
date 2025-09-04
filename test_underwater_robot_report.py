#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试生成水下特种机器人行业洞察报告
"""

import requests
import json
from datetime import datetime
import os

def test_underwater_robot_report():
    """测试生成水下特种机器人的行业洞察报告"""
    print("🤖 开始测试生成水下特种机器人行业洞察报告...")
    
    # API请求数据
    test_data = {
        "task": "生成水下特种机器人的行业洞察报告",
        "task_type": "auto",
        "kwargs": {
            "days": 365,  # 不限制日期，搜索一年内的信息
            "report_type": "comprehensive",
            "include_analysis": True
        }
    }
    
    try:
        print("📡 发送API请求...")
        response = requests.post(
            "http://localhost:8001/mcp/streaming/orchestrator",
            json=test_data,
            timeout=120
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功！")
            
            # 提取关键信息
            if 'result' in result and 'result' in result['result']:
                report_data = result['result']['result']
                
                print("\n📋 报告基本信息:")
                print(f"   主题: {report_data.get('topic', 'N/A')}")
                print(f"   生成时间: {report_data.get('generated_at', 'N/A')}")
                print(f"   会话ID: {report_data.get('session_id', 'N/A')}")
                print(f"   状态: {report_data.get('status', 'N/A')}")
                
                # 搜索结果统计
                search_results = report_data.get('search_results', {})
                if isinstance(search_results, dict) and 'results' in search_results:
                    results_count = len(search_results['results'])
                    total_count = search_results.get('total_count', 0)
                    print(f"\n🔍 搜索结果统计:")
                    print(f"   获取结果数: {results_count}")
                    print(f"   总计数量: {total_count}")
                    
                    # 显示前几个搜索结果标题
                    print(f"\n📰 主要搜索结果:")
                    for i, item in enumerate(search_results['results'][:5], 1):
                        title = item.get('title', 'N/A')[:100]
                        source = item.get('source', 'N/A')
                        print(f"   {i}. {title}... (来源: {source})")
                
                # 分析结果
                analysis = report_data.get('analysis', {})
                if analysis:
                    print(f"\n📊 质量分析结果:")
                    print(f"   分析类型: {analysis.get('analysis_type', 'N/A')}")
                    print(f"   总体评分: {analysis.get('score', 'N/A')}/10")
                    print(f"   评估理由: {analysis.get('reasoning', 'N/A')}")
                    
                    # 详细评分
                    if 'metadata' in analysis and 'raw_scores' in analysis['metadata']:
                        raw_scores = analysis['metadata']['raw_scores']
                        print(f"\n📈 详细评分:")
                        for criterion, score in raw_scores.items():
                            print(f"   {criterion}: {score}/10")
                
                # 保存报告到文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"reports/水下特种机器人行业洞察报告_{timestamp}.json"
                
                # 确保reports目录存在
                os.makedirs('reports', exist_ok=True)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                print(f"\n💾 报告已保存到: {filename}")
                
                # 错误信息
                errors = report_data.get('errors', [])
                if errors:
                    print(f"\n⚠️ 处理过程中的警告:")
                    for error in errors:
                        print(f"   - {error}")
                
                return True
            else:
                print("❌ 响应格式异常")
                print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}...")
                return False
        else:
            print(f"❌ API调用失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 水下特种机器人行业洞察报告生成测试")
    print("=" * 60)
    
    success = test_underwater_robot_report()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 测试成功完成！水下特种机器人行业洞察报告已生成")
    else:
        print("💥 测试失败，请检查服务器状态和配置")
    print("=" * 60)