#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
统一管理所有配置和环境变量
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# UTF-8编码设置
if sys.platform.startswith('win'):
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
        os.system('chcp 65001 > nul')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception as e:
        print(f"Warning: Failed to set UTF-8 encoding: {e}")

# 环境变量加载
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ 环境变量加载成功")
except ImportError:
    print("⚠️ python-dotenv未安装，跳过.env文件加载")
except Exception as e:
    print(f"⚠️ 加载.env文件失败: {e}")


@dataclass
class PathConfig:
    """路径配置"""
    project_root: Path
    search_mcp_path: Path
    search_mcp_module_path: Path
    collectors_path: Path
    outputs_path: Path
    reports_path: Path
    
    @classmethod
    def create_default(cls) -> 'PathConfig':
        """创建默认路径配置"""
        project_root = Path(__file__).parent
        return cls(
            project_root=project_root,
            search_mcp_path=project_root / "search_mcp" / "src",
            search_mcp_module_path=project_root / "search_mcp" / "src" / "search_mcp",
            collectors_path=project_root / "collectors",
            outputs_path=project_root / "outputs",
            reports_path=project_root / "reports"
        )
    
    def setup_paths(self) -> None:
        """设置Python路径"""
        paths_to_add = [
            str(self.search_mcp_path),
            str(self.search_mcp_module_path.parent),
            str(self.collectors_path)
        ]
        
        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)
        
        print(f"✅ Python路径设置完成: {len(paths_to_add)} 个路径已添加")
    
    def create_directories(self) -> None:
        """创建必要的目录"""
        directories = [self.outputs_path, self.reports_path]
        for directory in directories:
            directory.mkdir(exist_ok=True)
        print(f"✅ 目录创建完成: {len(directories)} 个目录已确保存在")


@dataclass
class APIConfig:
    """API配置"""
    tavily_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    google_cse_id: Optional[str] = None
    brave_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    dashscope_api_key: Optional[str] = None
    
    @classmethod
    def load_from_env(cls) -> 'APIConfig':
        """从环境变量加载API配置"""
        return cls(
            tavily_api_key=os.getenv('TAVILY_API_KEY'),
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            google_cse_id=os.getenv('GOOGLE_CSE_ID'),
            brave_api_key=os.getenv('BRAVE_API_KEY'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            dashscope_api_key=os.getenv('DASHSCOPE_API_KEY')
        )
    
    def get_available_apis(self) -> List[str]:
        """获取可用的API列表"""
        available = []
        if self.tavily_api_key:
            available.append('tavily')
        if self.google_api_key and self.google_cse_id:
            available.append('google')
        if self.brave_api_key:
            available.append('brave')
        if self.openai_api_key:
            available.append('openai')
        if self.dashscope_api_key:
            available.append('dashscope')
        return available
    
    def validate_search_apis(self) -> Dict[str, bool]:
        """验证搜索API配置"""
        return {
            'tavily': bool(self.tavily_api_key),
            'google': bool(self.google_api_key and self.google_cse_id),
            'brave': bool(self.brave_api_key)
        }


@dataclass
class ServerConfig:
    """服务器配置"""
    mcp_host: str = "localhost"
    mcp_port: int = 8000
    fastapi_host: str = "localhost"
    fastapi_port: int = 8001
    debug: bool = False
    cors_origins: List[str] = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]
    
    @classmethod
    def load_from_env(cls) -> 'ServerConfig':
        """从环境变量加载服务器配置"""
        return cls(
            mcp_host=os.getenv('MCP_HOST', 'localhost'),
            mcp_port=int(os.getenv('MCP_PORT', '8000')),
            fastapi_host=os.getenv('FASTAPI_HOST', 'localhost'),
            fastapi_port=int(os.getenv('FASTAPI_PORT', '8001')),
            debug=os.getenv('DEBUG', 'false').lower() == 'true'
        )


@dataclass
class SearchConfig:
    """搜索配置"""
    max_results_per_source: int = 5
    max_workers: int = 3
    search_timeout: int = 30
    retry_attempts: int = 3
    default_days: int = 7
    
    @classmethod
    def load_from_env(cls) -> 'SearchConfig':
        """从环境变量加载搜索配置"""
        return cls(
            max_results_per_source=int(os.getenv('MAX_RESULTS_PER_SOURCE', '5')),
            max_workers=int(os.getenv('MAX_WORKERS', '3')),
            search_timeout=int(os.getenv('SEARCH_TIMEOUT', '30')),
            retry_attempts=int(os.getenv('RETRY_ATTEMPTS', '3')),
            default_days=int(os.getenv('DEFAULT_DAYS', '7'))
        )


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.paths = PathConfig.create_default()
        self.apis = APIConfig.load_from_env()
        self.server = ServerConfig.load_from_env()
        self.search = SearchConfig.load_from_env()
        
        # 设置Python路径
        self.paths.setup_paths()
        # 创建必要目录
        self.paths.create_directories()
    
    def setup_encoding(self) -> None:
        """设置UTF-8编码"""
        if sys.platform.startswith('win'):
            import locale
            try:
                locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
                os.system('chcp 65001 > nul')
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stderr.reconfigure(encoding='utf-8')
                print("✅ UTF-8编码设置完成")
            except Exception as e:
                print(f"⚠️ UTF-8编码设置失败: {e}")
    
    def setup_environment(self) -> None:
        """设置环境变量"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ 环境变量设置完成")
        except ImportError:
            print("⚠️ python-dotenv未安装，跳过.env文件加载")
        except Exception as e:
            print(f"⚠️ 环境变量设置失败: {e}")
    
    def setup_paths(self) -> None:
        """设置路径"""
        self.paths.setup_paths()
        print("✅ 路径设置完成")
    
    def get_status_report(self) -> Dict[str, Any]:
        """获取配置状态报告"""
        return {
            'paths': {
                'project_root': str(self.paths.project_root),
                'search_mcp_exists': self.paths.search_mcp_path.exists(),
                'collectors_exists': self.paths.collectors_path.exists()
            },
            'apis': {
                'available': self.apis.get_available_apis(),
                'search_apis': self.apis.validate_search_apis()
            },
            'server': {
                'mcp_endpoint': f"{self.server.mcp_host}:{self.server.mcp_port}",
                'fastapi_endpoint': f"{self.server.fastapi_host}:{self.server.fastapi_port}",
                'debug_mode': self.server.debug
            },
            'search': {
                'max_results': self.search.max_results_per_source,
                'max_workers': self.search.max_workers,
                'timeout': self.search.search_timeout
            }
        }
    
    def print_status(self) -> None:
        """打印配置状态"""
        status = self.get_status_report()
        print("\n🔧 配置管理器状态报告:")
        print(f"   📁 项目根目录: {status['paths']['project_root']}")
        print(f"   🔍 搜索模块: {'✅' if status['paths']['search_mcp_exists'] else '❌'}")
        print(f"   📦 收集器模块: {'✅' if status['paths']['collectors_exists'] else '❌'}")
        print(f"   🔑 可用API: {', '.join(status['apis']['available']) if status['apis']['available'] else '无'}")
        print(f"   🌐 MCP服务器: {status['server']['mcp_endpoint']}")
        print(f"   📡 FastAPI服务器: {status['server']['fastapi_endpoint']}")
        print(f"   ⚙️ 搜索配置: {status['search']['max_results']}结果/{status['search']['max_workers']}线程")


# 全局配置实例
config_manager = ConfigManager()

# 便捷访问
paths = config_manager.paths
apis = config_manager.apis
server_config = config_manager.server
search_config = config_manager.search

# 打印初始化状态
if __name__ == "__main__":
    config_manager.print_status()
else:
    print("✅ 配置管理器初始化完成")