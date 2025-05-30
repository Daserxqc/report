# 报告生成工具函数
import os
from pathlib import Path
import json
from collectors.llm_processor import LLMProcessor

def fix_existing_reports(report_dir):
    """
    修复现有的报告文件
    
    Args:
        report_dir (str): 报告目录路径
    """
    # 获取所有.md文件
    report_dir = Path(report_dir)
    report_files = list(report_dir.glob("*.md"))
    
    if not report_files:
        print(f"未在 {report_dir} 中找到任何.md文件")
        return
    
    print(f"找到 {len(report_files)} 个Markdown文件")
    
    fixed_count = 0
    for file_path in report_files:
        if "fixed" in file_path.name:
            print(f"跳过已修复的文件: {file_path.name}")
            continue
            
        print(f"处理文件: {file_path.name}")
        
        # 读取原始二进制内容
        with open(file_path, "rb") as f:
            raw_data = f.read()
            
        # 尝试不同编码读取
        success = False
        for encoding in ['utf-8', 'gbk', 'gb18030', 'latin1']:
            try:
                content = raw_data.decode(encoding)
                chinese_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
                
                if chinese_count > 0:
                    print(f"  使用{encoding}解码成功，检测到{chinese_count}个中文字符")
                    
                    # 创建修复后的文件
                    fixed_path = file_path.with_name(f"{file_path.stem}_fixed.md")
                    with open(fixed_path, "w", encoding="utf-8-sig") as f:
                        f.write(content)
                        
                    print(f"  已修复并保存为: {fixed_path}")
                    fixed_count += 1
                    success = True
                    break
            except UnicodeDecodeError:
                continue
        
        if not success:
            print(f"  无法修复文件 {file_path.name}，所有编码尝试均失败")
            
    print(f"\n共处理了 {len(report_files)} 个文件，成功修复 {fixed_count} 个")

def safe_save_report(report_content, filename):
    """
    安全保存报告内容到文件，确保中文字符正确编码
    
    Args:
        report_content (str): 报告内容
        filename (str): 文件名
        
    Returns:
        bool: 保存是否成功
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        
        # 验证内容中的中文字符
        chinese_count = sum(1 for c in report_content if '\u4e00' <= c <= '\u9fff')
        print(f"报告包含 {chinese_count} 个中文字符")
        
        # 确保使用UTF-8-SIG (带BOM标记)编码保存
        with open(filename, "w", encoding="utf-8-sig") as f:
            f.write(report_content)
        print(f"报告已保存: {filename} ({os.path.getsize(filename)} 字节)")
        
        # 验证文件内容
        with open(filename, "r", encoding="utf-8-sig") as f:
            content = f.read()
            read_chinese = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
            print(f"验证成功: 写入{chinese_count}个中文字符，读取到{read_chinese}个中文字符")
            
        return True
    except Exception as e:
        print(f"保存报告失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

class ReportEvaluator:
    """
    报告评估器 - 根据报告类型自适应评估维度
    """
    
    def __init__(self, api_key=None, model=None):
        # 定义评估维度及其适用性
        self.evaluation_dimensions = {
            "Structure": {
                "description": "结构性",
                "criteria": "报告的逻辑结构是否清晰，章节安排是否合理，内容组织是否有序",
                "applies_to": ["insights", "news", "research"],
                "weight": {"insights": 0.15, "news": 0.15, "research": 0.15}
            },
            "Coherence": {
                "description": "连贯性", 
                "criteria": "内容之间的逻辑关联是否紧密，论述是否连贯流畅",
                "applies_to": ["insights", "news", "research"],
                "weight": {"insights": 0.15, "news": 0.10, "research": 0.15}
            },
            "Comprehensiveness": {
                "description": "全面性",
                "criteria": "是否覆盖了主题的关键方面，信息是否完整",
                "applies_to": ["insights", "news", "research"],
                "weight": {"insights": 0.15, "news": 0.20, "research": 0.15}
            },
            "Depth": {
                "description": "深度",
                "criteria": "分析的深入程度，是否有深层次的见解和思考",
                "applies_to": ["insights", "research"],
                "weight": {"insights": 0.20, "research": 0.25}
            },
            "Data_Evidence": {
                "description": "数据与证据",
                "criteria": "是否有充分的数据支撑，引用的资料是否可信",
                "applies_to": ["insights", "research"],
                "weight": {"insights": 0.15, "research": 0.20}
            },
            "Actionability": {
                "description": "可操作性",
                "criteria": "是否提供了可执行的建议或明确的行动方向",
                "applies_to": ["insights"],
                "weight": {"insights": 0.20}
            },
            "Timeliness": {
                "description": "时效性",
                "criteria": "信息是否及时，是否反映最新发展",
                "applies_to": ["news", "research"],
                "weight": {"news": 0.25, "research": 0.10}
            },
            "Readability": {
                "description": "可读性",
                "criteria": "语言表达是否清晰，格式是否美观，是否易于阅读理解",
                "applies_to": ["insights", "news", "research"],
                "weight": {"insights": 0.10, "news": 0.15, "research": 0.10}
            },
            "Innovation": {
                "description": "创新性",
                "criteria": "是否提出了新颖的观点或独特的见解",
                "applies_to": ["insights", "research"],
                "weight": {"insights": 0.15, "research": 0.15}
            },
            "Accuracy": {
                "description": "准确性",
                "criteria": "事实陈述是否准确，数据引用是否正确",
                "applies_to": ["news", "research"],
                "weight": {"news": 0.20, "research": 0.20}
            },
            "Relevance": {
                "description": "相关性",
                "criteria": "内容是否与主题高度相关，是否偏离核心议题",
                "applies_to": ["insights", "news", "research"],
                "weight": {"insights": 0.10, "news": 0.15, "research": 0.10}
            }
        }
        
        # 报告类型的特性描述
        self.report_types = {
            "insights": {
                "name": "洞察报告",
                "description": "深度分析报告，重点在于提供独特见解和可操作建议",
                "key_features": ["深度分析", "独特见解", "可操作建议", "数据支撑"]
            },
            "news": {
                "name": "行业动态",
                "description": "时效性新闻报告，重点在于及时准确地传达最新信息",
                "key_features": ["时效性", "准确性", "全面覆盖", "易读性"]
            },
            "research": {
                "name": "前沿研究",
                "description": "学术研究报告，重点在于深度探索和创新发现",
                "key_features": ["深度研究", "创新性", "严谨性", "数据证据"]
            }
        }
        
        # 初始化LLM处理器
        self.llm_processor = LLMProcessor(api_key=api_key, model=model)
        print(f"报告评估器已初始化，使用模型: {self.llm_processor.model}")

    def get_applicable_dimensions(self, report_type):
        """获取适用于特定报告类型的评估维度"""
        applicable = {}
        for dim_name, dim_info in self.evaluation_dimensions.items():
            if report_type in dim_info["applies_to"]:
                applicable[dim_name] = {
                    "description": dim_info["description"],
                    "criteria": dim_info["criteria"], 
                    "weight": dim_info["weight"][report_type]
                }
        return applicable
    
    def generate_evaluation_prompt(self, report_content, report_type, topic):
        """生成用于LLM评估的提示词"""
        
        applicable_dims = self.get_applicable_dimensions(report_type)
        report_info = self.report_types[report_type]
        
        # 根据报告类型设置不同的评分期望
        type_expectations = {
            "research": {
                "avg_score": "6-7分",
                "high_bar": "创新性、严谨性、深度分析",
                "common_issues": "过于学术化、可读性有限、缺乏实际应用价值"
            },
            "insights": {
                "avg_score": "7-8分", 
                "high_bar": "实用价值、商业洞察、可操作建议",
                "common_issues": "缺乏深度、数据支撑不足、见解不够独特"
            },
            "news": {
                "avg_score": "6-7分",
                "high_bar": "时效性、准确性、信息完整性", 
                "common_issues": "信息陈旧、覆盖不全、缺乏分析深度"
            }
        }
        
        curr_expectations = type_expectations[report_type]
        
        prompt = f"""
请你作为一位**严格且经验丰富**的行业分析师，对以下{report_info['name']}进行**客观严格**的评估。

## 重要评分原则
**请采用严格的评分标准，避免评分通胀！大多数报告应该得到中等分数！**

## 报告基本信息
- 报告类型: {report_info['name']} ({report_info['description']})
- 报告主题: {topic}
- 关键特征: {', '.join(report_info['key_features'])}
- 该类型报告平均水平: {curr_expectations['avg_score']}

## 严格评分标准
**请务必采用正态分布的评分理念，避免给出过多高分：**

- **1-2分**：严重缺陷，质量很差，基本不可用
- **3-4分**：质量较差，有明显问题，勉强达到最低要求
- **5-6分**：一般质量，达到基本要求，有改进空间（大多数报告应在此范围）
- **7-8分**：良好质量，多数方面表现出色，明显优于平均水平
- **9-10分**：卓越质量，各方面表现优异，极少见的高质量报告

## {report_info['name']}特殊评估要求
- **优秀标准**: {curr_expectations['high_bar']}
- **常见问题**: {curr_expectations['common_issues']}
- **评分期望**: 普通{report_info['name']}应得{curr_expectations['avg_score']}，只有真正卓越的才能得8分以上

## 评估维度说明
请从以下 {len(applicable_dims)} 个维度对报告进行**严格客观**评估：

"""
        
        for dim_name, dim_info in applicable_dims.items():
            prompt += f"""
### {dim_info['description']} (权重: {dim_info['weight']:.1%})
评估标准: {dim_info['criteria']}

**严格评分要求：**
- 1-3分：该维度表现差，有明显缺陷
- 4-5分：该维度表现一般，达到基本要求（多数报告应在此范围）
- 6-7分：该维度表现良好，明显优于平均水平
- 8-9分：该维度表现优秀，接近完美水平
- 10分：该维度表现完美，极其罕见

**特别提醒：不要轻易给出8分以上评分！需要有充分证据证明该维度确实卓越！**
"""
        
        prompt += f"""

## 评估要求
1. **严格标准**：基于实际质量严格评分，普通内容给普通分数
2. **避免通胀**：不要因为内容"不错"就给高分，要有明确的卓越证据
3. **差异化评分**：不同维度应有明显的分数差异，避免所有维度都是高分
4. **具体依据**：每个评分都要有具体的事实支撑和明确理由
5. **类型适配**：考虑{report_info['name']}的特点，但保持严格标准

## 质量检查要点
**请特别关注以下方面，作为评分依据：**
- 内容的原创性和独特价值（而非简单的信息堆砌）
- 逻辑论证的严密性和说服力
- 数据使用的准确性和权威性
- 语言表达的专业性和精确性
- 结构安排的合理性和阅读体验
- 见解的深度和实用价值

## 输出格式
请严格按照以下JSON格式输出评估结果：

```json
{{
    "scores": {{"""
        
        # 动态生成示例，使用更现实的分数
        example_dims = list(applicable_dims.keys())
        example_scores = [6, 5]  # 使用更保守的示例分数
        for i, dim_name in enumerate(example_dims[:2]):
            dim_info = applicable_dims[dim_name]
            score = example_scores[i] if i < len(example_scores) else 6
            prompt += f"""
        "{dim_name}": {{
            "score": {score},
            "reason": "详细的评分理由，必须基于报告具体内容",
            "strengths": ["具体优点1", "具体优点2"],
            "weaknesses": ["具体不足1", "具体不足2"]
        }}"""
            if i < 1:
                prompt += ","
        
        prompt += f"""
    }},
    "evaluation": "客观评价，既要指出优点也要指出不足，避免过度夸赞",
    "suggestions": [
        "具体可行的改进建议1",
        "具体可行的改进建议2", 
        "具体可行的改进建议3"
    ],
    "report_type_match": "评估是否符合{report_info['name']}的标准和期望"
}}
```

**关键要求：**
1. 必须评估以下所有维度：{', '.join(f'"{name}"' for name in applicable_dims.keys())}
2. 使用精确的键名，不要使用变体
3. 评分必须严格客观，有充分依据
4. **避免评分通胀 - 大多数维度应得4-6分**

## 待评估的报告内容:
{report_content}

**最后提醒：请严格按照标准评分，不要因为报告"还不错"就给高分。只有真正卓越的内容才配得上8分以上的评分！**
"""
        
        return prompt
    
    def calculate_weighted_score(self, scores, report_type):
        """计算加权总分"""
        applicable_dims = self.get_applicable_dimensions(report_type)
        
        total_weighted_score = 0
        total_weight = 0
        
        for dim_name, dim_info in applicable_dims.items():
            if dim_name in scores:
                weight = dim_info["weight"]
                score = scores[dim_name]["score"]
                total_weighted_score += score * weight
                total_weight += weight
        
        return round(total_weighted_score / total_weight, 1) if total_weight > 0 else 0
    
    def parse_evaluation_response(self, response_text, report_type):
        """解析LLM的评估响应"""
        try:
            # 尝试提取JSON部分
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                evaluation_result = json.loads(json_text)
                
                # 验证并补充缺失的字段
                if "scores" in evaluation_result:
                    applicable_dims = self.get_applicable_dimensions(report_type)
                    
                    # 创建维度名称映射，处理LLM可能使用的不同名称变体
                    dimension_mappings = {
                        "Data_Evidence": ["Data_Evidence", "Data_and_Evidence", "DataEvidence", "数据与证据"],
                        "Structure": ["Structure", "结构性"],
                        "Coherence": ["Coherence", "连贯性"],
                        "Comprehensiveness": ["Comprehensiveness", "全面性"],
                        "Depth": ["Depth", "深度"],
                        "Actionability": ["Actionability", "可操作性"],
                        "Timeliness": ["Timeliness", "时效性"],
                        "Readability": ["Readability", "可读性"],
                        "Innovation": ["Innovation", "创新性"],
                        "Accuracy": ["Accuracy", "准确性"],
                        "Relevance": ["Relevance", "相关性"]
                    }
                    
                    # 规范化scores中的键名
                    normalized_scores = {}
                    found_mappings = {}
                    
                    for standard_name, variants in dimension_mappings.items():
                        for variant in variants:
                            if variant in evaluation_result["scores"]:
                                normalized_scores[standard_name] = evaluation_result["scores"][variant]
                                found_mappings[variant] = standard_name
                                print(f"  维度名称映射: {variant} -> {standard_name}")
                                break
                    
                    # 替换为规范化的scores
                    evaluation_result["scores"] = normalized_scores
                    evaluation_result["dimension_mappings"] = found_mappings
                    
                    missing_dims = []
                    
                    # 检查是否所有维度都被评估
                    for dim_name in applicable_dims.keys():
                        if dim_name not in evaluation_result["scores"]:
                            missing_dims.append(dim_name)
                    
                    # 如果有缺失维度，尝试从响应文本中提取遗漏的评分
                    if missing_dims:
                        print(f"警告：评估结果缺少以下维度: {missing_dims}")
                        print("正在尝试从响应文本中补充缺失维度...")
                        
                        # 尝试从原始响应中提取缺失维度的评分
                        self._extract_missing_dimensions(evaluation_result, response_text, missing_dims, applicable_dims)
                        
                        # 重新检查缺失维度
                        remaining_missing = []
                        for dim_name in missing_dims:
                            if dim_name not in evaluation_result["scores"]:
                                remaining_missing.append(dim_name)
                        
                        if remaining_missing:
                            print(f"仍然缺失的维度: {remaining_missing}")
                            evaluation_result["missing_dimensions"] = remaining_missing
                            evaluation_result["evaluation_incomplete"] = True
                            evaluation_result["score_reliability"] = "中等 - 部分维度缺失"
                        else:
                            print("所有缺失维度已成功补充")
                            evaluation_result["score_reliability"] = "高 - 完整评估"
                    else:
                        evaluation_result["score_reliability"] = "高 - 完整评估"
                    
                    # 计算加权总分（这是唯一的总评分来源）
                    calculated_score = self.calculate_weighted_score(
                        evaluation_result["scores"], report_type
                    )
                    
                    # 设置最终评分（移除LLM主观评分）
                    evaluation_result["overall_score"] = calculated_score
                    evaluation_result["score_calculation_method"] = "加权平均计算"
                    
                    # 添加详细的计算信息
                    calculation_details = []
                    total_weighted = 0
                    total_weight = 0
                    
                    for dim_name, dim_info in applicable_dims.items():
                        if dim_name in evaluation_result["scores"]:
                            weight = dim_info["weight"]
                            score = evaluation_result["scores"][dim_name]["score"]
                            weighted_score = score * weight
                            total_weighted += weighted_score
                            total_weight += weight
                            calculation_details.append({
                                "dimension": dim_name,
                                "score": score,
                                "weight": weight,
                                "weighted_score": round(weighted_score, 3)
                            })
                    
                    evaluation_result["calculation_details"] = calculation_details
                    evaluation_result["total_weighted_score"] = round(total_weighted, 3)
                    evaluation_result["total_weight"] = round(total_weight, 3)
                
                return evaluation_result
            else:
                print("响应中未找到有效的JSON格式")
                return None
                
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            print(f"原始响应: {response_text[:500]}...")
            return None
        except Exception as e:
            print(f"解析响应时出错: {e}")
            return None

    def _extract_missing_dimensions(self, evaluation_result, response_text, missing_dims, applicable_dims):
        """从响应文本中提取缺失维度的评分"""
        import re
        
        # 维度名称变体映射
        dimension_variants = {
            "Data_Evidence": ["Data_Evidence", "Data_and_Evidence", "DataEvidence", "数据与证据", "Data & Evidence"],
            "Structure": ["Structure", "结构性", "Structur"],
            "Coherence": ["Coherence", "连贯性"],
            "Comprehensiveness": ["Comprehensiveness", "全面性"],
            "Depth": ["Depth", "深度"],
            "Actionability": ["Actionability", "可操作性"],
            "Timeliness": ["Timeliness", "时效性"],
            "Readability": ["Readability", "可读性"],
            "Innovation": ["Innovation", "创新性"],
            "Accuracy": ["Accuracy", "准确性"],
            "Relevance": ["Relevance", "相关性"]
        }
        
        for dim_name in missing_dims:
            dim_info = applicable_dims[dim_name]
            dim_description = dim_info["description"]
            
            # 获取该维度的所有可能名称变体
            variants = dimension_variants.get(dim_name, [dim_name])
            
            # 尝试多种模式匹配该维度的评分
            patterns = []
            
            # 为每个变体创建匹配模式
            for variant in variants:
                patterns.extend([
                    # JSON格式中的分数
                    rf'"{re.escape(variant)}"[^}}]*?"score"[：:\s]*(\d+)',
                    # 中文描述后的分数
                    rf"{re.escape(dim_description)}[：:]\s*(\d+)分?",
                    rf"{re.escape(dim_description)}.*?(\d+)/10",
                    rf"{re.escape(dim_description)}.*?评分[：:]?\s*(\d+)",
                    # 英文名称后的分数
                    rf"{re.escape(variant)}[：:]\s*(\d+)",
                    # 更宽松的匹配
                    rf"{re.escape(dim_description)}.*?(\d+)(?=\s*[分/])",
                ])
            
            score_found = False
            for pattern in patterns:
                try:
                    matches = re.findall(pattern, response_text, re.IGNORECASE | re.DOTALL)
                    if matches:
                        score = int(matches[0])
                        if 1 <= score <= 10:  # 验证分数范围
                            evaluation_result["scores"][dim_name] = {
                                "score": score,
                                "reason": f"从文本中提取的{dim_description}评分",
                                "extracted": True,
                                "extraction_pattern": pattern
                            }
                            print(f"  成功提取 {dim_name} ({dim_description}): {score}分")
                            score_found = True
                            break
                except (ValueError, IndexError):
                    continue
            
            if not score_found:
                print(f"  无法从文本中提取 {dim_name} ({dim_description}) 的评分")
                # 尝试查找原始响应中是否有相关内容
                for variant in variants:
                    if variant.lower() in response_text.lower():
                        print(f"    注意: 响应中包含 '{variant}' 但无法提取评分")
                        break

    def evaluate_report(self, report_content, report_type, topic):
        """
        评估报告质量
        
        Args:
            report_content (str): 报告内容
            report_type (str): 报告类型 (insights/news/research)
            topic (str): 报告主题
            
        Returns:
            dict: 评估结果
        """
        
        print(f"开始评估{self.report_types[report_type]['name']}: {topic}")
        print(f"报告长度: {len(report_content)} 字符")
        
        # 生成评估提示词
        prompt = self.generate_evaluation_prompt(report_content, report_type, topic)
        
        # 定义系统消息
        system_message = """你是一位资深的行业分析师和报告评估专家，具有丰富的评估经验。
你的任务是客观、专业地评估报告质量，给出公正的评分和建设性的改进建议。
请严格按照要求的JSON格式输出结果，确保所有字段完整准确。
重要：必须对提示中列出的所有评估维度进行评分，不可遗漏任何维度。"""
        
        max_retries = 2  # 最大重试次数
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    print(f"第 {attempt + 1} 次尝试评估...")
                else:
                    print("正在调用LLM API进行评估...")
                
                response = self.llm_processor.call_llm_api(
                    prompt=prompt,
                    system_message=system_message,
                    temperature=0.2,
                    max_tokens=6000
                )
                
                print(f"LLM响应长度: {len(response)} 字符")
                
                # 解析响应
                evaluation_result = self.parse_evaluation_response(response, report_type)
                
                if evaluation_result:
                    # 检查是否还有缺失的维度
                    if evaluation_result.get("missing_dimensions"):
                        missing_dims = evaluation_result["missing_dimensions"]
                        if attempt < max_retries:
                            print(f"第 {attempt + 1} 次评估仍有缺失维度: {missing_dims}")
                            print("将进行补充评估...")
                            
                            # 为缺失的维度生成补充提示
                            supplementary_prompt = self._generate_supplementary_prompt(
                                missing_dims, report_content, report_type, topic, evaluation_result.get("scores", {})
                            )
                            
                            # 调用LLM获取补充评估
                            supplementary_response = self.llm_processor.call_llm_api(
                                prompt=supplementary_prompt,
                                system_message=system_message,
                                temperature=0.2,
                                max_tokens=4000
                            )
                            
                            # 合并补充评估结果
                            merged_result = self._merge_supplementary_result(evaluation_result, supplementary_response, missing_dims)
                            if merged_result:
                                evaluation_result = merged_result
                                print("补充评估成功完成")
                                # 检查评估是否完整
                                if not evaluation_result.get("missing_dimensions"):
                                    print("所有维度评估完成")
                                    break
                            else:
                                print("补充评估失败")
                                break
                        else:
                            print(f"达到最大重试次数，仍有缺失维度: {missing_dims}")
                            # 即使有缺失维度，也返回部分结果
                            break
                    else:
                        # 没有缺失维度，评估完成
                        print("评估完成，所有维度都已评估")
                        break
                else:
                    if attempt < max_retries:
                        print(f"第 {attempt + 1} 次评估响应解析失败，正在重试...")
                        continue
                    else:
                        # 如果解析失败，返回错误信息和原始响应
                        print("评估响应解析失败，返回原始响应")
                        return {
                            "error": "评估响应解析失败",
                            "raw_response": response,
                            "evaluation_prompt": prompt,
                            "evaluation_attempts": attempt + 1
                        }
                        
            except Exception as e:
                if attempt < max_retries:
                    print(f"第 {attempt + 1} 次评估出错: {e}，正在重试...")
                    continue
                else:
                    print(f"评估过程中出错: {e}")
                    import traceback
                    print(traceback.format_exc())
                    
                    # 返回错误信息
                    return {
                        "error": f"评估失败: {str(e)}",
                        "evaluation_prompt": prompt,
                        "evaluation_attempts": attempt + 1
                    }
        
        # 确保有evaluation_result
        if evaluation_result:
            print(f"评估完成，总体评分: {evaluation_result.get('overall_score', 'N/A')}")
            
            # 添加评估元信息
            evaluation_result["evaluation_attempts"] = attempt + 1
            evaluation_result["evaluation_complete"] = not bool(evaluation_result.get("missing_dimensions"))
            
            return evaluation_result
        else:
            # 如果所有尝试都失败，返回错误信息
            return {
                "error": "所有评估尝试都失败",
                "evaluation_attempts": max_retries + 1,
                "evaluation_complete": False
            }

    def _generate_supplementary_prompt(self, missing_dims, report_content, report_type, topic, existing_scores):
        """为缺失维度生成补充评估提示词"""
        applicable_dims = self.get_applicable_dimensions(report_type)
        report_info = self.report_types[report_type]
        
        # 计算已有评分的统计信息，用于校准
        if existing_scores:
            existing_values = [score['score'] for score in existing_scores.values()]
            avg_score = sum(existing_values) / len(existing_values)
            max_score = max(existing_values)
            min_score = min(existing_values)
        else:
            avg_score = 6.0  # 默认期望
            max_score = 8.0
            min_score = 4.0
        
        prompt = f"""
请作为**严格且经验丰富**的行业分析师，对以下报告的特定维度进行**严格客观**的补充评估。

## 严重警告 - 评分标准
**禁止随意给出高分！必须有充分的事实依据！**

### 已有评分参考
- 其他维度平均分: {avg_score:.1f}分
- 分数范围: {min_score}-{max_score}分
- **你的评分应与现有评分保持一致性，避免突兀的高分或低分**

### 严格评分要求
- **4-6分**: 一般水平，达到基本要求（大多数维度应在此范围）
- **7分**: 良好水平，明显优于平均，需要具体优点支撑
- **8分**: 优秀水平，接近完美，需要多个突出亮点
- **9-10分**: 卓越/完美，极其罕见，需要压倒性证据

## 报告信息
- 类型: {report_info['name']}
- 主题: {topic}
- 已评估维度平均分: {avg_score:.1f}分

## 需要评估的缺失维度

"""
        
        for dim_name in missing_dims:
            if dim_name in applicable_dims:
                dim_info = applicable_dims[dim_name]
                prompt += f"""
### {dim_name} - {dim_info['description']}
**权重**: {dim_info['weight']:.1%}
**评估标准**: {dim_info['criteria']}

**特别提醒**: 
- 不要因为"还不错"就给7分以上
- 必须有具体事实证据支撑你的评分
- 参考已有维度平均分{avg_score:.1f}分保持一致性
- 高分(8+)需要压倒性的优秀表现证据
"""

        prompt += f"""

## 评分一致性要求
**关键原则：你的评分必须与已有评分保持合理一致性**

1. **谨慎高分**: 如果已有平均分是{avg_score:.1f}，不要轻易给出8分以上
2. **证据充分**: 每个7分以上的评分都必须列出至少3个具体优点
3. **避免通胀**: 大部分维度应该在5-7分之间
4. **事实为准**: 基于报告内容的客观事实，不要主观臆测

## 输出格式
请严格按照以下JSON格式输出：

```json
{{
    "scores": {{"""

        # 为每个缺失维度生成示例，使用保守评分
        for i, dim_name in enumerate(missing_dims):
            if dim_name in applicable_dims:
                # 使用稍低于平均分的保守评分
                conservative_score = max(int(avg_score) - 1, 5)
                prompt += f"""
        "{dim_name}": {{
            "score": {conservative_score},
            "reason": "基于报告内容的详细分析理由，必须有具体事实支撑",
            "strengths": ["具体优点1", "具体优点2", "具体优点3"],
            "weaknesses": ["具体不足1", "具体不足2"]
        }}"""
                if i < len(missing_dims) - 1:
                    prompt += ","

        prompt += f"""
    }},
    "evaluation": "客观评价，重点关注缺失维度的表现情况",
    "suggestions": [
        "针对缺失维度的具体改进建议1",
        "针对缺失维度的具体改进建议2"
    ]
}}
```

## 质量检查清单
评分前请自问：
1. ✓ 我的评分是否有具体的报告内容支撑？
2. ✓ 我是否避免了因为"看起来不错"就给高分？
3. ✓ 我的评分是否与已有评分保持一致性？
4. ✓ 如果给出7分以上，是否有压倒性的优秀证据？
5. ✓ 我的理由是否具体详细，而非空泛表述？

## 待评估报告内容
{report_content}

**最后严重提醒：绝对禁止随意给高分！每个评分都必须有扎实的事实依据！严格按照标准评分！**
"""
        
        return prompt

    def _merge_supplementary_result(self, original_result, supplementary_response, missing_dims):
        """合并补充评估结果"""
        print(f"\n=== 合并补充评估结果 ===")
        print(f"原始结果维度: {list(original_result.get('scores', {}).keys()) if original_result else '无'}")
        print(f"缺失维度: {missing_dims}")
        
        if not original_result or not original_result.get('scores'):
            return None
            
        try:
            # 解析补充评估响应
            json_start = supplementary_response.find('{')
            json_end = supplementary_response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = supplementary_response[json_start:json_end]
                supplementary_result = json.loads(json_text)
                print(f"补充结果维度: {list(supplementary_result.get('scores', {}).keys())}")
            else:
                print("补充响应中未找到有效JSON")
                return None
                
        except json.JSONDecodeError as e:
            print(f"补充响应JSON解析错误: {e}")
            return None
        
        # 复制原始结果
        merged_result = json.loads(json.dumps(original_result))
        supplementary_scores = supplementary_result.get('scores', {})
        
        # 检查补充评分的合理性
        high_score_count = 0
        suspicious_scores = []
        
        for dim_name, dim_data in supplementary_scores.items():
            score = dim_data.get('score', 0)
            reason = dim_data.get('reason', '')
            
            # 更严格的高分检查
            if score >= 8:
                high_score_count += 1
                # 检查是否有足够的证据支撑高分
                if len(reason) < 50 or not any(keyword in reason.lower() for keyword in 
                    ['卓越', '优秀', '完美', '杰出', '精彩', '深入', '全面', '创新', '独特', '专业', '详细']):
                    suspicious_scores.append(f"{dim_name}:{score}分")
                    # 降低可疑的高分
                    original_score = score
                    score = min(score - 1, 7)  # 最多降1分，且不超过7分
                    print(f"⚠️  可疑高分调整: {dim_name} {original_score}→{score}分 (理由不足)")
                    dim_data['score'] = score
                    dim_data['reason'] = f"[调整后评分] {reason}"
        
        # 如果超过40%的维度都是高分，进行整体调整
        total_dims = len(supplementary_scores)
        if total_dims > 0 and high_score_count / total_dims > 0.4:
            print(f"⚠️  检测到评分通胀：{high_score_count}/{total_dims}维度为高分，进行整体调整")
            for dim_name, dim_data in supplementary_scores.items():
                if dim_data.get('score', 0) >= 7:
                    original_score = dim_data['score']
                    # 轻微下调高分
                    dim_data['score'] = max(original_score - 1, 6)
                    print(f"   - {dim_name}: {original_score}→{dim_data['score']}分")
        
        # 合并维度评分
        successfully_merged = 0
        for dim_name in missing_dims:
            if dim_name in supplementary_scores:
                merged_result['scores'][dim_name] = supplementary_scores[dim_name]
                merged_result['scores'][dim_name]['source'] = 'supplementary'
                if dim_name in [s.split(':')[0] for s in suspicious_scores]:
                    merged_result['scores'][dim_name]['source'] = 'supplementary_adjusted'
                print(f"✓ 添加缺失维度: {dim_name} = {supplementary_scores[dim_name]['score']}分")
                successfully_merged += 1
        
        # 更新缺失维度列表
        remaining_missing = []
        for dim_name in missing_dims:
            if dim_name not in merged_result['scores']:
                remaining_missing.append(dim_name)
        
        if remaining_missing:
            merged_result["missing_dimensions"] = remaining_missing
            merged_result["evaluation_incomplete"] = True
            merged_result["score_reliability"] = "中等 - 部分维度缺失"
        else:
            if "missing_dimensions" in merged_result:
                del merged_result["missing_dimensions"]
            merged_result["evaluation_incomplete"] = False
            merged_result["score_reliability"] = "高 - 完整评估"
        
        # 重新计算总分
        # 需要获取当前的report_type，从原始结果中获取或者根据适用维度推断
        applicable_dims = self.get_applicable_dimensions("insights")  # 使用insights作为默认
        
        # 尝试根据已有维度推断report_type
        original_dims = set(original_result.get('scores', {}).keys())
        for rtype, rinfo in self.report_types.items():
            rtype_dims = set(self.get_applicable_dimensions(rtype).keys())
            if original_dims.issubset(rtype_dims):
                applicable_dims = self.get_applicable_dimensions(rtype)
                break
        
        merged_result["overall_score"] = self.calculate_weighted_score(
            merged_result["scores"], 
            "insights"  # 使用insights作为默认类型
        )
        
        # 更新评价和建议（更加保守）
        if supplementary_result.get('evaluation'):
            if merged_result.get('evaluation'):
                merged_result['evaluation'] = f"{merged_result['evaluation']}\n\n补充评估: {supplementary_result['evaluation']}"
            else:
                merged_result['evaluation'] = supplementary_result['evaluation']
        
        if supplementary_result.get('suggestions'):
            if merged_result.get('suggestions'):
                merged_result['suggestions'].extend(supplementary_result['suggestions'])
            else:
                merged_result['suggestions'] = supplementary_result['suggestions']
        
        # 添加评分质量警告
        if suspicious_scores:
            quality_warning = f"注意: 以下维度的高分可能存在评分通胀，已进行调整: {', '.join(suspicious_scores)}"
            if 'evaluation' in merged_result:
                merged_result['evaluation'] += f"\n\n⚠️ {quality_warning}"
            else:
                merged_result['evaluation'] = quality_warning
        
        print(f"成功合并 {successfully_merged} 个维度")
        return merged_result if successfully_merged > 0 else None
