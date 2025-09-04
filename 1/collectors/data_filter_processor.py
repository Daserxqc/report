#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据筛选和评分处理器
用于对收集的资料进行质量评估和筛选
"""

import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


@dataclass
class DataSource:
    """数据源信息"""
    content: str
    url: str
    title: str
    source_type: str  # 'academic', 'news', 'market', 'web'
    publish_date: Optional[str] = None
    author: Optional[str] = None
    domain: Optional[str] = None
    word_count: int = 0
    
    def __post_init__(self):
        if self.domain is None and self.url:
            self.domain = urlparse(self.url).netloc
        if self.word_count == 0:
            self.word_count = len(self.content.split())


@dataclass
class QualityScore:
    """质量评分"""
    relevance: float      # 相关性 0-1
    practicality: float   # 实用性 0-1
    timeliness: float     # 时效性 0-1
    authority: float      # 权威性 0-1
    completeness: float   # 完整性 0-1
    accuracy: float       # 准确性 0-1
    total_score: float = 0.0    # 总分 0-1，默认值
    
    def __post_init__(self):
        # 计算加权总分
        weights = {
            'relevance': 0.25,
            'practicality': 0.20,
            'timeliness': 0.15,
            'authority': 0.15,
            'completeness': 0.15,
            'accuracy': 0.10
        }
        
        self.total_score = (
            self.relevance * weights['relevance'] +
            self.practicality * weights['practicality'] +
            self.timeliness * weights['timeliness'] +
            self.authority * weights['authority'] +
            self.completeness * weights['completeness'] +
            self.accuracy * weights['accuracy']
        )


@dataclass
class FilteredData:
    """筛选后的数据"""
    source: DataSource
    quality_score: QualityScore
    selected_excerpts: List[str]  # 选中的关键摘录
    reasoning: str  # 评分理由
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': asdict(self.source),
            'quality_score': asdict(self.quality_score),
            'selected_excerpts': self.selected_excerpts,
            'reasoning': self.reasoning
        }


class DataFilterProcessor:
    """数据筛选处理器"""
    
    def __init__(self, llm_processor=None):
        self.llm_processor = llm_processor
        self.lock = threading.Lock()
        
        # 权威域名列表
        self.authoritative_domains = {
            'academic': ['arxiv.org', 'ieee.org', 'acm.org', 'springer.com', 'nature.com', 'sciencedirect.com'],
            'news': ['reuters.com', 'bloomberg.com', 'wsj.com', 'ft.com', 'economist.com'],
            'tech': ['techcrunch.com', 'wired.com', 'arstechnica.com', 'theverge.com'],
            'chinese': ['xinhua.net', 'people.com.cn', 'chinadaily.com.cn', 'caixin.com']
        }
        
        # 并行度配置 - 根据数据源限制设置
        self.parallel_config = {
            'brave': 2,     # Brave 有限制，少一些
            'google': 6,    # Google 可以多一些
            'tavily': 8,    # Tavily 可以多一些
            'arxiv': 4,     # 学术源适中
            'news': 5,      # 新闻源适中
            'web': 3,       # 通用网页源适中
            'default': 3    # 默认值
        }
    
    def filter_and_score_data_parallel(self, data_sources: List[DataSource], topic: str, 
                                     section_title: str, min_score: float = 0.6) -> List[FilteredData]:
        """
        并行筛选和评分数据源
        
        Args:
            data_sources: 原始数据源列表
            topic: 主题
            section_title: 章节标题
            min_score: 最低分数阈值
        
        Returns:
            筛选后的数据列表
        """
        print(f"🚀 开始并行筛选数据，共 {len(data_sources)} 个数据源")
        
        # 按数据源类型分组
        grouped_sources = self._group_sources_by_type(data_sources)
        
        filtered_data = []
        
        # 并行处理每个组
        for source_type, sources in grouped_sources.items():
            if not sources:
                continue
                
            max_workers = self.parallel_config.get(source_type, self.parallel_config['default'])
            print(f"  📊 处理 {source_type} 类数据源 {len(sources)} 个，并行度: {max_workers}")
            
            group_filtered = self._process_group_parallel(
                sources, topic, section_title, min_score, max_workers
            )
            filtered_data.extend(group_filtered)
        
        # 按分数排序
        filtered_data.sort(key=lambda x: x.quality_score.total_score, reverse=True)
        
        print(f"🎯 并行筛选完成，{len(filtered_data)} 个数据源通过筛选")
        return filtered_data
    
    def _group_sources_by_type(self, data_sources: List[DataSource]) -> Dict[str, List[DataSource]]:
        """按数据源类型分组"""
        grouped = {}
        
        for source in data_sources:
            # 根据域名或来源信息确定分组
            group_key = self._determine_group_key(source)
            if group_key not in grouped:
                grouped[group_key] = []
            grouped[group_key].append(source)
        
        return grouped
    
    def _determine_group_key(self, source: DataSource) -> str:
        """确定数据源的分组键"""
        if not source.domain:
            return source.source_type or 'default'
        
        domain_lower = source.domain.lower()
        
        # 优先检查是否来自特定搜索引擎（通过我们添加的标识）
        if 'brave.search_engine' in domain_lower:
            return 'brave'
        elif 'google.search_engine' in domain_lower:
            return 'google'
        elif 'tavily.search_engine' in domain_lower:
            return 'tavily'
        
        # 检查是否来自特定搜索引擎（通过域名匹配）
        elif 'brave' in domain_lower:
            return 'brave'
        elif 'google' in domain_lower:
            return 'google'
        elif 'tavily' in domain_lower:
            return 'tavily'
        elif 'arxiv' in domain_lower:
            return 'arxiv'
        elif any(news_domain in domain_lower for news_domain in ['reuters', 'bloomberg', 'wsj', 'ft', 'economist']):
            return 'news'
        else:
            return source.source_type or 'web'
    
    def _process_group_parallel(self, sources: List[DataSource], topic: str, 
                              section_title: str, min_score: float, max_workers: int) -> List[FilteredData]:
        """并行处理单个分组的数据源"""
        filtered_data = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_source = {
                executor.submit(self._process_single_source, source, topic, section_title, min_score): source
                for source in sources
            }
            
            # 收集结果
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    result = future.result()
                    if result:  # 通过筛选的数据
                        filtered_data.append(result)
                        with self.lock:
                            print(f"    ✅ {source.title[:50]}... 通过筛选，总分: {result.quality_score.total_score:.2f}")
                    else:
                        with self.lock:
                            print(f"    ❌ {source.title[:50]}... 未通过筛选")
                except Exception as e:
                    with self.lock:
                        print(f"    ⚠️ {source.title[:50]}... 评估出错: {str(e)}")
        
        return filtered_data
    
    def _process_single_source(self, source: DataSource, topic: str, 
                             section_title: str, min_score: float) -> Optional[FilteredData]:
        """处理单个数据源（线程安全）"""
        try:
            # 评估数据质量
            quality_score = self._evaluate_quality(source, topic, section_title)
            
            # 如果分数不达标，直接返回None
            if quality_score.total_score < min_score:
                return None
            
            # 筛选关键摘录
            excerpts = self._extract_key_excerpts(source, topic, section_title)
            
            # 生成评分理由
            reasoning = self._generate_reasoning(source, quality_score)
            
            return FilteredData(
                source=source,
                quality_score=quality_score,
                selected_excerpts=excerpts,
                reasoning=reasoning
            )
            
        except Exception as e:
            # 记录错误但不抛出，让调用者处理
            return None
    
    def filter_and_score_data(self, data_sources: List[DataSource], topic: str, 
                            section_title: str, min_score: float = 0.6) -> List[FilteredData]:
        """
        筛选和评分数据源（保持原有接口，优先使用并行版本）
        
        Args:
            data_sources: 原始数据源列表
            topic: 主题
            section_title: 章节标题
            min_score: 最低分数阈值
        
        Returns:
            筛选后的数据列表
        """
        # 如果数据源少于3个，使用串行处理
        if len(data_sources) < 3:
            return self._filter_and_score_data_serial(data_sources, topic, section_title, min_score)
        
        # 否则使用并行处理
        return self.filter_and_score_data_parallel(data_sources, topic, section_title, min_score)
    
    def _filter_and_score_data_serial(self, data_sources: List[DataSource], topic: str, 
                                    section_title: str, min_score: float = 0.6) -> List[FilteredData]:
        """
        串行筛选和评分数据源（原始实现）
        """
        print(f"🔍 开始串行筛选数据，共 {len(data_sources)} 个数据源")
        
        filtered_data = []
        
        for i, source in enumerate(data_sources):
            print(f"  正在评估数据源 {i+1}/{len(data_sources)}: {source.title[:50]}...")
            
            try:
                # 评估数据质量
                quality_score = self._evaluate_quality(source, topic, section_title)
                
                # 筛选关键摘录
                excerpts = self._extract_key_excerpts(source, topic, section_title)
                
                # 生成评分理由
                reasoning = self._generate_reasoning(source, quality_score)
                
                # 如果分数达到阈值，加入筛选结果
                if quality_score.total_score >= min_score:
                    filtered_data.append(FilteredData(
                        source=source,
                        quality_score=quality_score,
                        selected_excerpts=excerpts,
                        reasoning=reasoning
                    ))
                    print(f"    ✅ 通过筛选，总分: {quality_score.total_score:.2f}")
                else:
                    print(f"    ❌ 未通过筛选，总分: {quality_score.total_score:.2f}")
                    
            except Exception as e:
                print(f"    ⚠️ 评估出错: {str(e)}")
                continue
        
        # 按分数排序
        filtered_data.sort(key=lambda x: x.quality_score.total_score, reverse=True)
        
        print(f"🎯 串行筛选完成，{len(filtered_data)} 个数据源通过筛选")
        return filtered_data
    
    def _evaluate_quality(self, source: DataSource, topic: str, section_title: str) -> QualityScore:
        """评估数据质量"""
        
        # 1. 权威性评分
        authority_score = self._evaluate_authority(source)
        
        # 2. 时效性评分
        timeliness_score = self._evaluate_timeliness(source)
        
        # 3. 完整性评分
        completeness_score = self._evaluate_completeness(source)
        
        # 4. 使用LLM评估相关性、实用性、准确性
        if self.llm_processor:
            llm_scores = self._evaluate_with_llm(source, topic, section_title)
            relevance_score = llm_scores.get('relevance', 0.7)
            practicality_score = llm_scores.get('practicality', 0.7)
            accuracy_score = llm_scores.get('accuracy', 0.7)
        else:
            # 回退到规则评分
            relevance_score = self._evaluate_relevance_fallback(source, topic, section_title)
            practicality_score = self._evaluate_practicality_fallback(source)
            accuracy_score = self._evaluate_accuracy_fallback(source)
        
        return QualityScore(
            relevance=relevance_score,
            practicality=practicality_score,
            timeliness=timeliness_score,
            authority=authority_score,
            completeness=completeness_score,
            accuracy=accuracy_score
        )
    
    def _evaluate_authority(self, source: DataSource) -> float:
        """评估权威性"""
        if not source.domain:
            return 0.3
        
        # 检查是否在权威域名列表中
        for category, domains in self.authoritative_domains.items():
            if any(domain in source.domain for domain in domains):
                return 0.9
        
        # 根据域名特征评分
        domain_lower = source.domain.lower()
        
        # 学术机构
        if any(ext in domain_lower for ext in ['.edu', '.ac.', '.org']):
            return 0.8
        
        # 政府机构
        if any(ext in domain_lower for ext in ['.gov', '.mil']):
            return 0.85
        
        # 商业域名
        if domain_lower.endswith('.com'):
            return 0.5
        
        return 0.4
    
    def _evaluate_timeliness(self, source: DataSource) -> float:
        """评估时效性"""
        if not source.publish_date:
            return 0.5  # 无日期信息，给中等分
        
        try:
            # 尝试解析日期
            pub_date = datetime.strptime(source.publish_date, '%Y-%m-%d')
            now = datetime.now()
            
            # 计算天数差
            days_diff = (now - pub_date).days
            
            # 根据天数差评分
            if days_diff <= 30:
                return 1.0      # 30天内：最新
            elif days_diff <= 90:
                return 0.9      # 3个月内：很新
            elif days_diff <= 180:
                return 0.8      # 6个月内：较新
            elif days_diff <= 365:
                return 0.6      # 1年内：一般
            elif days_diff <= 730:
                return 0.4      # 2年内：较旧
            else:
                return 0.2      # 2年以上：很旧
                
        except:
            return 0.5
    
    def _evaluate_completeness(self, source: DataSource) -> float:
        """评估完整性"""
        content_length = len(source.content)
        
        # 根据内容长度评分
        if content_length >= 2000:
            return 1.0      # 长文章
        elif content_length >= 1000:
            return 0.8      # 中等长度
        elif content_length >= 500:
            return 0.6      # 短文章
        elif content_length >= 200:
            return 0.4      # 很短
        else:
            return 0.2      # 极短
    
    def _evaluate_with_llm(self, source: DataSource, topic: str, section_title: str) -> Dict[str, float]:
        """使用LLM评估相关性、实用性、准确性"""
        
        evaluation_prompt = f"""
请你作为一个专业的内容质量评估专家，对以下内容进行评分。

**评估主题**: {topic}
**章节标题**: {section_title}
**内容来源**: {source.title}
**内容摘要**: {source.content[:800]}...

请从以下三个维度对内容进行评分（0-1分，保留两位小数）：

1. **相关性（Relevance）**: 内容与主题和章节的匹配度
   - 1.0: 高度相关，直接对应主题
   - 0.8: 相关性强，大部分内容符合
   - 0.6: 中等相关，部分内容符合
   - 0.4: 相关性弱，少部分内容符合
   - 0.2: 基本不相关

2. **实用性（Practicality）**: 内容的实际应用价值
   - 1.0: 高度实用，有具体方案或案例
   - 0.8: 实用性强，有操作指导
   - 0.6: 中等实用，有参考价值
   - 0.4: 实用性弱，主要是理论
   - 0.2: 基本无实用价值

3. **准确性（Accuracy）**: 内容的准确性和可信度
   - 1.0: 高度准确，有数据支撑
   - 0.8: 准确性强，逻辑清晰
   - 0.6: 中等准确，基本可信
   - 0.4: 准确性待验证
   - 0.2: 存在明显错误

请以JSON格式返回评分结果：
```json
{{
    "relevance": 0.XX,
    "practicality": 0.XX,
    "accuracy": 0.XX,
    "reasoning": "简要说明评分理由"
}}
```
"""
        
        try:
            response = self.llm_processor.call_llm_api(evaluation_prompt, 
                                                      "你是一位专业的内容质量评估专家。请严格按照要求返回JSON格式的评分结果。",
                                                      temperature=0.3)
            
            # 尝试解析JSON响应
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
                return {
                    'relevance': float(result.get('relevance', 0.7)),
                    'practicality': float(result.get('practicality', 0.7)),
                    'accuracy': float(result.get('accuracy', 0.7)),
                    'reasoning': result.get('reasoning', '')
                }
            else:
                # 如果JSON解析失败，尝试从文本中提取数值
                relevance = self._extract_score_from_text(response, 'relevance')
                practicality = self._extract_score_from_text(response, 'practicality')
                accuracy = self._extract_score_from_text(response, 'accuracy')
                
                return {
                    'relevance': relevance,
                    'practicality': practicality,
                    'accuracy': accuracy,
                    'reasoning': '基于文本分析的评分'
                }
                
        except Exception as e:
            print(f"LLM评估出错: {str(e)}")
            return {
                'relevance': 0.7,
                'practicality': 0.7,
                'accuracy': 0.7,
                'reasoning': '评估过程中出现错误，使用默认分数'
            }
    
    def _extract_score_from_text(self, text: str, score_type: str) -> float:
        """从文本中提取评分"""
        pattern = rf'{score_type}["\']?\s*:\s*([0-9.]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except:
                pass
        return 0.7
    
    def _evaluate_relevance_fallback(self, source: DataSource, topic: str, section_title: str) -> float:
        """回退的相关性评估"""
        content_lower = source.content.lower()
        title_lower = source.title.lower()
        topic_lower = topic.lower()
        section_lower = section_title.lower()
        
        # 关键词匹配评分
        topic_keywords = topic_lower.split()
        section_keywords = section_lower.split()
        
        matches = 0
        total_keywords = len(topic_keywords) + len(section_keywords)
        
        for keyword in topic_keywords + section_keywords:
            if keyword in content_lower or keyword in title_lower:
                matches += 1
        
        return min(matches / total_keywords * 2, 1.0)
    
    def _evaluate_practicality_fallback(self, source: DataSource) -> float:
        """回退的实用性评估"""
        practical_indicators = [
            '案例', '实例', '应用', '方法', '步骤', '实现', '操作', '指南',
            'case', 'example', 'application', 'method', 'step', 'implementation'
        ]
        
        content_lower = source.content.lower()
        matches = sum(1 for indicator in practical_indicators if indicator in content_lower)
        
        return min(matches / len(practical_indicators) * 3, 1.0)
    
    def _evaluate_accuracy_fallback(self, source: DataSource) -> float:
        """回退的准确性评估"""
        # 基于来源类型和内容特征
        base_score = 0.7
        
        # 学术来源加分
        if source.source_type == 'academic':
            base_score += 0.2
        
        # 有数据支撑加分
        if any(indicator in source.content.lower() for indicator in ['数据', '统计', '研究', 'data', 'study', 'research']):
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _extract_key_excerpts(self, source: DataSource, topic: str, section_title: str) -> List[str]:
        """提取关键摘录"""
        
        if self.llm_processor:
            return self._extract_excerpts_with_llm(source, topic, section_title)
        else:
            return self._extract_excerpts_fallback(source, topic, section_title)
    
    def _extract_excerpts_with_llm(self, source: DataSource, topic: str, section_title: str) -> List[str]:
        """使用LLM提取关键摘录"""
        
        excerpt_prompt = f"""
请从以下内容中提取3-5个最重要的关键摘录，这些摘录应该：
1. 与主题 "{topic}" 和章节 "{section_title}" 高度相关
2. 包含具体的数据、案例或观点
3. 每个摘录长度控制在50-150字之间
4. 保持原文的准确性

**内容来源**: {source.title}
**内容**: {source.content}

请按以下格式返回摘录：
```
摘录1: [具体内容]
摘录2: [具体内容]
摘录3: [具体内容]
...
```
"""
        
        try:
            response = self.llm_processor.call_llm_api(excerpt_prompt, 
                                                      "你是一位专业的内容分析专家，擅长提取关键信息。请严格按照要求的格式返回摘录。",
                                                      temperature=0.3)
            
            # 解析摘录
            excerpts = []
            for line in response.split('\n'):
                if line.strip().startswith('摘录'):
                    excerpt = line.split(':', 1)[1].strip()
                    if excerpt and len(excerpt) >= 10:
                        excerpts.append(excerpt)
            
            return excerpts[:5]  # 最多5个摘录
            
        except Exception as e:
            print(f"LLM摘录提取出错: {str(e)}")
            return self._extract_excerpts_fallback(source, topic, section_title)
    
    def _extract_excerpts_fallback(self, source: DataSource, topic: str, section_title: str) -> List[str]:
        """回退的摘录提取"""
        sentences = source.content.split('。')
        topic_lower = topic.lower()
        section_lower = section_title.lower()
        
        scored_sentences = []
        for sentence in sentences:
            if len(sentence.strip()) < 20:
                continue
                
            sentence_lower = sentence.lower()
            score = 0
            
            # 关键词匹配
            for keyword in topic_lower.split() + section_lower.split():
                if keyword in sentence_lower:
                    score += 1
            
            # 数据指标
            if any(indicator in sentence_lower for indicator in ['%', '数据', '统计', '研究', '调查']):
                score += 2
            
            if score > 0:
                scored_sentences.append((sentence.strip(), score))
        
        # 排序并返回前5个
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        return [sentence for sentence, _ in scored_sentences[:5]]
    
    def _generate_reasoning(self, source: DataSource, quality_score: QualityScore) -> str:
        """生成评分理由"""
        reasons = []
        
        # 权威性
        if quality_score.authority >= 0.8:
            reasons.append(f"来源权威性高（{quality_score.authority:.2f}）")
        elif quality_score.authority <= 0.4:
            reasons.append(f"来源权威性较低（{quality_score.authority:.2f}）")
        
        # 时效性
        if quality_score.timeliness >= 0.8:
            reasons.append(f"内容时效性强（{quality_score.timeliness:.2f}）")
        elif quality_score.timeliness <= 0.4:
            reasons.append(f"内容时效性较弱（{quality_score.timeliness:.2f}）")
        
        # 相关性
        if quality_score.relevance >= 0.8:
            reasons.append(f"内容高度相关（{quality_score.relevance:.2f}）")
        elif quality_score.relevance <= 0.4:
            reasons.append(f"内容相关性较低（{quality_score.relevance:.2f}）")
        
        # 实用性
        if quality_score.practicality >= 0.8:
            reasons.append(f"实用价值高（{quality_score.practicality:.2f}）")
        elif quality_score.practicality <= 0.4:
            reasons.append(f"实用价值较低（{quality_score.practicality:.2f}）")
        
        return "；".join(reasons) if reasons else "综合评估结果" 