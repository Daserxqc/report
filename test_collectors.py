import os
import sys
import time
from typing import List, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('collector_test')

def test_collectors(topic: str = "人工智能", days: int = 7):
    """测试RSS收集器和网页爬虫收集器功能
    
    Args:
        topic: 要搜索的主题
        days: 过去几天的新闻
    """
    from collectors.rss_collector import RSSCollector
    from collectors.web_scraper import WebScraperCollector
    
    results = {
        "rss": {"success": False, "count": 0, "error": None, "sample": []},
        "web": {"success": False, "count": 0, "error": None, "sample": []}
    }
    
    # 测试RSS收集器
    logger.info("开始测试RSS收集器...")
    try:
        rss_collector = RSSCollector()
        rss_news = rss_collector.get_industry_news_direct(topic, days)
        
        results["rss"]["success"] = True
        results["rss"]["count"] = len(rss_news)
        results["rss"]["sample"] = rss_news[:3] if rss_news else []
        
        logger.info(f"RSS收集器测试完成，获取到 {len(rss_news)} 条新闻")
    except Exception as e:
        logger.error(f"RSS收集器测试失败: {str(e)}")
        results["rss"]["error"] = str(e)
    
    # 测试Web爬虫收集器
    logger.info("开始测试Web爬虫收集器...")
    try:
        web_collector = WebScraperCollector()
        web_news = web_collector.get_industry_news_direct(topic, days)
        
        results["web"]["success"] = True
        results["web"]["count"] = len(web_news)
        results["web"]["sample"] = web_news[:3] if web_news else []
        
        logger.info(f"Web爬虫收集器测试完成，获取到 {len(web_news)} 条新闻")
    except Exception as e:
        logger.error(f"Web爬虫收集器测试失败: {str(e)}")
        results["web"]["error"] = str(e)
    
    # 打印测试结果摘要
    print("\n=== 收集器测试结果摘要 ===")
    print(f"测试主题: {topic}, 时间范围: 过去{days}天")
    
    print("\nRSS收集器:")
    if results["rss"]["success"]:
        print(f"  状态: 成功 ✓")
        print(f"  获取到 {results['rss']['count']} 条新闻")
        
        if results["rss"]["sample"]:
            print("\n  样本新闻:")
            for i, news in enumerate(results["rss"]["sample"], 1):
                print(f"    {i}. {news.get('title', 'No title')} - {news.get('source', 'Unknown')}")
    else:
        print(f"  状态: 失败 ✗")
        print(f"  错误: {results['rss']['error']}")
    
    print("\nWeb爬虫收集器:")
    if results["web"]["success"]:
        print(f"  状态: 成功 ✓")
        print(f"  获取到 {results['web']['count']} 条新闻")
        
        if results["web"]["sample"]:
            print("\n  样本新闻:")
            for i, news in enumerate(results["web"]["sample"], 1):
                print(f"    {i}. {news.get('title', 'No title')} - {news.get('source', 'Unknown')}")
    else:
        print(f"  状态: 失败 ✗")
        print(f"  错误: {results['web']['error']}")
    
    return results

if __name__ == "__main__":
    # 可以通过命令行参数指定主题
    topic = sys.argv[1] if len(sys.argv) > 1 else "人工智能"
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    
    print(f"开始测试收集器，主题: {topic}, 时间范围: 过去{days}天")
    test_collectors(topic, days)