"""
Search MCP Server 完整测试文件

测试搜索MCP服务器的各种功能和边界情况
"""

import pytest
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加src目录到路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.search_mcp.config import SearchConfig
from src.search_mcp.models import Document, SearchRequest, SearchResult
from src.search_mcp.generators import SearchGenerator
from src.search_mcp.logger import setup_logger, SearchLogger


class TestSearchConfig:
    """测试搜索配置类"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = SearchConfig()
        assert config.max_results_per_query == 5
        assert config.max_workers == 6
        assert config.log_level == "INFO"
        assert config.output_dir == "outputs"
    
    def test_config_validation(self):
        """测试配置验证"""
        # 测试无效配置
        with pytest.raises(ValueError):
            SearchConfig(max_results_per_query=0)
        
        with pytest.raises(ValueError):
            SearchConfig(max_workers=0)
        
        with pytest.raises(ValueError):
            SearchConfig(request_timeout=0)
    
    def test_api_key_checking(self):
        """测试API密钥检查"""
        config = SearchConfig()
        
        # 测试不需要API密钥的源
        assert config.has_api_key('arxiv') == True
        assert config.has_api_key('academic') == True
        
        # 测试需要API密钥的源（默认为None）
        assert config.has_api_key('tavily') == False
        assert config.has_api_key('brave') == False
    
    def test_config_from_env(self):
        """测试从环境变量加载配置"""
        with patch.dict('os.environ', {
            'TAVILY_API_KEY': 'test_key',
            'SEARCH_MAX_WORKERS': '8',
            'SEARCH_LOG_LEVEL': 'DEBUG'
        }):
            config = SearchConfig()
            assert config.tavily_api_key == 'test_key'
            assert config.max_workers == 8
            assert config.log_level == 'DEBUG'


class TestDocument:
    """测试Document数据模型"""
    
    def test_document_creation(self):
        """测试Document创建"""
        doc = Document(
            title="Test Title",
            content="Test content",
            url="https://example.com",
            source="test",
            source_type="web"
        )
        
        assert doc.title == "Test Title"
        assert doc.content == "Test content"
        assert doc.url == "https://example.com"
        assert doc.source == "test"
        assert doc.source_type == "web"
        assert doc.authors == []  # 默认空列表
    
    def test_document_domain_extraction(self):
        """测试域名提取"""
        doc = Document(
            title="Test",
            content="Content",
            url="https://www.example.com/path",
            source="test",
            source_type="web"
        )
        
        assert doc.domain == "www.example.com"
    
    def test_document_similarity(self):
        """测试文档相似性"""
        doc1 = Document(
            title="Machine Learning Basics",
            content="Content 1",
            url="https://example.com/ml",
            source="test",
            source_type="web"
        )
        
        doc2 = Document(
            title="Machine Learning Advanced",
            content="Content 2",
            url="https://example.com/ml-advanced",
            source="test",
            source_type="web"
        )
        
        # 相同URL
        doc3 = Document(
            title="Different Title",
            content="Different Content",
            url="https://example.com/ml",
            source="test",
            source_type="web"
        )
        
        # 测试相似性
        assert doc1.is_similar_to(doc3) == True  # 相同URL
        similarity = doc1.is_similar_to(doc2)
        assert isinstance(similarity, bool)
    
    def test_document_to_dict(self):
        """测试Document转字典"""
        doc = Document(
            title="Test Title",
            content="Test content",
            url="https://example.com",
            source="test",
            source_type="web",
            authors=["Author 1", "Author 2"]
        )
        
        result = doc.to_dict()
        assert isinstance(result, dict)
        assert result['title'] == "Test Title"
        assert result['authors'] == ["Author 1", "Author 2"]


class TestSearchRequest:
    """测试搜索请求模型"""
    
    def test_valid_request(self):
        """测试有效请求"""
        request = SearchRequest(
            queries=["test query"],
            max_results_per_query=10,
            days_back=30,
            max_workers=4
        )
        
        assert request.queries == ["test query"]
        assert request.max_results_per_query == 10
        assert request.days_back == 30
        assert request.max_workers == 4
    
    def test_invalid_request(self):
        """测试无效请求"""
        # 空查询列表
        with pytest.raises(ValueError):
            SearchRequest(queries=[])
        
        # 无效参数
        with pytest.raises(ValueError):
            SearchRequest(queries=["test"], max_results_per_query=0)
        
        with pytest.raises(ValueError):
            SearchRequest(queries=["test"], days_back=0)
        
        with pytest.raises(ValueError):
            SearchRequest(queries=["test"], max_workers=0)


class TestSearchResult:
    """测试搜索结果模型"""
    
    def test_search_result_creation(self):
        """测试搜索结果创建"""
        documents = [
            Document("Title 1", "Content 1", "https://example.com/1", "test", "web"),
            Document("Title 2", "Content 2", "https://example.com/2", "test", "academic")
        ]
        
        result = SearchResult(
            documents=documents,
            total_count=2,
            search_type="test_search",
            execution_time=1.5,
            sources_used=["test"],
            query_count=1
        )
        
        assert len(result.documents) == 2
        assert result.total_count == 2
        assert result.execution_time == 1.5
    
    def test_filter_by_source_type(self):
        """测试按源类型过滤"""
        documents = [
            Document("Title 1", "Content 1", "https://example.com/1", "test", "web"),
            Document("Title 2", "Content 2", "https://example.com/2", "test", "academic"),
            Document("Title 3", "Content 3", "https://example.com/3", "test", "web")
        ]
        
        result = SearchResult(
            documents=documents,
            total_count=3,
            search_type="test",
            execution_time=1.0,
            sources_used=["test"],
            query_count=1
        )
        
        web_results = result.filter_by_source_type("web")
        assert len(web_results.documents) == 2
        assert all(doc.source_type == "web" for doc in web_results.documents)
    
    def test_sort_by_relevance(self):
        """测试按相关性排序"""
        documents = [
            Document("Title 1", "Content 1", "https://example.com/1", "test", "web", score=0.5),
            Document("Title 2", "Content 2", "https://example.com/2", "test", "web", score=0.9),
            Document("Title 3", "Content 3", "https://example.com/3", "test", "web", score=0.7)
        ]
        
        result = SearchResult(
            documents=documents,
            total_count=3,
            search_type="test",
            execution_time=1.0,
            sources_used=["test"],
            query_count=1
        )
        
        sorted_result = result.sort_by_relevance()
        scores = [doc.score for doc in sorted_result.documents]
        assert scores == [0.9, 0.7, 0.5]  # 降序排列


class TestSearchGenerator:
    """测试搜索生成器"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        config = Mock(spec=SearchConfig)
        config.has_api_key.return_value = False  # 默认无API密钥
        config.max_workers = 4
        config.request_timeout = 30.0
        return config
    
    @pytest.fixture
    def search_generator(self, mock_config):
        """创建搜索生成器实例"""
        with patch('search_mcp.generators.TavilyCollector'), \
             patch('search_mcp.generators.BraveSearchCollector'), \
             patch('search_mcp.generators.GoogleSearchCollector'), \
             patch('search_mcp.generators.ArxivCollector'), \
             patch('search_mcp.generators.AcademicCollector'), \
             patch('search_mcp.generators.NewsCollector'):
            generator = SearchGenerator(mock_config)
            return generator
    
    def test_generator_initialization(self, search_generator):
        """测试生成器初始化"""
        assert isinstance(search_generator.collectors, dict)
        assert isinstance(search_generator.source_types, dict)
        assert 'web' in search_generator.source_types
        assert 'academic' in search_generator.source_types
        assert 'news' in search_generator.source_types
    
    def test_get_available_sources(self, search_generator):
        """测试获取可用数据源"""
        sources = search_generator.get_available_sources()
        assert isinstance(sources, dict)
        assert 'web' in sources
        assert 'academic' in sources
        assert 'news' in sources
    
    def test_determine_source_type(self, search_generator):
        """测试确定数据源类型"""
        assert search_generator._determine_source_type('arxiv', {}) == 'academic'
        assert search_generator._determine_source_type('academic', {}) == 'academic'
        assert search_generator._determine_source_type('news', {}) == 'news'
        assert search_generator._determine_source_type('tavily', {}) == 'web'
    
    def test_extract_publish_date(self, search_generator):
        """测试日期提取"""
        # 测试年份整数
        result1 = {'year': 2023}
        date1 = search_generator._extract_publish_date(result1)
        assert date1 == "2023-01-01"
        
        # 测试ISO格式日期
        result2 = {'published': '2023-12-01T10:00:00Z'}
        date2 = search_generator._extract_publish_date(result2)
        assert date2 == "2023-12-01"
        
        # 测试无日期
        result3 = {}
        date3 = search_generator._extract_publish_date(result3)
        assert date3 is None
    
    def test_standardize_results(self, search_generator):
        """测试结果标准化"""
        raw_results = [
            {
                'title': 'Test Article',
                'content': 'Test content',
                'url': 'https://example.com/article',
                'authors': ['Author 1', 'Author 2'],
                'published': '2023-12-01',
                'score': 0.8
            }
        ]
        
        documents = search_generator._standardize_results(raw_results, 'test')
        
        assert len(documents) == 1
        doc = documents[0]
        assert doc.title == 'Test Article'
        assert doc.content == 'Test content'
        assert doc.url == 'https://example.com/article'
        assert doc.authors == ['Author 1', 'Author 2']
        assert doc.score == 0.8
    
    def test_parallel_search_empty_queries(self, search_generator):
        """测试空查询的并行搜索"""
        results = search_generator.parallel_search([])
        assert results == []
    
    def test_parallel_search_no_sources(self, search_generator):
        """测试无可用数据源的并行搜索"""
        # 模拟无可用收集器
        search_generator.collectors = {}
        results = search_generator.parallel_search(['test query'])
        assert results == []


class TestSearchLogger:
    """测试搜索日志器"""
    
    @pytest.fixture
    def logger_config(self):
        """日志配置"""
        return {
            'log_level': 'INFO',
            'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'enable_file_logging': False,
            'log_file_path': None
        }
    
    def test_logger_creation(self, logger_config):
        """测试日志器创建"""
        search_logger = SearchLogger(logger_config)
        assert search_logger.config == logger_config
        assert hasattr(search_logger, 'logger')
        assert isinstance(search_logger.search_logs, list)
    
    def test_log_search_start(self, logger_config):
        """测试记录搜索开始"""
        search_logger = SearchLogger(logger_config)
        queries = ['test query']
        sources = ['test_source']
        params = {'max_results': 5}
        
        search_logger.log_search_start(queries, sources, params)
        
        assert len(search_logger.search_logs) == 1
        log_entry = search_logger.search_logs[0]
        assert log_entry['event'] == 'search_start'
        assert log_entry['queries'] == queries
        assert log_entry['sources'] == sources
        assert log_entry['params'] == params
    
    def test_log_search_complete(self, logger_config):
        """测试记录搜索完成"""
        search_logger = SearchLogger(logger_config)
        
        search_logger.log_search_complete(
            results_count=10,
            execution_time=2.5,
            sources_used=['source1', 'source2'],
            errors=['error1']
        )
        
        assert len(search_logger.search_logs) == 1
        log_entry = search_logger.search_logs[0]
        assert log_entry['event'] == 'search_complete'
        assert log_entry['results_count'] == 10
        assert log_entry['execution_time'] == 2.5
        assert log_entry['errors'] == ['error1']
    
    def test_clear_search_logs(self, logger_config):
        """测试清除搜索日志"""
        search_logger = SearchLogger(logger_config)
        search_logger.search_logs.append({'test': 'data'})
        
        search_logger.clear_search_logs()
        assert len(search_logger.search_logs) == 0


@pytest.mark.integration
class TestMCPIntegration:
    """集成测试"""
    
    def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        # 这是一个集成测试示例
        # 在实际环境中需要设置真实的API密钥和网络连接
        pass
    
    @pytest.mark.asyncio
    async def test_async_operations(self):
        """测试异步操作"""
        # 测试异步MCP操作
        pass


# 测试运行器
def run_basic_tests():
    """运行基础测试"""
    print("🧪 运行基础功能测试...")
    
    # 测试配置
    try:
        config = SearchConfig()
        print("✅ 配置测试通过")
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
    
    # 测试Document模型
    try:
        doc = Document(
            title="Test Title",
            content="Test content",
            url="https://example.com",
            source="test",
            source_type="web"
        )
        assert doc.domain == "example.com"
        print("✅ Document模型测试通过")
    except Exception as e:
        print(f"❌ Document模型测试失败: {e}")
    
    # 测试SearchRequest模型
    try:
        request = SearchRequest(queries=["test"])
        print("✅ SearchRequest模型测试通过")
    except Exception as e:
        print(f"❌ SearchRequest模型测试失败: {e}")
    
    print("🎉 基础测试完成!")


def run_mock_search_test():
    """运行模拟搜索测试"""
    print("🔍 运行模拟搜索测试...")
    
    try:
        # 创建模拟配置
        config = SearchConfig()
        
        # 创建模拟搜索生成器
        with patch('search_mcp.generators.TavilyCollector'), \
             patch('search_mcp.generators.BraveSearchCollector'), \
             patch('search_mcp.generators.GoogleSearchCollector'), \
             patch('search_mcp.generators.ArxivCollector'), \
             patch('search_mcp.generators.AcademicCollector'), \
             patch('search_mcp.generators.NewsCollector'):
            
            generator = SearchGenerator(config)
            
            # 测试获取可用数据源
            sources = generator.get_available_sources()
            print(f"可用数据源: {sources}")
            
            # 测试空查询
            results = generator.parallel_search([])
            assert results == []
            print("✅ 空查询测试通过")
            
            print("✅ 模拟搜索测试通过")
            
    except Exception as e:
        print(f"❌ 模拟搜索测试失败: {e}")
    
    print("🎉 模拟搜索测试完成!")


if __name__ == "__main__":
    print("🚀 开始运行Search MCP测试...")
    
    # 运行基础测试
    run_basic_tests()
    print()
    
    # 运行模拟搜索测试
    run_mock_search_test()
    print()
    
    print("✨ 所有测试完成!")
    print("\n要运行完整的pytest测试套件，请使用:")
    print("  cd search_mcp && python -m pytest tests/ -v") 