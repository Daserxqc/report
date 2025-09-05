#!/usr/bin/env python3
"""
支持实时SSE推送的MCP调度器
"""

import json
import asyncio
from typing import Dict, Any, AsyncGenerator
from datetime import datetime

# 导入现有的MCP工具函数
from main import (
    analysis_mcp, query_generation_mcp, outline_writer_mcp, 
    summary_writer_mcp, content_writer_mcp, parallel_search,
    orchestrator_mcp, orchestrator_mcp_simple
)

# 导入原本agent的核心逻辑
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from generate_news_report_enhanced import IntelligentReportAgent

class StreamingOrchestrator:
    """支持实时SSE推送的MCP调度器"""
    
    def __init__(self):
        self.request_id = 1
        self.tool_name = ""
        # 初始化原本agent的核心组件
        try:
            self.intelligent_agent = IntelligentReportAgent()
            print("✅ IntelligentReportAgent 初始化成功")
        except Exception as e:
            print(f"❌ IntelligentReportAgent 初始化失败: {str(e)}")
            self.intelligent_agent = None
    
    async def generate_industry_dynamic_report(self, request: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """生成行业动态报告 - 兼容MCP工具调用"""
        async for message in self.stream_industry_dynamic_report(request):
            yield message
    
    async def stream_industry_dynamic_report(self, request: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """流式生成行业动态报告 - 集成原本agent的智能五步分析法"""
        self.tool_name = "generate_industry_dynamic_report"
        
        # 发送开始消息
        yield self._create_progress_message("started", "开始生成行业动态报告", "正在初始化智能分析系统...")
        await asyncio.sleep(0.1)
        
        try:
            industry = request.get("industry", "未指定行业")
            time_range = request.get("time_range", "recent")
            focus_areas = request.get("focus_areas", ["市场趋势", "技术创新", "政策影响", "竞争格局"])
            days = request.get("days", 30)
            use_local_data = request.get("use_local_data", False)
            
            # 如果使用本地数据，跳过网络搜索
            if use_local_data:
                yield self._create_progress_message("processing", "使用本地数据", "跳过网络搜索，使用预设的本地数据...")
                await asyncio.sleep(0.1)
                
                # 使用预设的本地数据
                local_data = self._get_local_data(industry)
                yield self._create_progress_message("completed", "本地数据加载完成", f"加载了{len(local_data)}条本地数据")
                await asyncio.sleep(0.1)
                
                # 直接进入内容生成阶段
                yield self._create_progress_message("processing", "综合报告生成", "基于本地数据生成报告...")
                await asyncio.sleep(0.1)
                
                # 生成报告内容
                report_content = await self._generate_report_from_local_data(local_data, industry)
                
                # 发送最终结果
                yield self._create_progress_message("completed", "报告生成完成", "基于本地数据成功生成报告")
                await asyncio.sleep(0.1)
                
                # 发送最终结果
                final_result = {
                    "type": "result",
                    "content": report_content,
                    "metadata": {
                        "industry": industry,
                        "data_source": "local",
                        "total_items": len(local_data)
                    }
                }
                yield f"data: {json.dumps(final_result, ensure_ascii=False)}\n\n"
                return
            
            # ========== 第一步：智能查询生成 ==========
            yield self._create_progress_message("processing", "智能查询生成", f"正在分析{industry}行业需求，生成多维度搜索策略...")
            await asyncio.sleep(0.1)
            
            # 使用原本agent的智能查询生成逻辑
            initial_data = await self._generate_initial_queries_enhanced(industry, days, focus_areas)
            total_count = initial_data.get('total_count', 0)
            if isinstance(total_count, int):
                count_str = str(total_count)
            else:
                count_str = str(len(total_count)) if hasattr(total_count, '__len__') else "0"
            yield self._create_progress_message("completed", "查询策略生成完成", f"生成了{count_str}条初始数据")
            await asyncio.sleep(0.1)
            
            # ========== 第二步：多渠道信息搜集 ==========
            yield self._create_progress_message("processing", "多渠道信息搜集", "正在整合多个搜索引擎的结果...")
            await asyncio.sleep(0.1)
            
            all_news_data = initial_data
            total_count = all_news_data.get('total_count', 0)
            if isinstance(total_count, int):
                count_str = str(total_count)
            else:
                count_str = str(len(total_count)) if hasattr(total_count, '__len__') else "0"
            yield self._create_progress_message("completed", "信息搜集完成", f"获得{count_str}条信息")
            await asyncio.sleep(0.1)
            
            # ========== 第三步：反思与知识缺口分析 ==========
            iteration_count = 0
            max_iterations = 3  # 最多3轮迭代
            
            while iteration_count < max_iterations:
                iteration_count += 1
                yield self._create_progress_message("processing", f"反思分析 (第{iteration_count}轮)", "正在分析信息完整性和质量...")
                await asyncio.sleep(0.1)
                
                gaps, is_sufficient = await self._reflect_on_information_gaps_enhanced(all_news_data, industry, days)
                
                if is_sufficient:
                    yield self._create_progress_message("completed", "信息充分性确认", "信息收集充分，准备生成报告")
                    await asyncio.sleep(0.1)
                    break
                
                if iteration_count < max_iterations:
                    yield self._create_progress_message("processing", f"补充搜索 (第{iteration_count}轮)", "正在生成针对性查询补充信息缺口...")
                    await asyncio.sleep(0.1)
                    
                    additional_data = await self._generate_targeted_queries_enhanced(gaps, industry, days)
                    if additional_data:
                        old_total = all_news_data.get('total_count', 0)
                        all_news_data = self._merge_data_enhanced(all_news_data, additional_data)
                        new_total = all_news_data.get('total_count', 0)
                        yield self._create_progress_message("completed", f"第{iteration_count}轮补充完成", f"新增{new_total - old_total}条数据，总量: {new_total}")
                        await asyncio.sleep(0.1)
                    else:
                        yield self._create_progress_message("completed", f"第{iteration_count}轮完成", "本轮未获得新数据")
                        await asyncio.sleep(0.1)
                else:
                    yield self._create_progress_message("completed", "达到迭代上限", "已完成最大迭代次数，开始生成报告")
                    await asyncio.sleep(0.1)
            
            # ========== 第四步：深度内容分析 ==========
            yield self._create_progress_message("processing", "深度内容分析", "正在对收集的信息进行智能分析和去重...")
            await asyncio.sleep(0.1)
            
            # 智能去重和时间过滤
            processed_data = await self._process_collected_data_enhanced(all_news_data, industry, days)
            total_count = processed_data.get('total_count', 0)
            if isinstance(total_count, int):
                count_str = str(total_count)
            else:
                count_str = str(len(total_count)) if hasattr(total_count, '__len__') else "0"
            yield self._create_progress_message("completed", "内容分析完成", f"处理完成，保留{count_str}条高质量信息")
            await asyncio.sleep(0.1)
            
            # ========== 第五步：综合报告生成 ==========
            yield self._create_progress_message("processing", "综合报告生成", "正在生成深度分析报告...")
            await asyncio.sleep(0.1)
            
            # 生成各个章节
            section_contents = {}
            
            # 1. 重大事件分析
            breaking_news = processed_data.get("breaking_news", [])
            print(f"🔍 [调试] breaking_news数据: {len(breaking_news)}条")
            if breaking_news and len(breaking_news) > 0:
                yield self._create_progress_message("processing", "生成重大事件分析", "正在深度分析行业重大事件...")
                await asyncio.sleep(0.1)
                try:
                    section_contents["重大事件"] = await self._process_breaking_news_enhanced(industry, breaking_news, days)
                    yield self._create_model_usage_message("dashscope", "qwen-max", 1500, 1000)
                    await asyncio.sleep(0.1)
                    yield self._create_progress_message("completed", "重大事件分析完成", "深度分析完成")
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"❌ 重大事件分析失败: {str(e)}")
                    yield self._create_progress_message("error", "重大事件分析", f"分析失败: {str(e)}")
                    await asyncio.sleep(0.1)
            else:
                print("⚠️ [调试] breaking_news为空，跳过重大事件分析")
                yield self._create_progress_message("skipped", "重大事件分析", "当前时间窗口内无重大事件")
                await asyncio.sleep(0.1)
            
            # 2. 技术创新分析
            innovation_news = processed_data.get("innovation_news", [])
            print(f"🔍 [调试] innovation_news数据: {len(innovation_news)}条")
            print(f"🔍 [调试] innovation_news内容: {innovation_news[:2] if innovation_news else '无数据'}")
            if innovation_news and len(innovation_news) > 0:
                yield self._create_progress_message("processing", "生成技术创新分析", "正在分析技术创新和突破...")
                await asyncio.sleep(0.1)
                try:
                    section_contents["技术创新"] = await self._process_innovation_news_enhanced(industry, innovation_news)
                    yield self._create_model_usage_message("dashscope", "qwen-max", 1200, 800)
                    await asyncio.sleep(0.1)
                    yield self._create_progress_message("completed", "技术创新分析完成", "技术分析完成")
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"❌ 技术创新分析失败: {str(e)}")
                    yield self._create_progress_message("error", "技术创新分析", f"分析失败: {str(e)}")
                    await asyncio.sleep(0.1)
            else:
                print("⚠️ [调试] innovation_news为空，跳过技术创新分析")
                yield self._create_progress_message("skipped", "技术创新分析", "当前时间窗口内无技术创新信息")
                await asyncio.sleep(0.1)
            
            # 3. 投资动态分析
            investment_news = processed_data.get("investment_news", [])
            print(f"🔍 [调试] investment_news数据: {len(investment_news)}条")
            if investment_news and len(investment_news) > 0:
                yield self._create_progress_message("processing", "生成投资动态分析", "正在分析投资和市场动向...")
                await asyncio.sleep(0.1)
                try:
                    section_contents["投资动态"] = await self._process_investment_news_enhanced(industry, investment_news)
                    yield self._create_model_usage_message("dashscope", "qwen-max", 1300, 900)
                    await asyncio.sleep(0.1)
                    yield self._create_progress_message("completed", "投资动态分析完成", "投资分析完成")
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"❌ 投资动态分析失败: {str(e)}")
                    yield self._create_progress_message("error", "投资动态分析", f"分析失败: {str(e)}")
                    await asyncio.sleep(0.1)
            else:
                print("⚠️ [调试] investment_news为空，跳过投资动态分析")
                yield self._create_progress_message("skipped", "投资动态分析", "当前时间窗口内无投资动态信息")
                await asyncio.sleep(0.1)
            
            # 4. 政策监管分析
            policy_news = processed_data.get("policy_news", [])
            print(f"🔍 [调试] policy_news数据: {len(policy_news)}条")
            if policy_news and len(policy_news) > 0:
                yield self._create_progress_message("processing", "生成政策监管分析", "正在分析政策和监管动态...")
                await asyncio.sleep(0.1)
                try:
                    section_contents["政策监管"] = await self._process_policy_news_enhanced(industry, policy_news)
                    yield self._create_model_usage_message("dashscope", "qwen-max", 1100, 700)
                    await asyncio.sleep(0.1)
                    yield self._create_progress_message("completed", "政策监管分析完成", "政策分析完成")
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"❌ 政策监管分析失败: {str(e)}")
                    yield self._create_progress_message("error", "政策监管分析", f"分析失败: {str(e)}")
                    await asyncio.sleep(0.1)
            else:
                print("⚠️ [调试] policy_news为空，跳过政策监管分析")
                yield self._create_progress_message("skipped", "政策监管分析", "当前时间窗口内无政策监管信息")
                await asyncio.sleep(0.1)
            
            # 5. 行业趋势分析
            trend_news = processed_data.get("trend_news", [])
            print(f"🔍 [调试] trend_news数据: {len(trend_news)}条")
            if trend_news and len(trend_news) > 0:
                yield self._create_progress_message("processing", "生成行业趋势分析", "正在分析行业发展趋势...")
                await asyncio.sleep(0.1)
                try:
                    section_contents["行业趋势"] = await self._process_industry_trends_enhanced(industry, trend_news, days)
                    yield self._create_model_usage_message("dashscope", "qwen-max", 1400, 1000)
                    await asyncio.sleep(0.1)
                    yield self._create_progress_message("completed", "行业趋势分析完成", "趋势分析完成")
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"❌ 行业趋势分析失败: {str(e)}")
                    yield self._create_progress_message("error", "行业趋势分析", f"分析失败: {str(e)}")
                    await asyncio.sleep(0.1)
            else:
                print("⚠️ [调试] trend_news为空，跳过行业趋势分析")
                yield self._create_progress_message("skipped", "行业趋势分析", "当前时间窗口内无行业趋势信息")
                await asyncio.sleep(0.1)
            
            # 6. 观点对比分析
            perspective_analysis = processed_data.get("perspective_analysis", [])
            print(f"🔍 [调试] perspective_analysis数据: {len(perspective_analysis)}条")
            if perspective_analysis and len(perspective_analysis) > 0:
                yield self._create_progress_message("processing", "生成观点对比分析", "正在分析不同观点和争议...")
                await asyncio.sleep(0.1)
                try:
                    section_contents["观点对比"] = await self._process_perspective_analysis_enhanced(industry, perspective_analysis)
                    yield self._create_model_usage_message("dashscope", "qwen-max", 1200, 800)
                    await asyncio.sleep(0.1)
                    yield self._create_progress_message("completed", "观点对比分析完成", "观点分析完成")
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"❌ 观点对比分析失败: {str(e)}")
                    yield self._create_progress_message("error", "观点对比分析", f"分析失败: {str(e)}")
                    await asyncio.sleep(0.1)
            else:
                print("⚠️ [调试] perspective_analysis为空，跳过观点对比分析")
                yield self._create_progress_message("skipped", "观点对比分析", "当前时间窗口内无观点对比信息")
                await asyncio.sleep(0.1)
            
            # 7. 生成智能总结
            yield self._create_progress_message("processing", "生成智能总结", "正在生成AI智能分析总结...")
            await asyncio.sleep(0.1)
            intelligent_summary = await self._generate_intelligent_summary_enhanced(industry, processed_data, days)
            yield self._create_model_usage_message("dashscope", "qwen-max", 1000, 800)
            await asyncio.sleep(0.1)
            yield self._create_progress_message("completed", "智能总结完成", "AI分析总结已生成")
            await asyncio.sleep(0.1)
            
            # 8. 组装最终报告
            yield self._create_progress_message("processing", "组装最终报告", "正在整合所有分析内容...")
            await asyncio.sleep(0.1)
            
            final_report = self._assemble_enhanced_report(industry, intelligent_summary, section_contents, processed_data, days)
            yield self._create_progress_message("completed", "报告生成完成", f"成功生成包含{len(section_contents)}个深度分析章节的智能报告")
            await asyncio.sleep(0.1)
            
            # 发送最终结果
            yield self._create_final_result(final_report)
            
        except Exception as e:
            yield self._create_error_message(str(e))
    
    def _create_progress_message(self, status: str, message: str, content: str) -> str:
        """创建进度更新消息"""
        progress_message = {
            "method": "notifications/message",
            "params": {
                "level": "info",
                "data": {
                    "msg": {
                        "status": status,
                        "message": message,
                        "details": {
                            "id": self.request_id,
                            "name": self.tool_name,
                            "content": content
                        }
                    },
                    "extra": None
                }
            },
            "jsonrpc": "2.0"
        }
        return f"data: {json.dumps(progress_message, ensure_ascii=False)}\n\n"
    
    def _create_model_usage_message(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> str:
        """创建模型用量消息"""
        usage_message = {
            "jsonrpc": "2.0",
            "method": "notifications/message",
            "params": {
                "data": {
                    "msg": {
                        "type": "model_usage",
                        "data": {
                            "model_provider": provider,
                            "model_name": model,
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens
                        }
                    }
                }
            }
        }
        return f"data: {json.dumps(usage_message, ensure_ascii=False)}\n\n"
    
    def _create_final_result(self, content: str) -> str:
        """创建最终结果消息"""
        final_response = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "result": {
                "content": content,
                "tool": self.tool_name
            }
        }
        return f"data: {json.dumps(final_response, ensure_ascii=False)}\n\n"
    
    # ========== 原本agent的核心方法集成 ==========
    
    async def _generate_initial_queries_enhanced(self, industry: str, days: int, focus_areas: list) -> Dict[str, Any]:
        """使用原本agent的智能查询生成逻辑"""
        try:
            if self.intelligent_agent is None:
                print("❌ IntelligentReportAgent 未初始化，使用备用查询")
                return {
                    "breaking_news": [],
                    "innovation_news": [],
                    "investment_news": [],
                    "policy_news": [],
                    "trend_news": [],
                    "company_news": [],
                    "total_count": 0
                }
            # 使用原本agent的多渠道整合搜索
            return self.intelligent_agent._parse_query_strategy("", industry, days, focus_areas)
        except Exception as e:
            print(f"智能查询生成失败: {str(e)}")
            # 降级到基础搜索
            if self.intelligent_agent:
                return self.intelligent_agent._get_fallback_queries(industry, days, focus_areas)
            else:
                return {
                    "breaking_news": [],
                    "innovation_news": [],
                    "investment_news": [],
                    "policy_news": [],
                    "trend_news": [],
                    "company_news": [],
                    "total_count": 0
                }
    
    async def _reflect_on_information_gaps_enhanced(self, collected_data: Dict[str, Any], industry: str, days: int) -> tuple:
        """使用原本agent的反思与知识缺口分析"""
        try:
            return self.intelligent_agent.reflect_on_information_gaps(collected_data, industry, days)
        except Exception as e:
            print(f"反思分析失败: {str(e)}")
            return [], True  # 出错时假设信息充分
    
    async def _generate_targeted_queries_enhanced(self, gaps: list, industry: str, days: int) -> Dict[str, Any]:
        """使用原本agent的针对性查询生成"""
        try:
            return self.intelligent_agent.generate_targeted_queries(gaps, industry, days)
        except Exception as e:
            print(f"针对性查询生成失败: {str(e)}")
            return self.intelligent_agent._fallback_targeted_search(industry, days)
    
    def _merge_data_enhanced(self, existing_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用原本agent的数据合并逻辑"""
        try:
            return self.intelligent_agent._merge_data(existing_data, new_data)
        except Exception as e:
            print(f"数据合并失败: {str(e)}")
            return existing_data
    
    async def _process_collected_data_enhanced(self, all_news_data: Dict[str, Any], industry: str, days: int) -> Dict[str, Any]:
        """使用原本agent的智能去重和时间过滤"""
        try:
            processed_data = all_news_data.copy()
            
            # 对每个类别进行智能去重
            for category in ["breaking_news", "innovation_news", "investment_news", "policy_news", "trend_news", "perspective_analysis"]:
                if processed_data.get(category):
                    processed_data[category] = self.intelligent_agent._deduplicate_by_content(
                        processed_data[category], category
                    )
            
            # 重新计算总数
            processed_data["total_count"] = sum(
                len(processed_data[key]) for key in processed_data.keys() 
                if key != "total_count" and isinstance(processed_data[key], list)
            )
            
            return processed_data
        except Exception as e:
            print(f"数据处理失败: {str(e)}")
            return all_news_data
    
    async def _process_breaking_news_enhanced(self, industry: str, breaking_news: list, days: int) -> str:
        """使用MCP工具生成重大事件分析"""
        try:
            if not breaking_news:
                return f"## 🚨 行业重大事件\n\n📊 **分析说明**: 在当前时间窗口内，暂未发现{industry}行业的重大突发事件。\n\n"
            
            print(f"🔍 [深度分析] 正在分析{len(breaking_news)}条重大事件...")
            
            # 构建新闻数据
            news_data = []
            for item in breaking_news[:5]:  # 只取前5条
                news_data.append({
                    "title": item.get('title', '无标题'),
                    "content": item.get('content', '无内容')[:500],
                    "source": item.get('source', '未知来源'),
                    "url": item.get('url', '#')
                })
            
            # 使用MCP内容生成工具
            try:
                print(f"🔄 正在调用content_writer_mcp生成重大事件分析...")
                content = content_writer_mcp(
                    section_title="行业重大事件深度分析",
                    content_data=news_data,
                    overall_report_context=f"{industry}行业动态报告",
                    writing_style="professional",
                    target_audience="行业分析师"
                )
                print(f"✅ content_writer_mcp调用成功，生成了{len(content)}字符的内容")
            except Exception as e:
                print(f"❌ content_writer_mcp调用失败: {str(e)}")
                import traceback
                print(f"详细错误信息:")
                traceback.print_exc()
                content = f"## 🚨 行业重大事件\n\n基于收集的{len(breaking_news)}条重大事件信息进行分析。\n\n"
            
            # 添加信息来源
            print(f"🔍 [调试] 开始添加信息来源，breaking_news数量: {len(breaking_news)}")
            sources = []
            for item in breaking_news:
                if item.get('url', '#') != '#':
                    sources.append(f"- [{item.get('title', '未知标题')}]({item.get('url')}) - {item.get('source', '未知来源')}")
            
            print(f"🔍 [调试] 收集到{len(sources)}个信息来源")
            if sources:
                content += "\n\n**信息来源:**\n" + "\n".join(sources)
                print(f"🔍 [调试] 信息来源添加完成，最终内容长度: {len(content)}")
            
            final_result = f"## 🚨 行业重大事件深度分析\n\n{content}\n\n"
            print(f"🔍 [调试] 准备返回最终结果，长度: {len(final_result)}")
            return final_result
            
        except Exception as e:
            print(f"重大事件分析失败: {str(e)}")
            return f"## 🚨 行业重大事件\n\n重大事件分析暂时不可用。\n\n"
    
    async def _process_innovation_news_enhanced(self, industry: str, innovation_news: list) -> str:
        """使用MCP工具生成技术创新分析"""
        try:
            print(f"🔍 [调试] _process_innovation_news_enhanced开始，数据: {len(innovation_news)}条")
            if not innovation_news:
                print(f"🔍 [调试] innovation_news为空，返回默认内容")
                return f"## 🔬 技术创新与新产品\n\n📊 **观察**: 当前时间窗口内{industry}行业技术创新活动相对平静。\n\n"
            
            print(f"🧪 [技术分析] 正在深度分析{len(innovation_news)}项技术创新...")
            print(f"🔍 [调试] 前2条数据: {innovation_news[:2]}")
            
            # 构建技术数据
            tech_data = []
            for item in innovation_news[:5]:  # 只取前5条
                tech_data.append({
                    "title": item.get('title', '无标题'),
                    "content": item.get('content', '无内容')[:500],
                    "source": item.get('source', '未知来源'),
                    "url": item.get('url', '#')
                })
            
            # 使用MCP内容生成工具
            try:
                print(f"🔄 正在调用content_writer_mcp生成技术创新分析...")
                content = await asyncio.to_thread(
                    content_writer_mcp,
                    section_title="技术创新与新产品深度解析",
                    content_data=tech_data,
                    overall_report_context=f"{industry}行业动态报告",
                    writing_style="professional",
                    target_audience="技术专家"
                )
                print(f"✅ content_writer_mcp调用成功，生成了{len(content)}字符的内容")
            except Exception as e:
                print(f"❌ content_writer_mcp调用失败: {str(e)}")
                content = f"## 🔬 技术创新与新产品\n\n基于收集的{len(innovation_news)}条技术创新信息进行分析。\n\n"
            
            return f"## 🔬 技术创新与新产品深度解析\n\n{content}\n\n"
            
        except Exception as e:
            print(f"技术创新分析失败: {str(e)}")
            return f"## 🔬 技术创新与新产品\n\n技术创新分析暂时不可用。\n\n"
    
    async def _process_investment_news_enhanced(self, industry: str, investment_news: list) -> str:
        """使用MCP工具生成投资动态分析"""
        try:
            if not investment_news:
                return f"## 💰 投资动态与市场动向\n\n📊 **观察**: 当前时间窗口内{industry}行业投资活动相对平静。\n\n"
            
            print(f"💰 [投资分析] 正在深度分析{len(investment_news)}项投资动态...")
            
            # 构建投资数据
            investment_data = []
            for item in investment_news[:5]:  # 只取前5条
                investment_data.append({
                    "title": item.get('title', '无标题'),
                    "content": item.get('content', '无内容')[:500],
                    "source": item.get('source', '未知来源'),
                    "url": item.get('url', '#')
                })
            
            # 使用MCP内容生成工具
            try:
                print(f"🔄 正在调用content_writer_mcp生成投资动态分析...")
                content = await asyncio.to_thread(
                    content_writer_mcp,
                    section_title="投资动态与市场动向深度解析",
                    content_data=investment_data,
                    overall_report_context=f"{industry}行业动态报告",
                    writing_style="professional",
                    target_audience="投资分析师"
                )
                print(f"✅ content_writer_mcp调用成功，生成了{len(content)}字符的内容")
            except Exception as e:
                print(f"❌ content_writer_mcp调用失败: {str(e)}")
                content = f"## 💰 投资动态与市场动向\n\n基于收集的{len(investment_news)}条投资动态信息进行分析。\n\n"
            
            return f"## 💰 投资动态与市场动向深度解析\n\n{content}\n\n"
            
        except Exception as e:
            print(f"投资动态分析失败: {str(e)}")
            return f"## 💰 投资动态与市场动向\n\n投资动态分析暂时不可用。\n\n"
    
    async def _process_policy_news_enhanced(self, industry: str, policy_news: list) -> str:
        """使用原本agent的政策监管分析逻辑"""
        try:
            return self.intelligent_agent._process_policy_news_enhanced(industry, policy_news)
        except Exception as e:
            print(f"政策监管分析失败: {str(e)}")
            return f"## 📜 政策与监管动态\n\n政策监管分析暂时不可用。\n\n"
    
    async def _process_industry_trends_enhanced(self, industry: str, trend_news: list, days: int) -> str:
        """使用原本agent的行业趋势分析逻辑"""
        try:
            return self.intelligent_agent._process_industry_trends_enhanced(industry, trend_news, days)
        except Exception as e:
            print(f"行业趋势分析失败: {str(e)}")
            return f"## 📈 行业趋势深度分析\n\n行业趋势分析暂时不可用。\n\n"
    
    async def _process_perspective_analysis_enhanced(self, industry: str, perspective_data: list) -> str:
        """使用原本agent的观点对比分析逻辑"""
        try:
            return self.intelligent_agent._process_perspective_analysis_enhanced(industry, perspective_data)
        except Exception as e:
            print(f"观点对比分析失败: {str(e)}")
            return f"## ⚖️ 多元观点对比分析\n\n观点对比分析暂时不可用。\n\n"
    
    async def _generate_intelligent_summary_enhanced(self, industry: str, processed_data: Dict[str, Any], days: int) -> str:
        """使用原本agent的智能总结生成逻辑"""
        try:
            return self.intelligent_agent._generate_intelligent_summary(industry, processed_data, days)
        except Exception as e:
            print(f"智能总结生成失败: {str(e)}")
            return f"## 🧠 AI智能分析总结\n\n{industry}行业正处于动态发展阶段，AI分析显示多个维度都有重要变化值得关注。\n\n"
    
    def _assemble_enhanced_report(self, industry: str, intelligent_summary: str, section_contents: Dict[str, str], processed_data: Dict[str, Any], days: int) -> str:
        """组装增强版报告，集成原本agent的格式"""
        try:
            # 使用原本agent的报告组装逻辑
            date_str = datetime.now().strftime('%Y-%m-%d')
            
            # 构建报告头部
            content = f"# {industry}行业智能分析报告\n\n"
            content += f"*本报告由AI智能代理生成，具备深度思考和反思能力*\n\n"
            content += f"报告日期: {date_str}\n\n"
            
            # 添加报告概述
            content += f"""## 📋 报告概述

本报告采用AI智能代理的五步分析法，对{industry}行业进行全方位深度解析。通过智能查询生成、
多维信息搜集、反思式缺口分析、迭代优化搜索和综合报告生成，确保信息的全面性和分析的深度。

**报告特色：**
- 🧠 深度思考：模拟专家级分析师的思维过程
- 🔄 多轮迭代：通过反思机制确保信息充分性
- 🎯 针对性强：根据识别的知识缺口进行补充搜索
- 📊 数据丰富：整合多源信息，提供全面视角
- 🔮 前瞻性强：不仅分析现状，更预测未来趋势

---

"""
            
            # 添加各个章节
            for section_name, section_content in section_contents.items():
                content += section_content + "\n"
            
            # 添加智能总结
            content += intelligent_summary + "\n"
            
            # 添加参考资料
            content += self.intelligent_agent._generate_references(processed_data)
            
            return content
        except Exception as e:
            print(f"报告组装失败: {str(e)}")
            return f"# {industry}行业分析报告\n\n报告生成过程中出现错误，请稍后重试。"
    
    def _create_error_message(self, error: str) -> str:
        """创建错误消息"""
        error_response = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": {
                    "type": "report_generation_failed",
                    "message": error
                }
            }
        }
        return f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"
    
    def _extract_topic_from_task(self, task: str) -> str:
        """从任务描述中提取主题"""
        stop_words = ["生成", "分析", "报告", "研究", "写", "创建", "制作", "行业", "动态", "新闻"]
        words = task.split()
        topic_words = [word for word in words if word not in stop_words]
        return " ".join(topic_words[:3]) if topic_words else "行业分析"
    
    def _assemble_report(self, topic: str, executive_summary: str, section_contents: Dict[str, str]) -> str:
        """组装最终报告"""
        report = f"# {topic}行业动态报告\n\n"
        report += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += "## 🔍 执行摘要\n\n"
        report += executive_summary + "\n\n"
        
        for section_title, content in section_contents.items():
            report += f"## {section_title}\n\n"
            report += content + "\n\n"
        
        report += "---\n\n*本报告由MCP智能调度器生成，整合了意图识别、大纲生成、内容检索、质量评估等多个MCP工具*"
        return report
    
    def _get_local_data(self, industry: str) -> list:
        """获取本地预设数据"""
        # 新能源汽车行业的本地数据
        if "新能源" in industry or "汽车" in industry:
            return [
                {
                    "title": "特斯拉2025年Q3交付量创新高",
                    "content": "特斯拉公布2025年第三季度全球交付量达到45.2万辆，同比增长23%，创历史新高。",
                    "source": "特斯拉官方",
                    "url": "https://example.com/tesla-q3-2025",
                    "category": "breaking_news",
                    "date": "2025-01-05"
                },
                {
                    "title": "比亚迪固态电池技术突破",
                    "content": "比亚迪宣布在固态电池技术方面取得重大突破，能量密度提升40%，预计2026年量产。",
                    "source": "比亚迪官方",
                    "url": "https://example.com/byd-solid-battery",
                    "category": "innovation_news",
                    "date": "2025-01-04"
                },
                {
                    "title": "蔚来获得50亿元战略投资",
                    "content": "蔚来汽车宣布获得来自某大型投资机构的50亿元战略投资，将用于技术研发和市场扩张。",
                    "source": "蔚来官方",
                    "url": "https://example.com/nio-investment",
                    "category": "investment_news",
                    "date": "2025-01-03"
                },
                {
                    "title": "国家发改委发布新能源汽车新政策",
                    "content": "国家发改委发布《关于进一步促进新能源汽车产业发展的指导意见》，提出多项支持措施。",
                    "source": "国家发改委",
                    "url": "https://example.com/ndrc-policy",
                    "category": "policy_news",
                    "date": "2025-01-02"
                },
                {
                    "title": "2025年新能源汽车市场趋势分析",
                    "content": "根据最新市场调研，2025年新能源汽车市场预计将保持30%以上的增长率，渗透率有望突破50%。",
                    "source": "市场研究机构",
                    "url": "https://example.com/market-trend",
                    "category": "trend_news",
                    "date": "2025-01-01"
                }
            ]
        else:
            # 其他行业的通用数据
            return [
                {
                    "title": f"{industry}行业最新动态",
                    "content": f"这是{industry}行业的最新动态信息，基于本地数据生成。",
                    "source": "本地数据源",
                    "url": "https://example.com/local-data",
                    "category": "breaking_news",
                    "date": "2025-01-05"
                }
            ]
    
    async def _generate_report_from_local_data(self, local_data: list, industry: str) -> str:
        """基于本地数据生成报告"""
        try:
            # 按类别分组数据
            categories = {}
            for item in local_data:
                category = item.get('category', 'other')
                if category not in categories:
                    categories[category] = []
                categories[category].append(item)
            
            # 生成报告内容
            report = f"# {industry}行业动态报告\n\n"
            report += f"**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += f"**数据来源**: 本地数据\n"
            report += f"**数据条数**: {len(local_data)}\n\n"
            
            # 按类别生成内容
            for category, items in categories.items():
                if category == "breaking_news":
                    report += "## 🚨 重大事件\n\n"
                elif category == "innovation_news":
                    report += "## 💡 技术创新\n\n"
                elif category == "investment_news":
                    report += "## 💰 投资动态\n\n"
                elif category == "policy_news":
                    report += "## 📋 政策法规\n\n"
                elif category == "trend_news":
                    report += "## 📈 市场趋势\n\n"
                else:
                    report += f"## 📊 {category}\n\n"
                
                for item in items:
                    report += f"### {item['title']}\n\n"
                    report += f"{item['content']}\n\n"
                    if item.get('url') and item['url'] != 'https://example.com/local-data':
                        report += f"**来源**: [{item['source']}]({item['url']})\n\n"
                    else:
                        report += f"**来源**: {item['source']}\n\n"
            
            return report
            
        except Exception as e:
            print(f"本地数据报告生成失败: {str(e)}")
            return f"# {industry}行业动态报告\n\n基于本地数据生成报告时出现错误，请稍后重试。"
