"""
Search MCP 数据模型

定义搜索相关的数据结构和类型
"""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Union, Any
from urllib.parse import urlparse
from datetime import datetime
from enum import Enum


class SourceType(Enum):
    """数据源类型枚举"""
    WEB = "web"
    ACADEMIC = "academic" 
    NEWS = "news"
    ARXIV = "arxiv"
    SOCIAL = "social"


@dataclass
class Document:
    """
    统一的文档数据结构
    标准化不同数据源的返回格式
    """
    title: str
    content: str
    url: str
    source: str
    source_type: str  # 'web', 'academic', 'news', 'arxiv'
    publish_date: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    venue: Optional[str] = None  # 学术期刊/会议名称
    score: Optional[float] = None  # 相关性评分
    language: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.authors is None:
            self.authors = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    @property
    def domain(self) -> str:
        """提取域名用于去重"""
        try:
            return urlparse(self.url).netloc.lower()
        except:
            return ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """从字典创建Document实例"""
        return cls(**data)
    
    def is_similar_to(self, other: 'Document', threshold: float = 0.8) -> bool:
        """判断是否与另一个文档相似"""
        # 简单的相似性检查：URL或标题相似
        if self.url == other.url:
            return True
        
        # 简单的标题相似性检查（可以使用更复杂的算法）
        title_similarity = self._calculate_text_similarity(self.title, other.title)
        return title_similarity >= threshold
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度（简化版本）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)


@dataclass
class SearchRequest:
    """搜索请求数据结构"""
    queries: List[str]
    sources: Optional[List[str]] = None
    max_results_per_query: int = 5
    days_back: int = 7
    max_workers: int = 6
    category: Optional[str] = None
    preferred_sources: Optional[List[str]] = None
    fallback_sources: Optional[List[str]] = None
    
    def __post_init__(self):
        """验证请求参数"""
        if not self.queries:
            raise ValueError("查询列表不能为空")
        
        if self.max_results_per_query <= 0:
            raise ValueError("每个查询的最大结果数必须大于0")
        
        if self.days_back <= 0:
            raise ValueError("搜索天数必须大于0")
        
        if self.max_workers <= 0:
            raise ValueError("最大工作线程数必须大于0")


@dataclass
class SearchResult:
    """搜索结果数据结构"""
    documents: List[Document]
    total_count: int
    search_type: str
    execution_time: float
    sources_used: List[str]
    query_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        if self.total_count != len(self.documents):
            self.total_count = len(self.documents)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "documents": [doc.to_dict() for doc in self.documents],
            "total_count": self.total_count,
            "search_type": self.search_type,
            "execution_time": self.execution_time,
            "sources_used": self.sources_used,
            "query_count": self.query_count,
            "metadata": self.metadata
        }
    
    def filter_by_source_type(self, source_type: str) -> 'SearchResult':
        """按数据源类型过滤结果"""
        filtered_docs = [doc for doc in self.documents if doc.source_type == source_type]
        
        return SearchResult(
            documents=filtered_docs,
            total_count=len(filtered_docs),
            search_type=f"{self.search_type} (filtered by {source_type})",
            execution_time=self.execution_time,
            sources_used=self.sources_used,
            query_count=self.query_count,
            metadata=self.metadata.copy()
        )
    
    def sort_by_relevance(self) -> 'SearchResult':
        """按相关性排序"""
        sorted_docs = sorted(
            self.documents,
            key=lambda doc: (doc.score or 0, self._parse_date(doc.publish_date)),
            reverse=True
        )
        
        return SearchResult(
            documents=sorted_docs,
            total_count=self.total_count,
            search_type=f"{self.search_type} (sorted by relevance)",
            execution_time=self.execution_time,
            sources_used=self.sources_used,
            query_count=self.query_count,
            metadata=self.metadata.copy()
        )
    
    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """解析日期字符串"""
        if not date_str:
            return datetime.min
        
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except:
                return datetime.min
    
    def get_summary(self) -> Dict[str, Any]:
        """获取结果摘要"""
        source_type_counts = {}
        source_counts = {}
        
        for doc in self.documents:
            # 按类型统计
            source_type = doc.source_type
            source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
            
            # 按来源统计
            source = doc.source
            source_counts[source] = source_counts.get(source, 0) + 1
        
        return {
            "total_documents": self.total_count,
            "search_type": self.search_type,
            "execution_time": f"{self.execution_time:.2f}s",
            "queries_processed": self.query_count,
            "sources_used": self.sources_used,
            "by_source_type": source_type_counts,
            "by_source": source_counts,
            "metadata": self.metadata
        }


@dataclass
class CollectorInfo:
    """收集器信息"""
    name: str
    source_type: str
    is_available: bool
    api_key_required: bool
    has_api_key: bool
    description: str = ""
    
    @property
    def status(self) -> str:
        """获取状态字符串"""
        if not self.is_available:
            return "❌ 不可用"
        elif self.api_key_required and not self.has_api_key:
            return "⚠️ 缺少API密钥"
        else:
            return "✅ 可用"


@dataclass
class SearchMetrics:
    """搜索性能指标"""
    total_queries: int
    successful_queries: int
    failed_queries: int
    total_results: int
    execution_time: float
    average_time_per_query: float
    sources_used: List[str]
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_queries == 0:
            return 0.0
        return self.successful_queries / self.total_queries
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self) 