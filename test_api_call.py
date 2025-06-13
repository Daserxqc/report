#!/usr/bin/env python3
"""
简单的API调用测试脚本
"""

import requests
import time
import json

def test_api():
    """测试智能报告生成API"""
    
    # API基础地址
    api_base = "http://localhost:8000"
    
    print("🤖 开始测试智能报告生成API...")
    print("=" * 50)
    
    # 1. 健康检查
    print("🔍 检查API服务状态...")
    try:
        response = requests.get(f"{api_base}/api/health")
        health = response.json()
        print(f"✅ API状态: {health['status']}")
        print(f"📊 活跃任务: {health['active_tasks']}")
    except Exception as e:
        print(f"❌ 无法连接到API: {e}")
        return
    
    # 2. 生成报告
    print("\n🚀 提交报告生成任务...")
    
    # 报告请求参数
    report_request = {
        "topic": "人工智能",           # 报告主题
        "companies": ["OpenAI", "百度", "腾讯"],  # 重点关注的公司（可选）
        "days": 7,                    # 搜索最近7天的新闻
        "output_filename": "AI_test_report.md"  # 输出文件名（可选）
    }
    
    try:
        response = requests.post(
            f"{api_base}/api/generate-report",
            json=report_request,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        result = response.json()
        task_id = result['task_id']
        
        print(f"✅ 任务已提交!")
        print(f"📋 任务ID: {task_id}")
        print(f"💬 消息: {result['message']}")
        
    except Exception as e:
        print(f"❌ 提交任务失败: {e}")
        return
    
    # 3. 监控任务进度
    print(f"\n⏱️ 监控任务进度 (任务ID: {task_id})")
    print("提示：报告生成通常需要3-10分钟，请耐心等待...")
    
    while True:
        try:
            response = requests.get(f"{api_base}/api/task/{task_id}")
            status_info = response.json()
            
            status = status_info['status']
            progress = status_info['progress']
            
            print(f"📊 {progress}")
            
            if status == 'completed':
                print("🎉 报告生成完成！")
                break
            elif status == 'failed':
                error = status_info.get('error', '未知错误')
                print(f"❌ 任务失败: {error}")
                return
            
            # 等待10秒后再次检查
            time.sleep(10)
            
        except Exception as e:
            print(f"❌ 检查状态失败: {e}")
            return
    
    # 4. 预览报告
    print("\n📖 预览报告内容...")
    try:
        response = requests.get(f"{api_base}/api/preview/{task_id}")
        preview = response.json()
        
        print(f"📄 文件名: {preview['filename']}")
        print(f"📅 生成日期: {preview['report_date']}")
        print(f"📊 数据统计: {preview['data_summary']}")
        print(f"📝 内容预览: {preview['content'][:300]}...")
        
    except Exception as e:
        print(f"❌ 预览失败: {e}")
    
    # 5. 下载报告
    print("\n📥 下载报告文件...")
    try:
        response = requests.get(f"{api_base}/api/download/{task_id}")
        response.raise_for_status()
        
        # 保存文件
        filename = f"downloaded_report_{task_id[:8]}.md"
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ 报告已下载: {filename}")
        
    except Exception as e:
        print(f"❌ 下载失败: {e}")
    
    print("\n🎯 测试完成！")

if __name__ == "__main__":
    test_api() 