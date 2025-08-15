"""
Search MCP 日志配置

配置和管理搜索服务的日志记录
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


def setup_logger(name: str, 
                 level: str = "INFO",
                 log_format: Optional[str] = None,
                 log_file: Optional[str] = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 enable_console: bool = True) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        log_format: 日志格式
        log_file: 日志文件路径
        max_file_size: 日志文件最大大小（字节）
        backup_count: 备份文件数量
        enable_console: 是否启用控制台输出
        
    Returns:
        配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 设置日志格式
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(log_format)
    
    # 控制台处理器
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用RotatingFileHandler实现日志轮转
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        logger.addHandler(file_handler)
    
    return logger


def setup_mcp_logger(config_dict: Dict[str, Any]) -> logging.Logger:
    """
    根据配置字典设置MCP日志记录器
    
    Args:
        config_dict: 配置字典，包含日志相关配置
        
    Returns:
        配置好的日志记录器
    """
    log_level = config_dict.get('log_level', 'INFO')
    log_format = config_dict.get('log_format', 
                                 "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    log_file = config_dict.get('log_file_path')
    enable_file_logging = config_dict.get('enable_file_logging', False)
    
    # 如果没有启用文件日志，则不设置日志文件
    if not enable_file_logging:
        log_file = None
    
    return setup_logger(
        name="search_mcp",
        level=log_level,
        log_format=log_format,
        log_file=log_file
    )


class SearchLogger:
    """搜索日志管理器"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.config = config_dict
        self.logger = setup_mcp_logger(config_dict)
        self.search_logs = []  # 存储搜索日志
    
    def log_search_start(self, queries: list, sources: list, params: dict):
        """记录搜索开始"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'search_start',
            'queries': queries,
            'sources': sources,
            'params': params
        }
        self.search_logs.append(log_entry)
        
        self.logger.info(f"🚀 开始搜索: {len(queries)}个查询, {len(sources)}个数据源")
        self.logger.debug(f"搜索参数: {params}")
    
    def log_search_complete(self, results_count: int, execution_time: float, 
                           sources_used: list, errors: list = None):
        """记录搜索完成"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'search_complete',
            'results_count': results_count,
            'execution_time': execution_time,
            'sources_used': sources_used,
            'errors': errors or []
        }
        self.search_logs.append(log_entry)
        
        self.logger.info(f"✅ 搜索完成: {results_count}条结果, 耗时{execution_time:.2f}秒")
        
        if errors:
            self.logger.warning(f"⚠️ 搜索过程中出现{len(errors)}个错误")
            for error in errors:
                self.logger.error(f"错误详情: {error}")
    
    def log_source_result(self, source: str, query: str, result_count: int, 
                         success: bool, error: str = None):
        """记录单个数据源的搜索结果"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'source_result',
            'source': source,
            'query': query,
            'result_count': result_count,
            'success': success,
            'error': error
        }
        self.search_logs.append(log_entry)
        
        if success:
            self.logger.debug(f"✅ {source}({query}): {result_count}条结果")
        else:
            self.logger.error(f"❌ {source}({query}): 搜索失败 - {error}")
    
    def log_collector_status(self, collectors_info: list):
        """记录收集器状态"""
        self.logger.info("📊 收集器状态:")
        for info in collectors_info:
            self.logger.info(f"  {info.name}: {info.status}")
    
    def log_api_request(self, source: str, endpoint: str, params: dict, 
                       response_time: float, success: bool, error: str = None):
        """记录API请求"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'api_request',
            'source': source,
            'endpoint': endpoint,
            'params': params,
            'response_time': response_time,
            'success': success,
            'error': error
        }
        self.search_logs.append(log_entry)
        
        if success:
            self.logger.debug(f"🌐 API请求成功: {source} - {response_time:.2f}s")
        else:
            self.logger.error(f"🌐 API请求失败: {source} - {error}")
    
    def log_rate_limit(self, source: str, retry_after: int = None):
        """记录速率限制"""
        self.logger.warning(f"⏱️ {source} 触发速率限制")
        if retry_after:
            self.logger.info(f"将在{retry_after}秒后重试")
    
    def log_cache_hit(self, cache_key: str):
        """记录缓存命中"""
        self.logger.debug(f"💾 缓存命中: {cache_key}")
    
    def log_cache_miss(self, cache_key: str):
        """记录缓存未命中"""
        self.logger.debug(f"💾 缓存未命中: {cache_key}")
    
    def get_search_logs(self, limit: int = 100) -> list:
        """获取搜索日志"""
        return self.search_logs[-limit:]
    
    def clear_search_logs(self):
        """清除搜索日志"""
        self.search_logs.clear()
        self.logger.info("🧹 搜索日志已清除")
    
    def export_logs(self, file_path: str, format: str = 'json'):
        """导出日志到文件"""
        import json
        from pathlib import Path
        
        log_path = Path(file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == 'json':
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(self.search_logs, f, indent=2, ensure_ascii=False)
        else:
            # 简单的文本格式
            with open(log_path, 'w', encoding='utf-8') as f:
                for log_entry in self.search_logs:
                    f.write(f"{log_entry['timestamp']} - {log_entry['event']}\n")
                    f.write(f"  {log_entry}\n\n")
        
        self.logger.info(f"📄 日志已导出到: {file_path}")


def create_search_logger(config_dict: Dict[str, Any]) -> SearchLogger:
    """创建搜索日志管理器的便捷函数"""
    return SearchLogger(config_dict)


# 默认日志配置
DEFAULT_LOG_CONFIG = {
    'log_level': 'INFO',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'enable_file_logging': False,
    'log_file_path': None
} 