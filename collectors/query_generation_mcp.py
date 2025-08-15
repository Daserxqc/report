import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from collectors.llm_processor import LLMProcessor


@dataclass
class QueryContext:
    """查询上下文数据结构"""
    topic: str
    strategy: str  # 'initial', 'iterative', 'targeted'
    context: str = ""
    existing_data: List[Dict] = None
    target_audience: str = "通用"
    report_type: str = "综合报告"
    
    def __post_init__(self):
        if self.existing_data is None:
            self.existing_data = []


class QueryGenerationMcp:
    """
    查询生成MCP (Model Context Protocol)
    
    用途：基于上下文能生成高效的搜索查询。
    
    职责：
    - 为初始搜索生成广泛的查询
    - 根据已有信息生成迭代式、补充性的查询
    - 根据章节标题生成高度针对性的查询
    
    输入：topic: str, strategy: str (e.g., 'initial', 'iterative', 'targeted'), context: str = ""
    输出：list[str]
    
    实现要点：核心是精心设计的Prompt，引导LLM进行思维链推理。例如，'iterative'策略的
             Prompt："...基于以下已知信息: [context]。请生成3个全新的查询，以探索我们尚未了解的方面。"
    """
    
    def __init__(self):
        """初始化QueryGenerationMcp"""
        try:
            self.llm_processor = LLMProcessor()
            self.has_llm = True
            print("✅ QueryGenerationMcp初始化完成")
        except Exception as e:
            print(f"⚠️ LLM处理器初始化失败: {str(e)}")
            self.has_llm = False
        
        # 预定义的查询策略模板
        self.strategy_templates = self._load_strategy_templates()
    
    def _load_strategy_templates(self) -> Dict[str, str]:
        """加载不同策略的Prompt模板"""
        return {
            "initial": """
作为一个专业的信息研究员，请为主题"{topic}"生成初始搜索查询。

报告类型：{report_type}
目标受众：{target_audience}

任务要求：
1. 生成5-8个多样化的搜索查询
2. 覆盖主题的核心概念、最新发展、应用场景、挑战问题
3. 查询应该具体且可搜索，避免过于宽泛
4. 包含中英文关键词组合，提高搜索覆盖面

请按以下格式输出JSON：
```json
{{
    "queries": [
        "查询1",
        "查询2",
        "..."
    ],
    "reasoning": "生成这些查询的理由和策略说明"
}}
```
""",
            
            "iterative": """
基于以下已知信息和搜索结果，为主题"{topic}"生成补充性查询。

已知信息摘要：
{context}

现有数据类型：{existing_data_summary}

任务要求：
1. 分析已有信息的覆盖面和缺口
2. 生成3-5个全新的、补充性的查询
3. 重点关注尚未充分探索的方面
4. 避免与已有查询重复

思维链推理：
1. 已有信息覆盖了哪些方面？
2. 还缺少哪些关键信息？
3. 哪些角度需要更深入的探索？
4. 如何设计查询来填补这些空白？

请按以下格式输出JSON：
```json
{{
    "gaps_identified": ["发现的信息缺口1", "缺口2", "..."],
    "queries": [
        "补充查询1",
        "补充查询2",
        "..."
    ],
    "reasoning": "基于缺口分析生成查询的理由"
}}
```
""",
            
            "targeted": """
为报告章节"{section_title}"生成高度针对性的搜索查询。

主题：{topic}
章节信息：{section_context}
报告整体背景：{context}

任务要求：
1. 生成3-4个专门针对该章节的精准查询
2. 查询应该能获取该章节所需的具体信息
3. 考虑章节在整个报告中的作用和位置
4. 确保查询的专业性和针对性

请按以下格式输出JSON：
```json
{{
    "section_focus": "该章节的核心关注点",
    "queries": [
        "针对性查询1",
        "针对性查询2",
        "..."
    ],
    "expected_content": "期望通过这些查询获得的信息类型"
}}
```
""",
            
            "academic": """
为学术研究主题"{topic}"生成学术导向的搜索查询。

研究背景：{context}
研究深度要求：{academic_level}

任务要求：
1. 生成4-6个学术性搜索查询
2. 包含专业术语和概念
3. 覆盖理论基础、研究方法、最新进展
4. 适合在学术数据库中搜索

请按以下格式输出JSON：
```json
{{
    "academic_areas": ["理论基础", "研究方法", "应用实例", "..."],
    "queries": [
        "学术查询1",
        "学术查询2", 
        "..."
    ],
    "keywords": ["关键学术术语1", "术语2", "..."]
}}
```
""",
            
            "news": """
为新闻话题"{topic}"生成时效性搜索查询。

时间范围：{time_range}
关注焦点：{news_focus}
背景信息：{context}

任务要求：
1. 生成4-5个新闻导向的搜索查询
2. 关注最新动态、突发事件、趋势变化
3. 包含时间敏感的关键词
4. 适合在新闻平台搜索

请按以下格式输出JSON：
```json
{{
    "news_angles": ["突发事件", "政策变化", "市场动态", "..."],
    "queries": [
        "新闻查询1",
        "新闻查询2",
        "..."
    ],
    "urgency_level": "信息时效性评估"
}}
```
"""
        }
    
    def generate_queries(self, 
                        topic: str, 
                        strategy: str = "initial",
                        context: str = "",
                        **kwargs) -> List[str]:
        """
        生成搜索查询
        
        Args:
            topic: 主题
            strategy: 策略 ('initial', 'iterative', 'targeted', 'academic', 'news')
            context: 上下文信息
            **kwargs: 其他参数
            
        Returns:
            List[str]: 生成的查询列表
        """
        if not self.has_llm:
            return self._fallback_query_generation(topic, strategy, context)
        
        try:
            # 构建查询上下文
            query_context = QueryContext(
                topic=topic,
                strategy=strategy,
                context=context,
                **kwargs
            )
            
            # 生成查询
            queries = self._generate_queries_with_llm(query_context)
            
            print(f"✅ 使用{strategy}策略为'{topic}'生成了{len(queries)}个查询")
            return queries
            
        except Exception as e:
            print(f"❌ LLM查询生成失败: {str(e)}")
            return self._fallback_query_generation(topic, strategy, context)
    
    def _generate_queries_with_llm(self, query_context: QueryContext) -> List[str]:
        """使用LLM生成查询"""
        template = self.strategy_templates.get(query_context.strategy, self.strategy_templates["initial"])
        
        # 准备模板参数
        template_params = {
            "topic": query_context.topic,
            "context": query_context.context,
            "report_type": query_context.report_type,
            "target_audience": query_context.target_audience,
            "existing_data_summary": self._summarize_existing_data(query_context.existing_data)
        }
        
        # 添加策略特定参数
        if query_context.strategy == "targeted":
            template_params.update({
                "section_title": query_context.context.split("|")[0] if "|" in query_context.context else "未指定章节",
                "section_context": query_context.context.split("|")[1] if "|" in query_context.context else query_context.context
            })
        elif query_context.strategy == "academic":
            template_params["academic_level"] = "研究生/专业研究人员级别"
        elif query_context.strategy == "news":
            template_params.update({
                "time_range": "最近30天",
                "news_focus": "行业动态和政策变化"
            })
        
        # 格式化prompt
        prompt = template.format(**template_params)
        
        # 调用LLM
        response = self.llm_processor.process_request(prompt)
        
        # 解析响应
        queries = self._parse_llm_response(response, query_context.strategy)
        
        # 验证和过滤查询
        return self._validate_queries(queries, query_context.topic)
    
    def _parse_llm_response(self, response: str, strategy: str) -> List[str]:
        """解析LLM响应提取查询"""
        try:
            # 尝试解析JSON格式
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                # 查找JSON对象
                start_idx = response.find("{")
                end_idx = response.rfind("}") + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response[start_idx:end_idx]
                else:
                    raise ValueError("无法找到JSON格式")
            
            parsed_data = json.loads(json_str)
            queries = parsed_data.get("queries", [])
            
            if queries:
                # 记录推理过程（如果有）
                if "reasoning" in parsed_data:
                    print(f"💡 查询生成推理: {parsed_data['reasoning']}")
                return queries
            else:
                raise ValueError("解析结果中没有queries字段")
                
        except Exception as e:
            print(f"⚠️ JSON解析失败: {str(e)}")
            return self._extract_queries_from_text(response)
    
    def _extract_queries_from_text(self, response: str) -> List[str]:
        """从文本中提取查询（备用方法）"""
        queries = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            # 查找类似查询的行
            if (any(marker in line.lower() for marker in ['查询', 'query', '搜索', 'search']) or 
                line.startswith('"') or 
                line.startswith('- ') or 
                line.startswith('* ') or
                line.startswith(tuple('123456789'))):
                
                # 清理和提取查询
                query = line
                for prefix in ['"', '- ', '* ', '1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ', '9. ']:
                    if query.startswith(prefix):
                        query = query[len(prefix):].strip()
                
                if query.endswith('"'):
                    query = query[:-1]
                
                if len(query) > 5 and len(query) < 200:  # 合理的查询长度
                    queries.append(query)
        
        return queries[:8]  # 最多返回8个查询
    
    def _validate_queries(self, queries: List[str], topic: str) -> List[str]:
        """验证和优化查询"""
        validated_queries = []
        
        for query in queries:
            query = query.strip()
            
            # 基本验证
            if not query or len(query) < 3 or len(query) > 200:
                continue
            
            # 去除重复
            if query not in validated_queries:
                validated_queries.append(query)
        
        # 确保至少有一些查询
        if not validated_queries:
            validated_queries = self._fallback_query_generation(topic, "initial", "")
        
        return validated_queries
    
    def _summarize_existing_data(self, existing_data: List[Dict]) -> str:
        """总结已有数据"""
        if not existing_data:
            return "无已有数据"
        
        data_types = set()
        source_types = set()
        
        for item in existing_data:
            if isinstance(item, dict):
                if 'source_type' in item:
                    source_types.add(item['source_type'])
                if 'title' in item:
                    data_types.add("标题信息")
                if 'content' in item:
                    data_types.add("内容摘要")
        
        summary = f"已有{len(existing_data)}条数据，"
        if source_types:
            summary += f"来源类型: {', '.join(source_types)}，"
        if data_types:
            summary += f"数据类型: {', '.join(data_types)}"
        
        return summary
    
    def _fallback_query_generation(self, topic: str, strategy: str, context: str) -> List[str]:
        """备用查询生成方法"""
        base_queries = [
            f"{topic} 最新发展",
            f"{topic} 技术原理",
            f"{topic} 应用案例",
            f"{topic} 市场趋势",
            f"{topic} 挑战问题"
        ]
        
        if strategy == "academic":
            academic_queries = [
                f"{topic} research papers",
                f"{topic} 学术研究",
                f"{topic} 理论基础",
                f"{topic} methodology"
            ]
            return academic_queries
            
        elif strategy == "news":
            news_queries = [
                f"{topic} 最新消息",
                f"{topic} 行业动态",
                f"{topic} 政策变化",
                f"{topic} breaking news"
            ]
            return news_queries
            
        elif strategy == "iterative" and context:
            # 基于上下文生成补充查询
            if "技术" in context:
                return [f"{topic} 商业应用", f"{topic} 市场分析", f"{topic} 用户体验"]
            elif "市场" in context:
                return [f"{topic} 技术详解", f"{topic} 产品评测", f"{topic} 专家观点"]
        
        return base_queries
    
    def generate_multi_strategy_queries(self, 
                                      topic: str,
                                      strategies: List[str] = None,
                                      context: str = "",
                                      **kwargs) -> Dict[str, List[str]]:
        """
        使用多种策略生成查询
        
        Args:
            topic: 主题
            strategies: 策略列表
            context: 上下文
            **kwargs: 其他参数
            
        Returns:
            Dict[str, List[str]]: 各策略对应的查询列表
        """
        if strategies is None:
            strategies = ["initial", "academic", "news"]
        
        all_queries = {}
        
        for strategy in strategies:
            try:
                queries = self.generate_queries(topic, strategy, context, **kwargs)
                all_queries[strategy] = queries
                print(f"  📋 {strategy}策略: {len(queries)}个查询")
            except Exception as e:
                print(f"  ❌ {strategy}策略失败: {str(e)}")
                all_queries[strategy] = []
        
        return all_queries
    
    def refine_queries_based_on_results(self, 
                                      original_queries: List[str],
                                      search_results: List[Dict],
                                      topic: str) -> List[str]:
        """
        基于搜索结果优化查询
        
        Args:
            original_queries: 原始查询
            search_results: 搜索结果
            topic: 主题
            
        Returns:
            List[str]: 优化后的查询
        """
        if not self.has_llm or not search_results:
            return original_queries
        
        # 分析搜索结果质量
        results_summary = self._analyze_search_results(search_results)
        
        # 生成优化查询
        context = f"原始查询: {original_queries}\n搜索结果分析: {results_summary}"
        
        refined_queries = self.generate_queries(
            topic=topic,
            strategy="iterative", 
            context=context
        )
        
        return refined_queries
    
    def _analyze_search_results(self, search_results: List[Dict]) -> str:
        """分析搜索结果质量"""
        if not search_results:
            return "无搜索结果"
        
        total_results = len(search_results)
        source_types = {}
        
        for result in search_results:
            source_type = result.get('source_type', 'unknown')
            source_types[source_type] = source_types.get(source_type, 0) + 1
        
        analysis = f"共{total_results}条结果，"
        analysis += f"来源分布: {dict(source_types)}"
        
        return analysis 