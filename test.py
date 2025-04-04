#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试AKShare工具集成到LLMCompiler
"""

import logging
import sys
from pprint import pprint

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
from llmcompiler.custom_llms.deepseek import DeepSeekLLM
from llmcompiler.tools.basic import Tools
from llmcompiler.result.chat import ChatRequest
from langchain_openai.chat_models.base import ChatOpenAI
from llmcompiler.chat.run import RunLLMCompiler
from llmcompiler.tools.tools import DefineTools
from llmcompiler.utils.date.date import formatted_dt_now
import os
from llmcompiler.tools.basetool.akshare_tools import (
    get_akshare_tools,
    get_akshare_tool_stats,
)


load_dotenv()

# chat = ChatRequest(message="How has the return been for Tech stocks since their inception?")
# tools = Tools.load_tools(["../llmcompiler/tools/basetool/stock_info_fake.py",
#                           "../llmcompiler/tools/basetool/multi_param_dep_v1.py"])

# chat = ChatRequest(message="宁德时代的股票代码是什么？")
# tools = DefineTools().tools()

# # chat = ChatRequest(
# #     message="How has the return been for Tech stocks since their inception? Calculate the average return of tech stocks.")
# # tools = Tools.load_tools(["../llmcompiler/tools/math",
# #                           "../llmcompiler/tools/basetool/stock_info_fake.py",
# #                           "../llmcompiler/tools/basetool/multi_param_dep_v3.py"])

# print(tools)

# llm = ChatOpenAI(model="deepseek-chat", temperature=0, max_retries=3)

# llm_compiler = RunLLMCompiler(chat, tools, llm)
# print(llm_compiler())

# # llm_compiler.runWithoutJoiner()


def test_akshare_tools_loading():
    """测试AKShare工具加载功能"""
    print("\n=== 测试AKShare工具加载 ===")

    # 测试不同模式下的工具加载
    for mode in ["essential", "common", "categories", "full"]:
        try:
            tools = get_akshare_tools(tool_mode=mode)
            print(f"模式 '{mode}': 成功加载 {len(tools)} 个工具")
            # 打印前3个工具名称
            if tools:
                tool_names = [tool.name for tool in tools[:3]]
                print(f"示例工具: {tool_names}")
        except Exception as e:
            print(f"模式 '{mode}' 加载失败: {str(e)}")

    # 获取统计信息
    try:
        stats = get_akshare_tool_stats()
        print("\n=== AKShare工具统计 ===")
        pprint(stats)
    except Exception as e:
        print(f"获取统计信息失败: {str(e)}")


def test_define_tools_integration():
    """测试AKShare工具与DefineTools的集成"""
    print("\n=== 测试AKShare工具与DefineTools的集成 ===")

    try:
        # 创建聊天请求
        chat = ChatRequest(message="华友钴业的股票代码是多少？")

        # 初始化DefineTools
        tools_manager = DefineTools(chat)

        # 获取工具列表
        all_tools = tools_manager.tools()

        # 统计AKShare工具数量
        akshare_tools = [tool for tool in all_tools if tool.name.startswith("akshare_")]

        print(f"总工具数量: {len(all_tools)}")
        print(f"AKShare工具数量: {len(akshare_tools)}")

        if akshare_tools:
            print("AKShare工具示例:")
            for tool in akshare_tools[:3]:
                print(f"- {tool.name}: {tool.description[:50]}...")

        return tools_manager
    except Exception as e:
        print(f"集成测试失败: {str(e)}")
        return None


def test_llm_compiler():
    """测试LLMCompiler与AKShare工具的集成"""
    print("\n=== 测试LLMCompiler与AKShare工具的集成 ===")

    try:
        # 创建聊天请求
        chat = ChatRequest(message="华友钴业的股票代码是多少？")

        # 获取工具
        tools_manager = DefineTools(chat)
        tools = tools_manager.tools()

        # 初始化LLM
        try:
            # 尝试使用OpenAI模型
            llm = DeepSeekLLM(
                model="deepseek-chat",
                debug=True,
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_API_BASE"),
                temperature=0,
                max_retries=1,
            )

            # 初始化LLMCompiler
            llm_compiler = RunLLMCompiler(chat, tools, llm)
            print("成功初始化LLMCompiler")

            # 返回llm_compiler以便进一步测试
            return llm_compiler
        except Exception as e:
            print(f"初始化LLM失败: {str(e)}")
            return None
    except Exception as e:
        print(f"LLMCompiler集成测试失败: {str(e)}")
        return None


def test_llm_logging():
    """测试大模型返回的数据日志记录功能"""
    import logging
    import os
    import json
    import sys
    from langchain.schema import HumanMessage, SystemMessage

    # 设置日志级别为INFO，以显示所有API调用日志
    logging.basicConfig(level=logging.INFO)

    print("开始测试大模型日志记录功能")

    # 提示用户输入API密钥
    api_key = input("请输入API密钥: ").strip()
    if not api_key:
        print("未提供API密钥，测试终止")
        return

    # 选择模型类型
    print("\n选择模型类型:")
    print("1. DeepSeek")
    print("2. OpenAI")
    choice = input("请选择 (1/2): ").strip()

    # 根据选择导入相应的模块
    if choice == "1":
        try:
            from llmcompiler.custom_llms.deepseek import DeepSeekLLM

            model_type = "deepseek"
            model_name = "deepseek-chat"
            model_class = DeepSeekLLM
        except ImportError:
            print("无法导入DeepSeekLLM模块")
            return
    elif choice == "2":
        try:
            from llmcompiler.custom_llms.openai import OpenaiLLM

            model_type = "openai"
            model_name = "gpt-3.5-turbo"
            model_class = OpenaiLLM
        except ImportError:
            print("无法导入OpenaiLLM模块")
            return
    else:
        print("无效的选择")
        return

    # 可选地让用户指定模型名称
    custom_model = input(f"\n请输入模型名称 (默认: {model_name}): ").strip()
    if custom_model:
        model_name = custom_model

    print(f"\n测试配置:")
    print(f"- 模型类型: {model_type}")
    print(f"- 模型名称: {model_name}")

    # 构造测试消息
    messages = [
        {"role": "system", "content": "你是一个智能助手。"},
        {"role": "user", "content": "用一句话介绍自己。"},
    ]

    try:
        # 初始化模型
        llm = model_class(api_key=api_key, model=model_name)
        llm.debug = True
        print(f"\n成功初始化模型: {model_type} - {model_name}")

        # 调用API
        print("\n正在调用API...")
        try:
            response = llm.api(messages)
            print(f"\nAPI调用成功!")
            print(
                f"响应内容: {response[:100]}..."
                if len(response) > 100
                else f"响应内容: {response}"
            )
        except Exception as e:
            print(f"\nAPI调用失败: {str(e)}")
    except Exception as e:
        print(f"\n模型初始化失败: {str(e)}")

    print("\n测试完成，请查看上方日志输出")


def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)
    # 测试AKShare工具加载
    # test_akshare_tools_loading()

    # 测试与DefineTools的集成
    tools_manager = test_define_tools_integration()

    # 如果需要测试LLMCompiler，取消下面的注释
    llm_compiler = test_llm_compiler()
    if llm_compiler:
        # 运行LLMCompiler
        print("\n=== 运行LLMCompiler ===")
        result = llm_compiler()
        print(f"查询结果: {result}")


if __name__ == "__main__":
    main()
    # print("=" * 30)
    # print("选择要运行的测试:")
    # print("1. AKShare工具与DefineTools的集成测试")
    # print("2. LLMCompiler与AKShare工具的集成测试")
    # print("3. 大模型日志记录功能测试")

    # choice = input("请输入选项 (1/2/3): ").strip()

    # if choice == "1":
    #     test_akshare_tools_loading()
    # elif choice == "2":
    #     test_llm_compiler()
    # elif choice == "3":
    #     test_llm_logging()
    # else:
    #     print("无效的选项")
