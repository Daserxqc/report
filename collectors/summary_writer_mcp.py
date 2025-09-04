from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from collectors.llm_processor import LLMProcessor
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'search_mcp', 'src'))
from collectors.search_mcp import Document


@dataclass
class SummaryConfig:
    """摘要配置"""
    length_constraint: str = "200-300字"  # 长度约束
    format: str = "paragraph"            # 格式: paragraph, bullet_points, structured
    focus_areas: List[str] = None        # 重点关注领域
    tone: str = "professional"           # 语调: professional, academic, casual
    target_audience: str = "通用"        # 目标受众
    
    def __post_init__(self):
        if self.focus_areas is None:
            self.focus_areas = []


class SummaryWriterMcp:
    """
    摘要写作MCP (Model Context Protocol)
    
    用途：将一份或多份文档浓缩成简洁的摘要。
    
    职责：
    - 根据指定的长度和格式要求撰写摘要
    - 确保摘要内容忠于原文
    
    输入：content_data: list[Document], length_constraint: str | int, format: str = 'paragraph'
    输出：str (摘要文本)
    
    实现要点：Prompt需强调"浓缩"、"精炼"、"忠于事实"。
    """
    
    def __init__(self):
        """初始化SummaryWriterMcp"""
        try:
            self.llm_processor = LLMProcessor()
            self.has_llm = True
            print("✅ SummaryWriterMcp初始化完成")
        except Exception as e:
            print(f"⚠️ LLM处理器初始化失败: {str(e)}")
            self.has_llm = False
        
        # 预定义的摘要模板
        self.summary_templates = self._load_summary_templates()
    
    def _load_summary_templates(self) -> Dict[str, str]:
        """加载摘要模板"""
        return {
            "paragraph": """
请为以下内容撰写一个简洁、准确的段落式摘要。

原始内容：
{content_data}

摘要要求：
- 长度限制：{length_constraint}
- 目标受众：{target_audience}
- 语言风格：{tone_description}
- 重点关注：{focus_areas}

撰写原则：
1. **浓缩精炼**：去除冗余信息，保留核心要点
2. **忠于事实**：不添加原文中没有的信息
3. **逻辑清晰**：按照重要性和逻辑顺序组织内容
4. **语言流畅**：使用连贯的段落形式表达

请直接输出摘要内容，不要包含其他解释性文字。
""",

            "bullet_points": """
请为以下内容撰写一个要点式摘要。

原始内容：
{content_data}

摘要要求：
- 长度限制：{length_constraint}
- 目标受众：{target_audience}
- 格式：项目符号列表
- 重点关注：{focus_areas}

撰写原则：
1. **要点提取**：识别并提取最关键的信息点
2. **层次分明**：按照重要性排序
3. **简洁明了**：每个要点都应简洁有力
4. **完整覆盖**：确保涵盖原文的主要内容

输出格式：
- 核心要点1
- 核心要点2
- 核心要点3
- ...

请直接输出要点列表，不要包含其他解释性文字。
""",

            "structured": """
请为以下内容撰写一个结构化摘要。

原始内容：
{content_data}

摘要要求：
- 长度限制：{length_constraint}
- 目标受众：{target_audience}
- 格式：结构化分节
- 重点关注：{focus_areas}

撰写原则：
1. **结构清晰**：使用明确的章节标题
2. **内容完整**：每个部分都应有实质内容
3. **逻辑连贯**：各部分之间应有逻辑关联
4. **信息准确**：严格基于原文内容

输出格式：
**核心概念**
[核心概念的简要说明]

**主要发现/观点**
[主要发现或观点的总结]

**应用价值**
[实际应用价值或意义]

**结论**
[总结性结论]

请按照上述结构输出摘要，不要包含其他解释性文字。
""",

            "executive": """
请为以下内容撰写一个执行摘要。

原始内容：
{content_data}

摘要要求：
- 长度限制：{length_constraint}
- 目标受众：{target_audience}（决策者和管理层）
- 格式：执行摘要
- 重点关注：{focus_areas}

撰写原则：
1. **决策导向**：突出对决策有用的关键信息
2. **商业价值**：强调商业影响和价值主张
3. **行动建议**：提供明确的行动方向
4. **数据驱动**：引用关键数据和指标

输出格式：
**概述**
[简要概述核心内容]

**关键发现**
[最重要的发现和洞察]

**影响分析**
[对业务/行业的影响]

**建议行动**
[推荐的具体行动]

请按照执行摘要的标准格式输出，语言要专业且具有说服力。
""",

            "academic": """
请为以下学术内容撰写一个学术摘要。

原始内容：
{content_data}

摘要要求：
- 长度限制：{length_constraint}
- 目标受众：{target_audience}（学术研究人员）
- 格式：学术摘要
- 重点关注：{focus_areas}

撰写原则：
1. **学术规范**：遵循学术写作标准
2. **理论基础**：突出理论贡献和创新
3. **方法论**：说明研究方法和数据来源
4. **客观中立**：保持学术写作的客观性

输出格式：
**研究背景**
[研究背景和问题陈述]

**主要方法**
[采用的研究方法和数据]

**核心发现**
[关键研究结果和发现]

**学术贡献**
[理论贡献和实践意义]

请使用学术写作的语言风格，确保准确性和严谨性。
"""
        }
    
    def write_summary(self, 
                     content_data: Union[List[Document], List[Dict], str],
                     length_constraint: Union[str, int] = "200-300字",
                     format: str = "paragraph",
                     **kwargs) -> str:
        """
        生成摘要
        
        Args:
            content_data: 内容数据
            length_constraint: 长度限制
            format: 输出格式
            **kwargs: 其他配置参数
            
        Returns:
            str: 生成的摘要
        """
        if not self.has_llm:
            return self._fallback_summary_generation(content_data, length_constraint, format)
        
        try:
            # 构建摘要配置
            config = SummaryConfig(
                length_constraint=str(length_constraint),
                format=format,
                **kwargs
            )
            
            # 准备内容数据
            prepared_content = self._prepare_content_for_summary(content_data)
            
            # 生成摘要
            summary = self._generate_summary_with_llm(prepared_content, config)
            
            print(f"✅ 生成{format}格式摘要，长度约{len(summary)}字符")
            return summary
            
        except Exception as e:
            print(f"❌ 摘要生成失败: {str(e)}")
            return self._fallback_summary_generation(content_data, length_constraint, format)
    
    def _generate_summary_with_llm(self, content_data: str, config: SummaryConfig) -> str:
        """使用LLM生成摘要"""
        # 选择合适的模板
        template = self.summary_templates.get(config.format, self.summary_templates["paragraph"])
        
        # 准备模板参数
        tone_descriptions = {
            "professional": "专业、正式的商务语言",
            "academic": "学术、严谨的研究语言",
            "casual": "轻松、易懂的通俗语言",
            "technical": "技术、精确的专业语言"
        }
        
        template_params = {
            "content_data": content_data,
            "length_constraint": config.length_constraint,
            "target_audience": config.target_audience,
            "tone_description": tone_descriptions.get(config.tone, tone_descriptions["professional"]),
            "focus_areas": ", ".join(config.focus_areas) if config.focus_areas else "全面覆盖主要内容"
        }
        
        # 格式化prompt
        prompt = template.format(**template_params)
        
        # 计算token限制
        length_parts = config.length_constraint.replace("字", "").replace("词", "").replace(" ", "")
        if "-" in length_parts:
            try:
                max_length = int(length_parts.split("-")[1])
                max_tokens = min(max_length * 2, 2000)  # 字数转token，限制最大值
            except:
                max_tokens = 1000
        else:
            try:
                max_tokens = min(int(length_parts) * 2, 2000)
            except:
                max_tokens = 1000
        
        # 调用LLM
        summary = self.llm_processor.call_llm_api(
            prompt,
            f"你是一位专业的内容摘要专家，擅长将复杂信息浓缩为简洁、准确的摘要。你的语言风格是{config.tone}，目标受众是{config.target_audience}。",
            temperature=0.3,
            max_tokens=max_tokens
        )
        
        # 后处理摘要
        return self._post_process_summary(summary, config)
    
    def _post_process_summary(self, summary: str, config: SummaryConfig) -> str:
        """后处理摘要"""
        if not summary:
            return "摘要生成失败"
        
        # 清理格式
        summary = summary.strip()
        
        # 移除可能的标题或前言
        unwanted_prefixes = [
            "摘要：", "总结：", "概述：", "Summary:", "以下是摘要：", 
            "根据提供的内容", "基于以上信息", "摘要如下："
        ]
        
        for prefix in unwanted_prefixes:
            if summary.startswith(prefix):
                summary = summary[len(prefix):].strip()
        
        # 检查长度约束
        if self._is_length_exceeded(summary, config.length_constraint):
            print(f"⚠️ 摘要长度超出限制，当前长度: {len(summary)}")
        
        return summary
    
    def _is_length_exceeded(self, text: str, length_constraint: str) -> bool:
        """检查长度是否超出限制"""
        try:
            # 解析长度限制
            constraint_str = length_constraint.replace("字", "").replace("词", "").replace(" ", "")
            
            if "-" in constraint_str:
                max_length = int(constraint_str.split("-")[1])
            else:
                max_length = int(constraint_str)
            
            return len(text) > max_length * 1.2  # 允许20%的误差
        except:
            return False
    
    def _prepare_content_for_summary(self, content_data: Union[List[Document], List[Dict], str]) -> str:
        """准备用于摘要的内容数据"""
        if isinstance(content_data, str):
            return content_data
        
        if not content_data:
            return "无内容数据"
        
        content_parts = []
        
        for i, item in enumerate(content_data):
            if isinstance(item, Document):
                content_parts.append(f"[文档{i+1}] {item.title}\n{item.content}")
            elif isinstance(item, dict):
                title = item.get("title", f"文档{i+1}")
                content = item.get("content", item.get("summary", item.get("abstract", "")))
                content_parts.append(f"[{title}]\n{content}")
        
        return "\n\n".join(content_parts)
    
    def write_multi_level_summary(self, 
                                 content_data: Union[List[Document], List[Dict]],
                                 levels: List[str] = None) -> Dict[str, str]:
        """
        生成多层次摘要
        
        Args:
            content_data: 内容数据
            levels: 摘要级别列表，如 ["executive", "detailed", "bullet"]
            
        Returns:
            Dict[str, str]: 各级别对应的摘要
        """
        if levels is None:
            levels = ["executive", "paragraph", "bullet_points"]
        
        summaries = {}
        
        # 不同级别的长度配置
        level_configs = {
            "executive": {"length": "150-200字", "format": "executive"},
            "paragraph": {"length": "300-400字", "format": "paragraph"},
            "detailed": {"length": "500-600字", "format": "structured"},
            "bullet_points": {"length": "200-300字", "format": "bullet_points"},
            "academic": {"length": "250-350字", "format": "academic"}
        }
        
        for level in levels:
            try:
                config = level_configs.get(level, {"length": "200-300字", "format": "paragraph"})
                
                summary = self.write_summary(
                    content_data=content_data,
                    length_constraint=config["length"],
                    format=config["format"]
                )
                
                summaries[level] = summary
                print(f"  ✅ {level}级摘要生成完成")
                
            except Exception as e:
                print(f"  ❌ {level}级摘要生成失败: {str(e)}")
                summaries[level] = f"摘要生成失败: {str(e)}"
        
        return summaries
    
    def write_focused_summary(self, 
                             content_data: Union[List[Document], List[Dict]],
                             focus_keywords: List[str],
                             length_constraint: str = "200-300字") -> str:
        """
        生成关注特定关键词的摘要
        
        Args:
            content_data: 内容数据
            focus_keywords: 关注的关键词列表
            length_constraint: 长度限制
            
        Returns:
            str: 聚焦摘要
        """
        return self.write_summary(
            content_data=content_data,
            length_constraint=length_constraint,
            format="paragraph",
            focus_areas=focus_keywords,
            tone="professional"
        )
    
    def write_comparative_summary(self, 
                                 content_groups: Dict[str, List[Union[Document, Dict]]],
                                 comparison_aspects: List[str] = None) -> str:
        """
        生成比较性摘要
        
        Args:
            content_groups: 内容分组，如 {"方案A": [docs], "方案B": [docs]}
            comparison_aspects: 比较方面
            
        Returns:
            str: 比较摘要
        """
        if not self.has_llm:
            return "比较摘要功能需要LLM支持"
        
        try:
            # 为每个组生成简要摘要
            group_summaries = {}
            for group_name, content_list in content_groups.items():
                summary = self.write_summary(
                    content_data=content_list,
                    length_constraint="100-150字",
                    format="paragraph"
                )
                group_summaries[group_name] = summary
            
            # 构建比较prompt
            comparison_content = "\n\n".join([
                f"**{group}**：\n{summary}" 
                for group, summary in group_summaries.items()
            ])
            
            aspects_text = ", ".join(comparison_aspects) if comparison_aspects else "各方面特点"
            
            prompt = f"""
请基于以下各组内容的摘要，撰写一个比较性摘要：

{comparison_content}

比较重点：{aspects_text}

要求：
1. 突出各组的主要差异和特点
2. 指出共同点和不同点
3. 提供客观的比较分析
4. 长度控制在300-400字

请直接输出比较摘要，不要包含其他解释性文字。
"""
            
            comparative_summary = self.llm_processor.call_llm_api(
                prompt,
                "你是一位专业的比较分析专家，擅长识别和总结不同内容之间的异同点。",
                temperature=0.3,
                max_tokens=800
            )
            
            return comparative_summary.strip()
            
        except Exception as e:
            print(f"❌ 比较摘要生成失败: {str(e)}")
            return "比较摘要生成失败"
    
    def _fallback_summary_generation(self, content_data, length_constraint, format) -> str:
        """备用摘要生成方法"""
        try:
            # 准备内容
            if isinstance(content_data, str):
                text = content_data
            elif isinstance(content_data, list) and content_data:
                if isinstance(content_data[0], Document):
                    text = " ".join([doc.content[:200] for doc in content_data[:3]])
                else:
                    text = " ".join([item.get("content", "")[:200] for item in content_data[:3]])
            else:
                return "无可用内容进行摘要"
            
            # 简单的句子提取
            sentences = [s.strip() for s in text.split('。') if len(s.strip()) > 10]
            
            # 根据格式调整输出
            if format == "bullet_points":
                return "\n".join([f"- {s}" for s in sentences[:5]])
            elif format == "structured":
                return f"**主要内容**\n{sentences[0] if sentences else '无内容'}。\n\n**关键要点**\n" + \
                       "\n".join([f"- {s}" for s in sentences[1:4]])
            else:
                # 段落格式
                summary_text = "。".join(sentences[:3]) + "。" if sentences else "无可用内容"
                return summary_text[:300] + "..." if len(summary_text) > 300 else summary_text
                
        except Exception as e:
            return f"摘要生成失败: {str(e)}"