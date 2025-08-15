"""
Search MCP - 基于MCP协议的统一搜索服务器

提供标准化的并行搜索接口，整合多个数据源的搜索能力
"""

__version__ = "0.1.0"
__author__ = "Report Generation Team"
__email__ = "team@example.com"

from .models import Document, SearchRequest, SearchResult
from .generators import SearchGenerator
from .config import SearchConfig

__all__ = [
    "Document",
    "SearchRequest", 
    "SearchResult",
    "SearchGenerator",
    "SearchConfig",
] 