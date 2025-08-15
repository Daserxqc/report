#!/usr/bin/env python3
"""
测试重构后的Search MCP功能
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """测试导入是否正常"""
    print("🔧 测试模块导入...")
    
    try:
        from search_mcp.config import SearchConfig
        print("✅ SearchConfig导入成功")
        
        from search_mcp.models import Document, SearchRequest, SourceType
        print("✅ 数据模型导入成功")
        
        from search_mcp.generators import SearchOrchestrator
        print("✅ SearchOrchestrator导入成功")
        
        from search_mcp.logger import setup_logger
        print("✅ 日志模块导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_config():
    """测试配置"""
    print("\n🔧 测试配置初始化...")
    
    try:
        from search_mcp.config import SearchConfig
        config = SearchConfig()
        print(f"✅ 配置初始化成功")
        print(f"   - 最大结果数: {config.max_results_per_query}")
        print(f"   - 搜索超时: {config.search_timeout}秒")
        print(f"   - 日志级别: {config.log_level}")
        return True
    except Exception as e:
        print(f"❌ 配置初始化失败: {e}")
        return False

def test_models():
    """测试数据模型"""
    print("\n🔧 测试数据模型...")
    
    try:
        from search_mcp.models import Document, SearchRequest, SourceType
        
        # 测试Document
        doc = Document(
            title="测试文档",
            content="这是一个测试文档的内容",
            url="https://example.com",
            source="test",
            source_type="web"
        )
        print(f"✅ Document创建成功: {doc.title}")
        
        # 测试SearchRequest
        request = SearchRequest(
            queries=["AI", "机器学习"],
            max_results_per_query=5
        )
        print(f"✅ SearchRequest创建成功: {len(request.queries)}个查询")
        
        # 测试SourceType
        source_types = list(SourceType)
        print(f"✅ SourceType枚举正常: {[st.value for st in source_types]}")
        
        return True
    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")
        return False

def test_orchestrator_init():
    """测试搜索编排器初始化"""
    print("\n🔧 测试SearchOrchestrator初始化...")
    
    try:
        from search_mcp.config import SearchConfig
        from search_mcp.generators import SearchOrchestrator
        
        config = SearchConfig()
        orchestrator = SearchOrchestrator(config)
        
        print("✅ SearchOrchestrator初始化成功")
        
        # 获取可用数据源
        sources = orchestrator.get_available_sources()
        print(f"✅ 可用数据源获取成功:")
        for category, source_list in sources.items():
            print(f"   - {category}: {source_list}")
        
        return True
    except Exception as e:
        print(f"❌ SearchOrchestrator初始化失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试重构后的Search MCP...")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("配置初始化", test_config),
        ("数据模型", test_models),
        ("搜索编排器", test_orchestrator_init)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name}测试失败")
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 恭喜！重构成功，所有测试通过！")
        print("\n📋 接下来可以：")
        print("1. 使用 uvx run search-mcp 运行MCP服务器")
        print("2. 在MCP客户端中连接到此服务器")
        print("3. 运行完整的搜索功能测试")
    else:
        print("⚠️ 部分测试失败，请检查错误信息")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 