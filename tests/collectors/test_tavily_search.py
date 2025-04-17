from collectors.tavily_collector import TavilyCollector

def test_tavily_search():
    """测试Tavily搜索功能"""
    print("=== 测试Tavily搜索功能 ===")
    
    collector = TavilyCollector()
    
    # 测试基本搜索
    query = "人工智能最新技术趋势"
    print(f"执行搜索: {query}")
    
    results = collector.search(query, max_results=3)
    
    if results:
        print(f"搜索成功，获取到 {len(results)} 条结果:")
        for i, result in enumerate(results, 1):
            print(f"\n--- 结果 {i} ---")
            print(f"标题: {result.get('title', '无标题')}")
            print(f"来源: {result.get('source', '未知来源')}")
            print(f"URL: {result.get('url', '无URL')}")
            content_preview = result.get('content', '无内容')[:100] + "..." if len(result.get('content', '')) > 100 else result.get('content', '无内容')
            print(f"内容预览: {content_preview}")
    else:
        print("搜索未返回任何结果或出现错误")

if __name__ == "__main__":
    test_tavily_search() 