#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大纲创建详细调试测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.outline_writer_mcp import OutlineWriterMcp
from collectors.llm_processor import LLMProcessor
import traceback

def debug_outline_creation():
    """详细调试大纲创建过程"""
    print("\n" + "="*80)
    print("🔍 大纲创建详细调试")
    print("="*80)
    
    try:
        # 1. 测试LLM处理器
        print("\n1. 测试LLM处理器初始化...")
        llm = LLMProcessor()
        print(f"✅ LLM处理器初始化成功")
        print(f"   模型: {llm.model}")
        print(f"   API URL: {llm.base_url}")
        print(f"   有API密钥: {bool(llm.api_key)}")
        
        # 2. 测试简单LLM调用
        print("\n2. 测试简单LLM调用...")
        try:
            simple_response = llm.call_llm_api("请回答：1+1等于几？")
            print(f"✅ 简单LLM调用成功: {simple_response[:100]}...")
        except Exception as e:
            print(f"❌ 简单LLM调用失败: {str(e)}")
            print(f"   错误详情: {traceback.format_exc()}")
            return False
        
        # 3. 测试JSON LLM调用
        print("\n3. 测试JSON LLM调用...")
        try:
            json_prompt = "请以JSON格式返回：{\"result\": 2, \"explanation\": \"1+1=2\"}"
            json_response = llm.call_llm_api_json(json_prompt)
            print(f"✅ JSON LLM调用成功: {json_response}")
        except Exception as e:
            print(f"❌ JSON LLM调用失败: {str(e)}")
            print(f"   错误详情: {traceback.format_exc()}")
            return False
        
        # 4. 测试大纲创建器初始化
        print("\n4. 测试大纲创建器初始化...")
        outline_writer = OutlineWriterMcp()
        print(f"✅ 大纲创建器初始化成功")
        print(f"   有LLM支持: {outline_writer.has_llm}")
        
        # 5. 测试大纲创建（无参考数据）
        print("\n5. 测试大纲创建（无参考数据）...")
        try:
            outline = outline_writer.create_outline(
                topic="人工智能技术发展趋势",
                report_type="comprehensive",
                user_requirements="请创建一个详细的技术报告大纲"
            )
            print(f"✅ 大纲创建成功")
            print(f"   大纲标题: {outline.title}")
            print(f"   主章节数量: {len(outline.subsections)}")
            
            if outline.subsections:
                print("   主章节列表:")
                for i, section in enumerate(outline.subsections[:3]):
                    print(f"     {i+1}. {section.title}")
            else:
                print("   ⚠️ 没有主章节！")
                
        except Exception as e:
            print(f"❌ 大纲创建失败: {str(e)}")
            print(f"   错误详情: {traceback.format_exc()}")
            return False
        
        # 6. 测试大纲创建（带参考数据）
        print("\n6. 测试大纲创建（带参考数据）...")
        try:
            reference_data = [
                {"title": "AI技术发展报告", "content": "人工智能技术在各个领域都有重要应用..."},
                {"title": "机器学习趋势", "content": "机器学习算法不断演进，深度学习成为主流..."}
            ]
            
            outline_with_ref = outline_writer.create_outline(
                topic="人工智能技术发展趋势",
                report_type="technical_report",
                user_requirements="基于参考资料创建技术报告大纲",
                reference_data=reference_data
            )
            
            print(f"✅ 带参考数据的大纲创建成功")
            print(f"   大纲标题: {outline_with_ref.title}")
            print(f"   主章节数量: {len(outline_with_ref.subsections)}")
            
            if outline_with_ref.subsections:
                print("   主章节列表:")
                for i, section in enumerate(outline_with_ref.subsections[:3]):
                    print(f"     {i+1}. {section.title}")
            else:
                print("   ⚠️ 没有主章节！")
                
        except Exception as e:
            print(f"❌ 带参考数据的大纲创建失败: {str(e)}")
            print(f"   错误详情: {traceback.format_exc()}")
            return False
        
        print("\n🎉 所有调试测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 调试过程中发生错误: {str(e)}")
        print(f"   错误详情: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    debug_outline_creation()