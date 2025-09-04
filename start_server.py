#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器启动脚本

这个脚本会同时启动:
1. MCP服务器 (用于MCP协议通信)
2. FastAPI Web服务器 (用于HTTP API和SSE流式响应)
"""

import threading
import time
from mcp.server.fastmcp import FastMCP

# 导入模块化组件
from config_manager import ConfigManager
from search_manager import SearchEngineManager
from streaming import StreamingSessionManager
from mcp_tools import get_tool_registry
from web_server import initialize_web_server, start_fastapi_server

def start_mcp_server():
    """启动MCP服务器"""
    print("🚀 启动MCP服务器...")
    
    # 初始化FastMCP服务器
    mcp = FastMCP("Search Server")
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    config_manager.setup_encoding()
    config_manager.setup_environment()
    config_manager.setup_paths()
    
    # 初始化搜索引擎管理器
    search_manager = SearchEngineManager()
    # 搜索管理器已在构造函数中自动初始化
    
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
    
    # 启动MCP服务器
    mcp.run(transport="streamable-http")
    
    return tool_registry

def start_web_server(tool_registry):
    """启动Web服务器"""
    print("🌐 启动FastAPI Web服务器...")
    
    # 初始化Web服务器
    initialize_web_server(tool_registry)
    
    # 启动FastAPI服务器
    start_fastapi_server(host="0.0.0.0", port=8001)

def main():
    """主启动函数"""
    print("=" * 50)
    print("🎯 报告生成系统启动中...")
    print("=" * 50)
    
    try:
        # 首先初始化所有组件
        print("📦 初始化系统组件...")
        
        # 初始化配置管理器
        config_manager = ConfigManager()
        config_manager.setup_encoding()
        config_manager.setup_environment()
        config_manager.setup_paths()
        
        # 初始化搜索引擎管理器
        search_manager = SearchEngineManager()
        # 搜索组件已在构造函数中初始化
        
        # 初始化MCP工具注册表
        tool_registry = get_tool_registry(search_manager)
        tool_registry.initialize_components()
        
        print("✅ 系统组件初始化完成")
        
        # 启动Web服务器线程
        print("🌐 启动Web服务器线程...")
        web_thread = threading.Thread(
            target=start_web_server, 
            args=(tool_registry,),
            daemon=True
        )
        web_thread.start()
        
        # 等待Web服务器启动
        time.sleep(2)
        print("✅ Web服务器已启动 (http://localhost:8001)")
        
        # 启动MCP服务器 (主线程)
        print("🚀 启动MCP服务器...")
        mcp = FastMCP("Search Server")
        
        # 注册MCP工具函数
        tool_registry.register_tools(mcp)
        
        # MCP资源定义
        @mcp.resource("search://{query}")
        def get_search_info(query: str) -> str:
            """Get information about a search query"""
            return f"搜索查询: '{query}'\n这个资源可以提供关于该查询的详细搜索信息。"
        
        print("✅ MCP工具已注册")
        print("=" * 50)
        print("🎉 系统启动完成!")
        print("📡 MCP服务器: streamable-http协议")
        print("🌐 Web服务器: http://localhost:8001")
        print("📊 SSE流式端点: http://localhost:8001/mcp/streaming/orchestrator")
        print("=" * 50)
        
        # 启动MCP服务器 (阻塞主线程)
        mcp.run(transport="streamable-http")
        
    except KeyboardInterrupt:
        print("\n👋 用户中断，正在关闭服务器...")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise

if __name__ == "__main__":
    main()