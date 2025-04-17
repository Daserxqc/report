import config
"""
CORE API实现代码
这是一个单独的文件，包含CORE API搜索的改进实现
您可以将此代码集成到collectors/academic_collector.py文件中
"""

def search_core(self, query, days_back=7, max_results=None):
    """
    从CORE API搜索学术论文
    
    Args:
        query (str): 搜索关键词
        days_back (int): 搜索多少天内的论文
        max_results (int): 最大结果数量
        
    Returns:
        list: 论文信息列表
    """
    import datetime
    import requests
    
    if not self.available_apis['core']:
        print("缺少CORE API密钥，无法搜索CORE")
        return []
        
    # 确保查询词是英文
    english_query = self._translate_to_english(query)
        
    # 设置最大结果数
    if max_results is None:
        max_results = getattr(config, "CORE_MAX_RESULTS", 20)
        
    # 构建API请求头部
    headers = {
        "Authorization": f"Bearer {self.api_keys['core']}"
    }
    
    # 根据CORE API v3的文档，使用works端点进行搜索
    api_url = getattr(config, "CORE_API_URL", "https://api.core.ac.uk/v3")
    endpoint = f"{api_url}/search/works"
    
    # 构建查询参数
    # 根据CORE API文档，使用正确的查询格式
    # 按相关性排序，并按年份过滤
    current_year = datetime.datetime.now().year
    min_year = current_year - (days_back // 365) - 1  # 将天数转换为大致年数
    
    year_filter = f"yearPublished>={min_year}"
    
    params = {
        "q": english_query,
        "limit": max_results,
        "offset": 0,
        "filter": year_filter
    }
    
    try:
        print(f"正在CORE上搜索: {english_query}，过滤条件: {year_filter}")
        response = requests.get(endpoint, headers=headers, params=params)
        
        # 详细记录错误信息以便调试
        if response.status_code != 200:
            print(f"CORE API返回错误: HTTP {response.status_code}")
            print(f"响应内容: {response.text[:200]}...")  # 只打印前200个字符
            return []
            
        response.raise_for_status()
        data = response.json()
        
        # 如果没有结果，提前返回
        if "results" not in data or not data["results"]:
            print("CORE API没有返回任何结果")
            return []
            
        # 处理结果
        results = []
        current_time = datetime.datetime.now()
        
        for work in data.get("results", []):
            # 尝试获取发布日期 - CORE API返回的日期可能有多种格式
            published_date_str = current_time.strftime('%Y-%m-%d')
            
            # 尝试不同的日期字段
            if "publishedDate" in work:
                published_date_str = work["publishedDate"]
            elif "publishedYear" in work or "yearPublished" in work:
                published_year = work.get("publishedYear") or work.get("yearPublished")
                if published_year:
                    published_date_str = f"{published_year}-01-01"
            
            # 提取作者 - CORE返回的作者可能有不同格式
            authors = []
            for author in work.get("authors", []):
                if isinstance(author, dict) and "name" in author:
                    authors.append(author["name"])
                elif isinstance(author, str):
                    authors.append(author)
            
            # 获取正确的URL - CORE提供多种可能的URL
            paper_url = None
            # 1. 首先尝试下载URL
            if "downloadUrl" in work and work["downloadUrl"]:
                paper_url = work["downloadUrl"]
            # 2. 其次尝试源文本URL列表中的第一个
            elif "sourceFulltextUrls" in work and work["sourceFulltextUrls"]:
                paper_url = work["sourceFulltextUrls"][0]
            # 3. 然后尝试DOI
            elif "doi" in work and work["doi"]:
                paper_url = f"https://doi.org/{work['doi']}"
            # 4. 最后使用CORE自己的链接
            else:
                paper_url = f"https://core.ac.uk/works/{work.get('id')}"
            
            # 构建论文信息
            paper_info = {
                "title": work.get("title", "无标题"),
                "authors": authors,
                "summary": work.get("abstract", "无摘要"),
                "published": published_date_str,
                "url": paper_url,
                "source": "CORE",
                "doi": work.get("doi", "无DOI")
            }
            results.append(paper_info)
            
        print(f"在CORE上找到 {len(results)} 篇论文")
        return results
        
    except Exception as e:
        print(f"CORE API错误: {str(e)}")
        # 如果有响应对象，记录更详细的错误信息
        if 'response' in locals() and response is not None:
            print(f"HTTP状态码: {response.status_code}")
            print(f"响应内容: {response.text[:200]}...")  # 只打印前200个字符
        return [] 