from typing import List, Dict, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import json


class InteractionType(Enum):
    """交互类型枚举"""
    CHOICE = "choice"           # 选择题
    INPUT = "input"             # 文本输入
    CONFIRMATION = "confirm"    # 确认
    RATING = "rating"          # 评分
    MULTI_CHOICE = "multi_choice"  # 多选
    CUSTOM = "custom"          # 自定义


@dataclass
class InteractionOption:
    """交互选项"""
    value: str
    label: str
    description: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "value": self.value,
            "label": self.label,
            "description": self.description
        }


@dataclass
class InteractionPrompt:
    """交互提示"""
    prompt: str
    interaction_type: InteractionType
    options: List[InteractionOption] = None
    allow_custom: bool = False
    validation_rules: Dict = None
    default_value: str = ""
    timeout_seconds: int = 300  # 5分钟超时
    
    def __post_init__(self):
        if self.options is None:
            self.options = []
        if self.validation_rules is None:
            self.validation_rules = {}


class UserInteractionMcp:
    """
    用户交互MCP (Model Context Protocol)
    
    用途：在流程的关键决策点暂停，并获取用户输入。
    
    职责：
    - 向用户展示选项
    - 接收用户的选择或自定义输入
    - 管理重试或修改的循环逻辑
    
    输入：prompt: str, options: list[str] = [], allow_custom: bool = False
    输出：str (用户的选择)
    
    实现要点：在CLI中可基于input()实现，在Web应用中则与前端组件交互。
    """
    
    def __init__(self, interface_type: str = "cli"):
        """
        初始化UserInteractionMcp
        
        Args:
            interface_type: 接口类型 ('cli', 'web', 'api')
        """
        self.interface_type = interface_type
        self.interaction_history = []
        print(f"✅ UserInteractionMcp初始化完成 ({interface_type}模式)")
    
    def get_user_choice(self,
                       prompt: str,
                       options: List[str] = None,
                       allow_custom: bool = False,
                       default: str = "") -> str:
        """
        获取用户选择
        
        Args:
            prompt: 提示信息
            options: 选项列表
            allow_custom: 是否允许自定义输入
            default: 默认值
            
        Returns:
            str: 用户选择
        """
        if options is None:
            options = []
        
        # 创建交互选项
        interaction_options = [
            InteractionOption(value=str(i), label=option) 
            for i, option in enumerate(options, 1)
        ]
        
        interaction_prompt = InteractionPrompt(
            prompt=prompt,
            interaction_type=InteractionType.CHOICE,
            options=interaction_options,
            allow_custom=allow_custom,
            default_value=default
        )
        
        return self._execute_interaction(interaction_prompt)
    
    def get_user_input(self,
                      prompt: str,
                      validation_pattern: str = None,
                      max_length: int = 1000,
                      required: bool = True) -> str:
        """
        获取用户文本输入
        
        Args:
            prompt: 提示信息
            validation_pattern: 验证正则表达式
            max_length: 最大长度
            required: 是否必需
            
        Returns:
            str: 用户输入
        """
        validation_rules = {
            "max_length": max_length,
            "required": required
        }
        
        if validation_pattern:
            validation_rules["pattern"] = validation_pattern
        
        interaction_prompt = InteractionPrompt(
            prompt=prompt,
            interaction_type=InteractionType.INPUT,
            validation_rules=validation_rules
        )
        
        return self._execute_interaction(interaction_prompt)
    
    def get_confirmation(self,
                        prompt: str,
                        default: bool = None) -> bool:
        """
        获取用户确认
        
        Args:
            prompt: 提示信息
            default: 默认值
            
        Returns:
            bool: 用户确认结果
        """
        options = [
            InteractionOption("yes", "是", "确认执行"),
            InteractionOption("no", "否", "取消操作")
        ]
        
        default_value = ""
        if default is not None:
            default_value = "yes" if default else "no"
        
        interaction_prompt = InteractionPrompt(
            prompt=prompt,
            interaction_type=InteractionType.CONFIRMATION,
            options=options,
            default_value=default_value
        )
        
        result = self._execute_interaction(interaction_prompt)
        return result.lower() in ["yes", "y", "是", "确认", "1", "true"]
    
    def get_rating(self,
                  prompt: str,
                  min_score: int = 1,
                  max_score: int = 5,
                  labels: Dict[int, str] = None) -> int:
        """
        获取用户评分
        
        Args:
            prompt: 提示信息
            min_score: 最小分数
            max_score: 最大分数
            labels: 分数标签
            
        Returns:
            int: 用户评分
        """
        if labels is None:
            labels = {
                1: "很差",
                2: "较差", 
                3: "一般",
                4: "较好",
                5: "很好"
            }
        
        options = []
        for score in range(min_score, max_score + 1):
            label = labels.get(score, str(score))
            options.append(InteractionOption(str(score), f"{score}分", label))
        
        interaction_prompt = InteractionPrompt(
            prompt=prompt,
            interaction_type=InteractionType.RATING,
            options=options,
            validation_rules={"min": min_score, "max": max_score}
        )
        
        result = self._execute_interaction(interaction_prompt)
        return int(result)
    
    def get_multi_choice(self,
                        prompt: str,
                        options: List[str],
                        min_selections: int = 1,
                        max_selections: int = None) -> List[str]:
        """
        获取用户多项选择
        
        Args:
            prompt: 提示信息
            options: 选项列表
            min_selections: 最少选择数
            max_selections: 最多选择数
            
        Returns:
            List[str]: 用户选择列表
        """
        if max_selections is None:
            max_selections = len(options)
        
        interaction_options = [
            InteractionOption(value=str(i), label=option)
            for i, option in enumerate(options, 1)
        ]
        
        interaction_prompt = InteractionPrompt(
            prompt=prompt + f"\n(请选择{min_selections}-{max_selections}项，用逗号分隔)",
            interaction_type=InteractionType.MULTI_CHOICE,
            options=interaction_options,
            validation_rules={
                "min_selections": min_selections,
                "max_selections": max_selections
            }
        )
        
        result = self._execute_interaction(interaction_prompt)
        
        # 解析多选结果
        if isinstance(result, str):
            selected_indices = [idx.strip() for idx in result.split(',')]
            selected_options = []
            for idx in selected_indices:
                try:
                    option_index = int(idx) - 1
                    if 0 <= option_index < len(options):
                        selected_options.append(options[option_index])
                except ValueError:
                    continue
            return selected_options
        
        return []
    
    def review_and_modify(self,
                         content: str,
                         content_type: str = "内容",
                         actions: List[str] = None) -> Dict[str, str]:
        """
        内容审查和修改
        
        Args:
            content: 要审查的内容
            content_type: 内容类型描述
            actions: 可用操作列表
            
        Returns:
            Dict: 包含操作和修改内容的字典
        """
        if actions is None:
            actions = ["确认使用", "修改内容", "重新生成", "跳过此项"]
        
        print(f"\n{'='*60}")
        print(f"📋 {content_type}预览:")
        print(f"{'='*60}")
        print(content)
        print(f"{'='*60}")
        
        action = self.get_user_choice(
            f"请选择对此{content_type}的操作:",
            options=actions,
            allow_custom=False
        )
        
        result = {"action": actions[int(action) - 1], "content": content}
        
        if result["action"] == "修改内容":
            modification = self.get_user_input(
                f"请输入修改建议或新的{content_type}:",
                required=True
            )
            result["modification"] = modification
        
        return result
    
    def interactive_outline_review(self, outline_data: Dict) -> Dict:
        """
        交互式大纲审查
        
        Args:
            outline_data: 大纲数据
            
        Returns:
            Dict: 审查结果和修改建议
        """
        print("\n📋 大纲结构预览:")
        self._print_outline_tree(outline_data)
        
        # 整体评价
        overall_rating = self.get_rating(
            "请对整体大纲结构进行评分:",
            min_score=1,
            max_score=5,
            labels={1: "需要重新设计", 2: "需要大幅修改", 3: "基本可用", 4: "较好", 5: "很好"}
        )
        
        modifications = []
        
        if overall_rating <= 3:
            modify_sections = self.get_confirmation("是否需要修改特定章节?")
            
            if modify_sections:
                # 获取需要修改的章节
                section_titles = self._extract_section_titles(outline_data)
                
                sections_to_modify = self.get_multi_choice(
                    "请选择需要修改的章节:",
                    options=section_titles,
                    min_selections=1
                )
                
                # 为每个选中的章节获取修改建议
                for section in sections_to_modify:
                    suggestion = self.get_user_input(
                        f"请输入对章节'{section}'的修改建议:",
                        required=True
                    )
                    modifications.append({
                        "section": section,
                        "suggestion": suggestion
                    })
        
        return {
            "overall_rating": overall_rating,
            "modifications": modifications,
            "approved": overall_rating >= 4
        }
    
    def _execute_interaction(self, interaction_prompt: InteractionPrompt) -> str:
        """执行交互"""
        if self.interface_type == "cli":
            return self._cli_interaction(interaction_prompt)
        elif self.interface_type == "web":
            return self._web_interaction(interaction_prompt)
        elif self.interface_type == "api":
            return self._api_interaction(interaction_prompt)
        else:
            raise ValueError(f"不支持的接口类型: {self.interface_type}")
    
    def _cli_interaction(self, interaction_prompt: InteractionPrompt) -> str:
        """CLI交互实现"""
        print(f"\n{interaction_prompt.prompt}")
        
        # 显示选项
        if interaction_prompt.options:
            print("\n可选项:")
            for option in interaction_prompt.options:
                desc_text = f" - {option.description}" if option.description else ""
                print(f"  {option.value}. {option.label}{desc_text}")
        
        # 显示默认值
        if interaction_prompt.default_value:
            print(f"\n默认值: {interaction_prompt.default_value}")
        
        # 显示自定义输入提示
        if interaction_prompt.allow_custom:
            print("\n或输入自定义内容")
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n请输入选择: ").strip()
                
                # 如果为空且有默认值，使用默认值
                if not user_input and interaction_prompt.default_value:
                    user_input = interaction_prompt.default_value
                
                # 验证输入
                if self._validate_input(user_input, interaction_prompt):
                    # 记录交互历史
                    self.interaction_history.append({
                        "prompt": interaction_prompt.prompt,
                        "response": user_input,
                        "timestamp": self._get_timestamp()
                    })
                    
                    return self._process_user_input(user_input, interaction_prompt)
                else:
                    print("❌ 输入无效，请重新输入")
                    
            except KeyboardInterrupt:
                print("\n\n⚠️ 用户中断操作")
                return ""
            except Exception as e:
                print(f"❌ 输入处理错误: {str(e)}")
    
    def _web_interaction(self, interaction_prompt: InteractionPrompt) -> str:
        """Web交互实现（返回JSON格式，供前端处理）"""
        # 在实际Web应用中，这里会将交互请求发送给前端
        # 现在返回一个模拟的交互请求
        interaction_request = {
            "type": "user_interaction",
            "prompt": interaction_prompt.prompt,
            "interaction_type": interaction_prompt.interaction_type.value,
            "options": [opt.to_dict() for opt in interaction_prompt.options],
            "allow_custom": interaction_prompt.allow_custom,
            "default_value": interaction_prompt.default_value,
            "validation_rules": interaction_prompt.validation_rules
        }
        
        print(f"Web交互请求: {json.dumps(interaction_request, ensure_ascii=False, indent=2)}")
        
        # 在实际应用中，这里会等待前端响应
        # 现在返回一个模拟响应
        if interaction_prompt.options:
            return interaction_prompt.options[0].value
        return interaction_prompt.default_value or "默认响应"
    
    def _api_interaction(self, interaction_prompt: InteractionPrompt) -> str:
        """API交互实现"""
        # 在实际API应用中，这里会通过回调或队列机制处理交互
        interaction_data = {
            "interaction_id": self._generate_interaction_id(),
            "prompt": interaction_prompt.prompt,
            "type": interaction_prompt.interaction_type.value,
            "options": [opt.to_dict() for opt in interaction_prompt.options],
            "metadata": {
                "allow_custom": interaction_prompt.allow_custom,
                "default_value": interaction_prompt.default_value,
                "validation_rules": interaction_prompt.validation_rules,
                "timeout_seconds": interaction_prompt.timeout_seconds
            }
        }
        
        print(f"API交互数据: {json.dumps(interaction_data, ensure_ascii=False, indent=2)}")
        
        # 返回模拟响应
        return interaction_prompt.default_value or "api_response"
    
    def _validate_input(self, user_input: str, interaction_prompt: InteractionPrompt) -> bool:
        """验证用户输入"""
        if not user_input and interaction_prompt.validation_rules.get("required", False):
            return False
        
        # 长度验证
        max_length = interaction_prompt.validation_rules.get("max_length")
        if max_length and len(user_input) > max_length:
            print(f"输入长度超过限制({max_length}字符)")
            return False
        
        # 选择验证
        if interaction_prompt.options and not interaction_prompt.allow_custom:
            valid_values = [opt.value for opt in interaction_prompt.options]
            if user_input not in valid_values:
                return False
        
        # 多选验证
        if interaction_prompt.interaction_type == InteractionType.MULTI_CHOICE:
            try:
                selected_indices = [idx.strip() for idx in user_input.split(',')]
                min_sel = interaction_prompt.validation_rules.get("min_selections", 1)
                max_sel = interaction_prompt.validation_rules.get("max_selections", len(interaction_prompt.options))
                
                if not (min_sel <= len(selected_indices) <= max_sel):
                    print(f"请选择{min_sel}-{max_sel}项")
                    return False
                
                # 验证索引有效性
                for idx in selected_indices:
                    if not idx.isdigit() or int(idx) < 1 or int(idx) > len(interaction_prompt.options):
                        print(f"无效选项: {idx}")
                        return False
                        
            except Exception:
                return False
        
        # 评分验证
        if interaction_prompt.interaction_type == InteractionType.RATING:
            try:
                score = int(user_input)
                min_score = interaction_prompt.validation_rules.get("min", 1)
                max_score = interaction_prompt.validation_rules.get("max", 5)
                if not (min_score <= score <= max_score):
                    print(f"评分必须在{min_score}-{max_score}之间")
                    return False
            except ValueError:
                print("请输入有效的数字评分")
                return False
        
        return True
    
    def _process_user_input(self, user_input: str, interaction_prompt: InteractionPrompt) -> str:
        """处理用户输入"""
        # 如果是选择题，返回选择的选项文本
        if interaction_prompt.interaction_type == InteractionType.CHOICE:
            if interaction_prompt.options and user_input.isdigit():
                index = int(user_input) - 1
                if 0 <= index < len(interaction_prompt.options):
                    return interaction_prompt.options[index].label
        
        return user_input
    
    def _print_outline_tree(self, outline_data: Dict, indent: int = 0):
        """打印大纲树状结构"""
        indent_str = "  " * indent
        
        if isinstance(outline_data, dict):
            title = outline_data.get("title", "未命名")
            print(f"{indent_str}📝 {title}")
            
            if "subsections" in outline_data:
                for subsection in outline_data["subsections"]:
                    self._print_outline_tree(subsection, indent + 1)
    
    def _extract_section_titles(self, outline_data: Dict) -> List[str]:
        """提取章节标题列表"""
        titles = []
        
        def extract_recursive(data):
            if isinstance(data, dict):
                if "title" in data:
                    titles.append(data["title"])
                if "subsections" in data:
                    for sub in data["subsections"]:
                        extract_recursive(sub)
        
        extract_recursive(outline_data)
        return titles
    
    def _generate_interaction_id(self) -> str:
        """生成交互ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_interaction_history(self) -> List[Dict]:
        """获取交互历史"""
        return self.interaction_history.copy()
    
    def clear_interaction_history(self):
        """清空交互历史"""
        self.interaction_history.clear()
        print("✅ 交互历史已清空") 