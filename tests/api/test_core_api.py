"""
CORE API测试脚本
这个脚本专门用于测试CORE API的功能
"""
import os
from dotenv import load_dotenv
import config
from collectors.academic_collector import AcademicCollector

def test_core_api():
    """测试CORE API功能"""
    print("开始测试CORE API...")
    
    # 加载环境变量
    load_dotenv()
    
    # 检查CORE API密钥是否存在
    core_api_key = os.getenv("CORE_API_KEY")
    if not core_api_key:
        print("错误: CORE API密钥未在环境变量中设置")
        return
    
    print(f"CORE API密钥已从环境变量中读取: {core_api_key[:5]}...{core_api_key[-5:]}")
    
    # 初始化AcademicCollector
    academic_collector = AcademicCollector()
    
    # 输出初始化状态
    print(f"可用API: {[k for k, v in academic_collector.available_apis.items() if v]}")
    print(f"API状态: {academic_collector.api_status}")
    
    # 测试搜索功能
    test_query = "AI Agent"
    days = 10
    
    print(f"\n使用查询'{test_query}'和时间范围{days}天测试CORE API...")
    
    try:
        # 调用CORE API搜索
        results = academic_collector.search_core(test_query, days)
        
        # 输出结果
        print(f"\n搜索结果: 找到 {len(results)} 篇论文")
        
        # 显示前3篇论文的标题和URL
        for i, paper in enumerate(results[:3]):
            print(f"\n论文 {i+1}:")
            print(f"  标题: {paper.get('title', '无标题')}")
            print(f"  作者: {', '.join(paper.get('authors', ['未知']))}")
            print(f"  URL: {paper.get('url', '#')}")
            print(f"  发布日期: {paper.get('published', '未知')}")
            
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
    
    print("\nCORE API测试完成")

if __name__ == "__main__":
    test_core_api()