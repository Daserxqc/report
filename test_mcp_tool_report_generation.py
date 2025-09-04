import asyncio
import os
import sys
import json

# 将项目根目录添加到Python路径中，以便导入mcp_tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp_tools import content_writer_mcp, initialize_tools

async def run_test():
    """
    运行一个测试用例，调用 content_writer_mcp 生成一份关于“人工智能在医疗领域的应用”的详细报告。
    """
    # 初始化工具
    initialize_tools()
    
    topic = "人工智能在医疗领域的应用"
    session_id = "test_session_12345"
    
    print(f"--- 开始运行报告生成测试 ---")
    print(f"主题: {topic}")
    print(f"会话ID: {session_id}")
    
    # 调用 content_writer_mcp 函数
    # 这个函数现在内部会处理搜索、大纲生成和详细内容写作
    result = await content_writer_mcp(
        topic=topic,
        session_id=session_id,
        content_style="enhanced"  # 确保使用我们新的增强模式
    )
    
    print(f"--- 测试完成 ---")
    
    # 处理并打印结果
    if "error" in result:
        print(f"测试失败: 报告生成过程中出现错误。")
        print(f"错误详情: {result['error']}")
    else:
        print(f"测试成功: 报告生成成功！")
        
        content = result.get("content", "")
        content_length = result.get("content_length", 0)
        quality_score = result.get("quality_score", "N/A")
        
        # 保存报告到文件
        output_filename = "final_generated_report.txt"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"\n--- 报告摘要 ---")
        print(f"主题: {result.get('topic', 'N/A')}")
        print(f"总字符数: {content_length}")
        print(f"内容质量评分: {quality_score}")
        print(f"数据源数量: {result.get('data_sources_count', 0)}")
        print(f"报告已保存到: {output_filename}")
        
        # 检查是否达到目标长度
        target_length = 30000
        if content_length >= target_length:
            print(f"\n目标达成: 报告长度 ({content_length}) 已达到或超过目标 ({target_length})。")
        else:
            print(f"\n目标未达成: 报告长度 ({content_length}) 未达到目标 ({target_length})。")

if __name__ == "__main__":
    # 在Windows上设置事件循环策略以避免常见错误
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(run_test())