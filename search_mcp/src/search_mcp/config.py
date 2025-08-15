"""
Search MCP 配置管理

管理搜索服务的配置参数和环境变量
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class SearchConfig:
    """搜索配置类"""
    
    # API密钥配置
    tavily_api_key: Optional[str] = None
    brave_search_api_key: Optional[str] = None
    google_search_api_key: Optional[str] = None
    google_search_cx: Optional[str] = None
    newsapi_key: Optional[str] = None
    ieee_api_key: Optional[str] = None
    core_api_key: Optional[str] = None
    
    # 搜索限制配置
    max_results_per_query: int = 5
    max_total_results: int = 100
    default_days_back: int = 7
    max_days_back: int = 365
    max_workers: int = 6
    max_concurrent_requests: int = 10
    
    # 超时配置
    request_timeout: float = 30.0
    search_timeout: float = 120.0
    
    # 重试配置
    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_factor: float = 2.0
    
    # 缓存配置
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1小时
    cache_size: int = 1000
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_file_logging: bool = False
    log_file_path: Optional[str] = None
    
    # 数据源配置
    enabled_sources: List[str] = field(default_factory=lambda: [
        "tavily", "brave", "google", "arxiv", "academic", "news"
    ])
    
    # 特定数据源配置
    tavily_config: Dict[str, Any] = field(default_factory=lambda: {
        "search_depth": "advanced",
        "max_results": 15,
        "include_answer": True,
        "include_raw_content": False
    })
    
    brave_config: Dict[str, Any] = field(default_factory=lambda: {
        "country": "ALL",
        "search_lang": "ALL",
        "ui_lang": "en-US",
        "safesearch": "moderate",
        "freshness": "pw"  # past week
    })
    
    google_config: Dict[str, Any] = field(default_factory=lambda: {
        "num": 10,
        "hl": "zh-CN",
        "gl": "cn",
        "safe": "active"
    })
    
    arxiv_config: Dict[str, Any] = field(default_factory=lambda: {
        "max_results": 50,
        "sort_by": "submittedDate",
        "sort_order": "descending"
    })
    
    news_config: Dict[str, Any] = field(default_factory=lambda: {
        "language": "zh",
        "country": "cn",
        "sort_by": "publishedAt",
        "page_size": 40
    })
    
    # RSS源配置
    rss_feeds: List[str] = field(default_factory=lambda: [
        "https://feeds.bbci.co.uk/zhongwen/simp/rss.xml",
        "https://www.zaobao.com/rss/realtime/china",
        "https://www.36kr.com/feed",
        "https://techcrunch.com/feed/",
        "https://www.wired.com/feed/rss"
    ])
    
    # 输出配置
    output_dir: str = "outputs"
    save_results: bool = False
    result_format: str = "json"  # json, csv, md
    
    def __post_init__(self):
        """初始化后加载环境变量"""
        self._load_from_env()
        self._validate_config()
        self._setup_directories()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        # API密钥
        self.tavily_api_key = os.getenv("TAVILY_API_KEY", self.tavily_api_key)
        self.brave_search_api_key = os.getenv("BRAVE_SEARCH_API_KEY", self.brave_search_api_key)
        self.google_search_api_key = os.getenv("GOOGLE_SEARCH_API_KEY", self.google_search_api_key)
        self.google_search_cx = os.getenv("GOOGLE_SEARCH_CX", self.google_search_cx)
        self.newsapi_key = os.getenv("NEWSAPI_KEY", self.newsapi_key)
        self.ieee_api_key = os.getenv("IEEE_API_KEY", self.ieee_api_key)
        self.core_api_key = os.getenv("CORE_API_KEY", self.core_api_key)
        
        # 数值配置
        self.max_results_per_query = int(os.getenv("SEARCH_MAX_RESULTS_PER_QUERY", self.max_results_per_query))
        self.max_workers = int(os.getenv("SEARCH_MAX_WORKERS", self.max_workers))
        self.request_timeout = float(os.getenv("SEARCH_REQUEST_TIMEOUT", self.request_timeout))
        
        # 日志配置
        self.log_level = os.getenv("SEARCH_LOG_LEVEL", self.log_level).upper()
        self.log_file_path = os.getenv("SEARCH_LOG_FILE", self.log_file_path)
        
        # 输出配置
        self.output_dir = os.getenv("SEARCH_OUTPUT_DIR", self.output_dir)
        self.save_results = os.getenv("SEARCH_SAVE_RESULTS", "false").lower() == "true"
    
    def _validate_config(self):
        """验证配置参数"""
        if self.max_results_per_query <= 0:
            raise ValueError("max_results_per_query must be positive")
        
        if self.max_workers <= 0:
            raise ValueError("max_workers must be positive")
        
        if self.request_timeout <= 0:
            raise ValueError("request_timeout must be positive")
        
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Invalid log level: {self.log_level}")
    
    def _setup_directories(self):
        """设置必要的目录"""
        output_path = Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if self.log_file_path:
            log_path = Path(self.log_file_path).parent
            log_path.mkdir(parents=True, exist_ok=True)
    
    def get_api_keys(self) -> Dict[str, Optional[str]]:
        """获取所有API密钥"""
        return {
            "tavily": self.tavily_api_key,
            "brave": self.brave_search_api_key,
            "google": self.google_search_api_key,
            "google_cx": self.google_search_cx,
            "newsapi": self.newsapi_key,
            "ieee": self.ieee_api_key,
            "core": self.core_api_key,
        }
    
    def has_api_key(self, source: str) -> bool:
        """检查是否有指定数据源的API密钥"""
        api_keys = self.get_api_keys()
        
        if source == "tavily":
            return bool(api_keys["tavily"])
        elif source == "brave":
            return bool(api_keys["brave"])
        elif source == "google":
            return bool(api_keys["google"]) and bool(api_keys["google_cx"])
        elif source == "newsapi" or source == "news":
            return bool(api_keys["newsapi"])
        elif source == "ieee":
            return bool(api_keys["ieee"])
        elif source == "core":
            return bool(api_keys["core"])
        elif source in ["arxiv", "academic"]:
            return True  # 这些不需要API密钥
        else:
            return False
    
    def get_source_config(self, source: str) -> Dict[str, Any]:
        """获取指定数据源的配置"""
        config_map = {
            "tavily": self.tavily_config,
            "brave": self.brave_config,
            "google": self.google_config,
            "arxiv": self.arxiv_config,
            "news": self.news_config,
        }
        return config_map.get(source, {})
    
    def get_enabled_sources(self) -> List[str]:
        """获取启用的数据源列表"""
        return [source for source in self.enabled_sources if self.has_api_key(source)]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（不包含敏感信息）"""
        config_dict = {
            "max_results_per_query": self.max_results_per_query,
            "max_workers": self.max_workers,
            "request_timeout": self.request_timeout,
            "search_timeout": self.search_timeout,
            "log_level": self.log_level,
            "enabled_sources": self.enabled_sources,
            "output_dir": self.output_dir,
            "save_results": self.save_results,
        }
        
        # 添加API密钥状态（不包含实际密钥）
        config_dict["api_key_status"] = {
            source: self.has_api_key(source)
            for source in ["tavily", "brave", "google", "newsapi", "ieee", "core", "arxiv"]
        }
        
        return config_dict
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'SearchConfig':
        """从字典创建配置实例"""
        return cls(**config_dict)
    
    def update(self, **kwargs):
        """更新配置参数"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown config parameter: {key}")
        
        # 重新验证配置
        self._validate_config()


def load_config_from_file(config_path: str) -> SearchConfig:
    """从配置文件加载配置"""
    import json
    
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    return SearchConfig.from_dict(config_data)


def save_config_to_file(config: SearchConfig, config_path: str):
    """保存配置到文件"""
    import json
    
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config.to_dict(), f, indent=2, ensure_ascii=False) 