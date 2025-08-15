#!/usr/bin/env python3
"""
简单的FastMCP测试服务器
"""

from fastmcp import FastMCP

# 创建FastMCP应用
app = FastMCP("Simple Test Server")

@app.tool()
async def hello_world(name: str = "World") -> str:
    """
    简单的问候工具
    
    Args:
        name: 要问候的名字
    
    Returns:
        问候消息
    """
    return f"Hello, {name}! 🌟"

@app.tool()
async def get_server_info() -> str:
    """
    获取服务器信息
    
    Returns:
        服务器基本信息
    """
    return "🚀 FastMCP测试服务器正在运行！"

if __name__ == "__main__":
    print("🚀 启动 FastMCP 测试服务器...")
    print("📡 MCP协议端点")
    print("\n按 Ctrl+C 停止服务器")
    
    try:
        # FastMCP通过stdio运行，不是HTTP服务器
        app.run()
    except KeyboardInterrupt:
        print("\n👋 测试服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        import traceback
        traceback.print_exc() 