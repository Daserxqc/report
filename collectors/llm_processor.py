import requests
import json
from typing import List, Dict, Any, Optional
import config
import re
from tenacity import retry, stop_after_attempt, wait_exponential
import traceback

class LLMProcessor:
    """
    使用大模型处理和总结搜索结果，生成结构化的报告内容
    """
    
    def __init__(self, api_key=None, model=None):
        """
        初始化LLM处理器
        
        Args:
            api_key (str, optional): API密钥，默认从config获取
            model (str, optional): 使用的模型名称，默认从config获取
        """
        # 配置API密钥和URL
        self.api_key = api_key or getattr(config, "OPENAI_API_KEY", None)
        self.base_url = getattr(config, "OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        # 如果URL以/结尾，移除
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
            
        # 如果URL不包含完整路径，添加/v1
        if "/v1" not in self.base_url:
            self.base_url += "/v1"
            
        # 设置模型，默认使用gpt-3.5-turbo
        self.model = model or getattr(config, "LLM_MODEL", "gpt-3.5-turbo")
        
        # 根据base_url判断使用的API类型
        self.is_openai = "openai" in self.base_url.lower()
        self.is_azure = "azure" in self.base_url.lower()
        self.is_deepseek = "deepseek" in self.base_url.lower()
        
        # 如果是深度思考API，使用其专用模型
        if self.is_deepseek:
            self.model = "deepseek-chat"
            
        print(f"LLM处理器已初始化，使用的模型: {self.model}, API URL: {self.base_url}")
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def call_llm_api(self, prompt: str, system_message: Optional[str] = None, 
                  temperature: float = 0.3, max_tokens: int = 1500) -> str:
        """
        调用LLM API进行内容生成
        
        Args:
            prompt (str): 用户提示
            system_message (str, optional): 系统消息
            temperature (float): 温度参数，控制创造性
            max_tokens (int): 最大生成token数
            
        Returns:
            str: 生成的内容
        """
        if not self.api_key:
            raise ValueError("API密钥未提供，无法调用LLM API")
            
        try:
            # 构建消息
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            # 尝试使用OpenAI Python库
            try:
                from openai import OpenAI
                
                client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                if hasattr(response, 'choices') and len(response.choices) > 0:
                    return response.choices[0].message.content
                else:
                    raise ValueError(f"API返回无效响应: {response}")
                    
            except ImportError:
                # 如果没有OpenAI库，使用requests直接调用API
                print("OpenAI库未安装，使用HTTP请求调用API")
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                endpoint = f"{self.base_url}/chat/completions"
                data = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                response = requests.post(endpoint, headers=headers, json=data, timeout=60)
                response.raise_for_status()
                
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    raise ValueError(f"API返回无效JSON: {result}")
                    
        except Exception as e:
            print(f"调用LLM API时出错: {str(e)}")
            print(traceback.format_exc())
            raise
            
    def summarize_content(self, content: str, topic: str, 
                         max_length: int = 1000, focus: Optional[str] = None) -> str:
        """
        总结内容，提取关键信息
        
        Args:
            content (str): 需要总结的原始内容
            topic (str): 内容主题
            max_length (int): 结果最大长度
            focus (str, optional): 总结的重点方向
            
        Returns:
            str: 总结后的内容
        """
        if not content or len(content.strip()) < 50:
            return content
            
        system_message = """你是一位专业的文本摘要专家，擅长从原始内容中提取关键信息并生成简洁、信息密集的总结。
提取所有重要数据点、统计数字、关键观点和主要论述，同时保持原文的核心信息和结构，但去除冗余内容。
使用Markdown格式，用粗体标记重要概念和数据点。
减少括号的使用，避免过多术语解释，使文本更加自然流畅。
直接输出总结结果，不要添加任何元说明或评论。"""

        focus_text = f"，重点关注{focus}" if focus else ""
        
        prompt = f"""请对以下关于"{topic}"{focus_text}的内容进行专业总结，提取最有价值的信息：

{content}

总结要求：
1. 保留所有重要数据点、统计数字和关键事实
2. 突出主要观点和核心论述
3. 使用清晰专业的语言风格
4. 总结长度控制在{max_length}字以内
5. 使用Markdown格式，重要数据或概念用**粗体**标记
6. 减少括号的使用，避免过多术语解释，使行文更加自然
7. 直接给出总结内容，不要添加额外说明"""

        try:
            result = self.call_llm_api(prompt, system_message, temperature=0.2)
            return result.strip()
        except Exception as e:
            print(f"总结内容时出错: {str(e)}")
            # 如果API调用失败，返回截断的原始内容
            if len(content) > max_length:
                return content[:max_length] + "..."
            return content
    
    def generate_section_content(self, section_items: List[Dict[str, Any]], topic: str, section_name: str) -> str:
        """
        基于多个搜索结果生成一个特定章节的内容
        
        Args:
            section_items: 包含章节相关内容的项目列表
            topic: 主题
            section_name: 章节名称
            
        Returns:
            str: 生成的章节内容
        """
        # 收集所有内容
        all_contents = []
        for item in section_items:
            if "content" in item and item["content"]:
                all_contents.append(item["content"])
                
        if not all_contents:
            return f"关于{topic}的{section_name}，目前暂无充分资料。"
            
        # 合并内容
        combined_content = "\n\n---\n\n".join(all_contents)
        
        # 根据章节类型定制提示
        if section_name == "行业概况":
            focus = "行业定义、特点、发展历程、产业链结构、主要参与者等"
        elif section_name == "政策支持":
            focus = "政策环境、法规框架、政府支持措施、国内外政策比较等"
        elif section_name == "市场规模":
            focus = "市场规模数据、增长率、地区分布、细分市场占比等"
        elif section_name == "技术趋势":
            focus = "关键技术发展方向、创新突破、技术路线图等"
        elif section_name == "未来展望":
            focus = "行业前景预测、发展趋势、机遇与挑战、战略建议等"
        else:
            focus = f"{section_name}相关的关键信息"
            
        system_message = f"""你是一位专业的{topic}行业分析师，擅长撰写高质量的行业报告。
基于提供的材料，请撰写一篇关于{topic}的{section_name}分析。
内容应专业、客观、有深度，同时注重可读性。
统计数据和关键事实必须基于提供的材料，不要捏造数据。
使用清晰的标题层次，并确保关键数据突出显示。
减少括号和术语解释的使用，使文本更加流畅自然。
如果材料中有冲突的信息，请选择最可信的数据来源或明确指出差异。"""

        prompt = f"""请基于以下关于{topic}的{section_name}原始资料，撰写一篇专业、连贯、结构清晰的分析文章：

{combined_content}

撰写要求：
1. 重点关注{focus}
2. 使用专业、客观的语言风格
3. 文章结构应清晰，分段合理，使用**粗体**标记重要小标题
4. 使用Markdown格式，保留所有重要数据点和统计数字
5. 长度适中，约800-1200字
6. 文章应当是完整的，具有内在逻辑和连贯性
7. 直接给出文章内容，不要添加标题或额外说明
8. 减少括号的使用，避免过多术语解释，使行文更加自然
9. 对重要数据或概念使用加粗格式突出显示"""

        try:
            result = self.call_llm_api(prompt, system_message, temperature=0.4, max_tokens=2000)
            # 清理可能的元说明
            result = re.sub(r'^(以下是|这是|这篇文章是|下面是).*?[:：]', '', result, flags=re.IGNORECASE).strip()
            return result
        except Exception as e:
            print(f"生成{section_name}章节内容时出错: {str(e)}")
            # 失败时尝试简单合并内容
            fallback_content = f"根据搜集的资料，{topic}的{section_name}主要包括以下几个方面：\n\n"
            # 提取每个来源的前200个字符作为备用
            for i, content in enumerate(all_contents[:3]):
                fallback_content += f"● {content[:200]}...\n\n"
            return fallback_content
            
    def organize_search_results(self, raw_results: List[Dict[str, Any]], topic: str) -> Dict[str, Any]:
        """
        组织搜索结果，生成结构化的报告
        
        Args:
            raw_results: 原始搜索结果列表
            topic: 主题
            
        Returns:
            Dict: 包含结构化报告内容的字典
        """
        print(f"开始处理{len(raw_results)}条关于{topic}的搜索结果")
        
        # 按章节分类结果
        sections = {}
        all_sources = []
        
        # 将结果分类到不同章节
        for i, result in enumerate(raw_results):
            try:
                # 检查结果格式
                if not isinstance(result, dict):
                    print(f"警告: 第{i+1}个结果不是字典类型: {type(result)}")
                    continue
                
                section = result.get("section", "其他信息")
                
                if section not in sections:
                    sections[section] = []
                    
                # 提取并清理内容
                content = result.get("content", "").strip()
                title = result.get("title", "").strip()
                url = result.get("url", "#")
                source = result.get("source", "Web")
                
                if not content or len(content) < 10:
                    print(f"警告: 第{i+1}个结果内容为空或过短")
                    continue
                
                # 使用LLM总结内容以确保质量
                summarized_content = self.summarize_content(content, topic, focus=section)
                
                # 添加到章节
                sections[section].append({
                    "title": title,
                    "content": summarized_content,
                    "url": url,
                    "source": source
                })
                
                # 记录来源
                source_info = {
                    "title": title,
                    "url": url,
                    "source": source
                }
                if source_info not in all_sources:
                    all_sources.append(source_info)
                    
            except Exception as e:
                print(f"处理第{i+1}个结果时出错: {str(e)}")
                continue
                
        # 生成报告内容
        report_content = f"# {topic}行业洞察报告\n\n"
        structured_sections = []
        
        # 处理每个章节
        for section_name, section_items in sections.items():
            if not section_items:
                continue
                
            print(f"正在生成'{section_name}'章节，处理{len(section_items)}个条目")
            
            # 使用LLM生成章节内容
            section_content = self.generate_section_content(section_items, topic, section_name)
            
            # 添加到报告 - 使用二级标题
            report_content += f"## {section_name}\n\n"
            report_content += section_content + "\n\n"
            
            # 添加参考来源
            report_content += "**参考来源**:\n"
            for idx, item in enumerate(section_items[:3]):
                report_content += f"- [{item['title']}]({item['url']})\n"
                
            report_content += "\n\n"
            
            # 添加到结构化章节
            structured_sections.append({
                "title": section_name,
                "content": section_content
            })
            
        # 返回完整报告
        from datetime import datetime
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        return {
            "content": report_content,
            "sources": all_sources,
            "sections": structured_sections,
            "date": current_date
        }
        
    def translate_text(self, text: str, target_language: str = "中文") -> str:
        """
        将文本翻译为目标语言
        
        Args:
            text: 需要翻译的文本
            target_language: 目标语言，默认为中文
            
        Returns:
            str: 翻译后的文本
        """
        if not text or len(text.strip()) == 0:
            return ""
            
        # 检查是否需要翻译(如果已经是目标语言)
        if target_language == "中文":
            # 计算中文字符占比
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            if chinese_chars / len(text) > 0.5:
                print("文本主要是中文，无需翻译")
                return text
        
        system_message = f"""你是一位专业的翻译专家，请将以下文本翻译成{target_language}。
翻译应准确传达原文含义，同时符合目标语言的表达习惯。
减少括号的使用，使文本更加自然流畅，保留原文Markdown格式。
直接返回翻译结果，不要添加任何说明、注释或额外文本。"""

        prompt = f"请将以下文本翻译成{target_language}：\n\n{text}"
        
        try:
            result = self.call_llm_api(prompt, system_message, temperature=0.1)
            
            # 清理翻译结果中可能的元说明
            patterns = [
                "翻译:", "翻译：", "以下是翻译:", "以下是翻译：",
                "翻译结果:", "翻译结果：", "译文:", "译文："
            ]
            for pattern in patterns:
                if result.startswith(pattern):
                    result = result[len(pattern):].strip()
                    
            return result
            
        except Exception as e:
            print(f"翻译文本时出错: {str(e)}")
            return text  # 失败时返回原文 

    def process_json_response(self, response_text: str) -> dict:
        """
        处理LLM返回的JSON响应，移除可能存在的代码块标记和其他非JSON内容
        
        Args:
            response_text (str): LLM返回的原始文本
            
        Returns:
            dict: 解析后的JSON对象
        """
        if not response_text or not response_text.strip():
            raise ValueError("输入的响应文本为空")
            
        # 尝试直接解析为JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试处理常见的格式问题
            cleaned_text = response_text.strip()
            
            # 1. 移除可能的Markdown代码块标记
            if "```" in cleaned_text:
                try:
                    # 尝试提取代码块内容
                    import re
                    code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned_text)
                    if code_block_match:
                        cleaned_text = code_block_match.group(1).strip()
                except Exception as e:
                    print(f"提取代码块时出错: {str(e)}")
            
            # 2. 尝试找出JSON开始和结束的位置
            try:
                json_start = cleaned_text.find('{')
                json_end = cleaned_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    cleaned_text = cleaned_text[json_start:json_end]
            except Exception as e:
                print(f"查找JSON边界时出错: {str(e)}")
            
            # 3. 尝试解析清理后的文本
            try:
                return json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                # 如果仍然失败，抛出异常
                print(f"清理后的JSON仍然无法解析: {cleaned_text}")
                print(f"JSON错误: {str(e)}")
                raise ValueError(f"无法解析为有效的JSON: {e}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def call_llm_api_json(self, prompt: str, system_message: Optional[str] = None, 
                       temperature: float = 0.2, max_tokens: int = 1500) -> dict:
        """
        调用LLM API并确保返回有效的JSON格式
        
        Args:
            prompt (str): 用户提示
            system_message (str, optional): 系统消息
            temperature (float): 温度参数，控制创造性，默认较低以保证格式一致性
            max_tokens (int): 最大生成token数
            
        Returns:
            dict: 解析后的JSON对象
        """
        # 如果没有提供系统消息，使用默认的JSON格式化指令
        if not system_message:
            system_message = """你是一个API程序，只返回有效的JSON格式数据，不要包含任何解释、注释或额外的文本。
确保你的响应是直接的JSON对象，没有代码块标记(```)或其他格式化标记。
不要在JSON前后添加任何文字，例如"以下是JSON格式的结果:"或"希望这对你有帮助"。"""
        else:
            # 若提供了系统消息，增加JSON格式要求
            system_message += "\n务必只返回有效的JSON格式，不要包含代码块标记(```)或其他额外文本。"
            
        # 调用API获取响应
        response_text = self.call_llm_api(prompt, system_message, temperature, max_tokens)
        
        # 处理并解析响应为JSON
        return self.process_json_response(response_text) 