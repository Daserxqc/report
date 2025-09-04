# -*- coding: utf-8 -*-
from mcp.server.fastmcp import FastMCP

# 导入新的模块化组件
from config_manager import ConfigManager
from search_manager import SearchEngineManager
from streaming import StreamingSessionManager
from mcp_tools import get_tool_registry, orchestrator_mcp_simple, orchestrator_mcp
from collectors.analysis_mcp import AnalysisMcp

# 初始化分析MCP组件
analysis_mcp = AnalysisMcp()

# 初始化FastMCP服务器
mcp = FastMCP("Search Server")

# 初始化配置管理器
config_manager = ConfigManager()
config_manager.setup_encoding()
config_manager.setup_environment()
config_manager.setup_paths()

# 初始化搜索引擎管理器
search_manager = SearchEngineManager()

# 初始化流式会话管理器
streaming_manager = StreamingSessionManager()

# 初始化MCP工具注册表
tool_registry = get_tool_registry(search_manager)

# 注册MCP工具函数
tool_registry.register_tools(mcp)

# MCP资源定义
@mcp.resource("search://{query}")
def get_search_info(query: str) -> str:
    """Get information about a search query"""
    return f"搜索查询: '{query}'\n这个资源可以提供关于该查询的详细搜索信息。"

if __name__ == "__main__":
    print("🚀 启动MCP服务器...")
    
    # 启动主MCP服务器
    # FastMCP默认使用streamable-http传输协议
    mcp.run(transport="streamable-http")
