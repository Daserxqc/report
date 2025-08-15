#!/usr/bin/env python3
"""
Search HTTP API Server

基于 FastAPI 的统一搜索HTTP服务器
支持浏览器访问和RESTful API调用
"""

import sys
import json
from pathlib import Path
from typing import Any, Optional, List

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import uvicorn

from search_mcp.config import SearchConfig
from search_mcp.generators import SearchOrchestrator
from search_mcp.logger import setup_logger
from search_mcp.models import Document

# 创建FastAPI应用
app = FastAPI(
    title="Search API Server",
    description="统一搜索HTTP服务器，支持多种数据源的并行搜索",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 全局配置和服务
config = SearchConfig()
logger = setup_logger("search_api", config.log_level)
search_orchestrator = SearchOrchestrator(config)

logger.info("🚀 Search HTTP API服务器初始化完成")

# API请求模型
class ParallelSearchRequest(BaseModel):
    queries: List[str] = Field(..., description="搜索查询列表")
    sources: Optional[List[str]] = Field(None, description="指定的数据源列表")
    max_results_per_query: int = Field(5, ge=1, le=20, description="每个查询的最大结果数")
    days_back: int = Field(7, ge=1, le=365, description="搜索多少天内的内容")
    max_workers: int = Field(6, ge=1, le=20, description="最大并行工作线程数")

class CategorySearchRequest(BaseModel):
    queries: List[str] = Field(..., description="搜索查询列表")
    category: str = Field("web", description="搜索类别 (web, academic, news)")
    max_results_per_query: int = Field(5, ge=1, le=20, description="每个查询的最大结果数")
    days_back: int = Field(7, ge=1, le=365, description="搜索多少天内的内容")
    max_workers: int = Field(4, ge=1, le=20, description="最大并行工作线程数")

class FallbackSearchRequest(BaseModel):
    queries: List[str] = Field(..., description="搜索查询列表")
    preferred_sources: Optional[List[str]] = Field(None, description="首选数据源列表")
    fallback_sources: Optional[List[str]] = Field(None, description="备选数据源列表")
    max_results_per_query: int = Field(5, ge=1, le=20, description="每个查询的最大结果数")
    days_back: int = Field(7, ge=1, le=365, description="搜索多少天内的内容")

# API响应模型
class SearchResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    count: int = 0

@app.get("/", response_class=HTMLResponse)
async def root():
    """主页 - 提供服务介绍和测试界面"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Search API Server</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            .endpoint {{ background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #3498db; }}
            .method {{ font-weight: bold; color: #e67e22; }}
            .url {{ font-family: monospace; background: #34495e; color: white; padding: 2px 6px; border-radius: 3px; }}
            .test-form {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            input, textarea, select {{ width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }}
            button {{ background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }}
            button:hover {{ background: #2980b9; }}
            .result {{ background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; margin-top: 10px; white-space: pre-wrap; font-family: monospace; }}
            .sources {{ display: flex; flex-wrap: wrap; gap: 10px; }}
            .source-tag {{ background: #27ae60; color: white; padding: 5px 10px; border-radius: 3px; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Search API Server</h1>
            <p><strong>版本:</strong> 0.1.0</p>
            <p><strong>描述:</strong> 统一搜索HTTP服务器，支持多种数据源的并行搜索</p>
            
            <div class="sources">
                <h2>📊 可用数据源</h2>
                <div class="source-tag">Tavily</div>
                <div class="source-tag">Brave Search</div>
                <div class="source-tag">Google Search</div>
                <div class="source-tag">ArXiv</div>
                <div class="source-tag">Academic</div>
            </div>

            <h2>🔧 API端点</h2>
            
            <div class="endpoint">
                <div><span class="method">GET</span> <span class="url">/</span> - 主页</div>
            </div>
            
            <div class="endpoint">
                <div><span class="method">GET</span> <span class="url">/health</span> - 健康检查</div>
            </div>
            
            <div class="endpoint">
                <div><span class="method">GET</span> <span class="url">/sources</span> - 获取可用数据源</div>
            </div>
            
            <div class="endpoint">
                <div><span class="method">POST</span> <span class="url">/search/parallel</span> - 并行搜索</div>
            </div>
            
            <div class="endpoint">
                <div><span class="method">POST</span> <span class="url">/search/category</span> - 按类别搜索</div>
            </div>
            
            <div class="endpoint">
                <div><span class="method">POST</span> <span class="url">/search/fallback</span> - 带降级搜索</div>
            </div>
            
            <div class="endpoint">
                <div><span class="method">GET</span> <span class="url">/search/quick</span> - 快速搜索 (GET参数)</div>
            </div>

            <h2>🧪 快速测试</h2>
            <div class="test-form">
                <h3>快速搜索测试</h3>
                <input type="text" id="queryInput" placeholder="输入搜索关键词，如：AI人工智能" value="AI人工智能">
                <select id="categorySelect">
                    <option value="web">网页搜索</option>
                    <option value="academic">学术搜索</option>
                    <option value="news">新闻搜索</option>
                </select>
                <button onclick="quickSearch()">🔍 搜索</button>
                <div id="result" class="result" style="display:none;"></div>
            </div>

            <div style="margin-top: 30px; text-align: center; color: #7f8c8d;">
                <p>📚 <a href="/docs" target="_blank">完整API文档</a> | 🔄 <a href="/redoc" target="_blank">ReDoc文档</a></p>
            </div>
        </div>

        <script>
        async function quickSearch() {{
            const query = document.getElementById('queryInput').value;
            const category = document.getElementById('categorySelect').value;
            const resultDiv = document.getElementById('result');
            
            if (!query.trim()) {{
                alert('请输入搜索关键词');
                return;
            }}
            
            resultDiv.style.display = 'block';
            resultDiv.textContent = '🔄 搜索中...';
            
            try {{
                const response = await fetch(`/search/quick?q=${{encodeURIComponent(query)}}&category=${{category}}`);
                const data = await response.json();
                
                if (response.ok) {{
                    resultDiv.textContent = JSON.stringify(data, null, 2);
                }} else {{
                    resultDiv.textContent = `❌ 错误: ${{data.message || '搜索失败'}}`;
                }}
            }} catch (error) {{
                resultDiv.textContent = `❌ 网络错误: ${{error.message}}`;
            }}
        }}
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        sources = search_orchestrator.get_available_sources()
        return {
            "status": "healthy",
            "service": "Search HTTP API Server",
            "version": "0.1.0",
            "available_sources": sources,
            "timestamp": str(search_orchestrator.config.log_level)
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务异常: {str(e)}")

@app.get("/sources")
async def get_sources():
    """获取可用数据源"""
    try:
        sources = search_orchestrator.get_available_sources()
        return SearchResponse(
            success=True,
            message="获取数据源成功",
            data=sources,
            count=sum(len(source_list) for source_list in sources.values())
        )
    except Exception as e:
        logger.error(f"获取数据源失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取数据源失败: {str(e)}")

@app.post("/search/parallel")
async def parallel_search(request: ParallelSearchRequest):
    """并行搜索多个查询和数据源"""
    try:
        logger.info(f"🔧 并行搜索: {request.queries[:3]}{'...' if len(request.queries) > 3 else ''}")
        
        documents = search_orchestrator.parallel_search(
            queries=request.queries,
            sources=request.sources,
            max_results_per_query=request.max_results_per_query,
            days_back=request.days_back,
            max_workers=request.max_workers
        )
        
        return SearchResponse(
            success=True,
            message=f"并行搜索完成，找到 {len(documents)} 条结果",
            data=[doc.to_dict() for doc in documents],
            count=len(documents)
        )
        
    except Exception as e:
        logger.error(f"并行搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.post("/search/category")
async def category_search(request: CategorySearchRequest):
    """按类别搜索"""
    try:
        if request.category not in ["web", "academic", "news"]:
            raise HTTPException(status_code=400, detail=f"不支持的搜索类别: {request.category}")
        
        logger.info(f"🔧 {request.category}类别搜索: {request.queries[:3]}{'...' if len(request.queries) > 3 else ''}")
        
        documents = search_orchestrator.search_by_category(
            queries=request.queries,
            category=request.category,
            max_results_per_query=request.max_results_per_query,
            days_back=request.days_back,
            max_workers=request.max_workers
        )
        
        return SearchResponse(
            success=True,
            message=f"{request.category}类别搜索完成，找到 {len(documents)} 条结果",
            data=[doc.to_dict() for doc in documents],
            count=len(documents)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"{request.category}类别搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.post("/search/fallback")
async def fallback_search(request: FallbackSearchRequest):
    """带降级的搜索"""
    try:
        logger.info(f"🔧 降级搜索: {request.queries[:3]}{'...' if len(request.queries) > 3 else ''}")
        
        documents = search_orchestrator.search_with_fallback(
            queries=request.queries,
            preferred_sources=request.preferred_sources,
            fallback_sources=request.fallback_sources,
            max_results_per_query=request.max_results_per_query,
            days_back=request.days_back
        )
        
        return SearchResponse(
            success=True,
            message=f"降级搜索完成，找到 {len(documents)} 条结果",
            data=[doc.to_dict() for doc in documents],
            count=len(documents)
        )
        
    except Exception as e:
        logger.error(f"降级搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.get("/search/quick")
async def quick_search(
    q: str = Query(..., description="搜索查询"),
    category: str = Query("web", description="搜索类别"),
    max_results: int = Query(5, ge=1, le=20, description="最大结果数")
):
    """快速搜索 - GET方式，方便浏览器直接访问"""
    try:
        logger.info(f"🔧 快速搜索: {q} (类别: {category})")
        
        documents = search_orchestrator.search_by_category(
            queries=[q],
            category=category,
            max_results_per_query=max_results
        )
        
        return SearchResponse(
            success=True,
            message=f"快速搜索完成，找到 {len(documents)} 条结果",
            data=[doc.to_dict() for doc in documents],
            count=len(documents)
        )
        
    except Exception as e:
        logger.error(f"快速搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

if __name__ == "__main__":
    print("🚀 启动 Search HTTP API 服务器...")
    print("📡 服务地址: http://localhost:8080")
    print("📚 API文档: http://localhost:8080/docs")
    print("🔄 ReDoc文档: http://localhost:8080/redoc")
    print("❤️  健康检查: http://localhost:8080/health")
    print("🔍 快速测试: http://localhost:8080/search/quick?q=AI人工智能")
    print("\n按 Ctrl+C 停止服务器")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    ) 