# -*- coding: utf-8 -*-
"""
@Author  : Yc-Ma
@Desc    : DeepSeek LLM 测试
@Time    : 2024-08-02 09:30:49
"""
import os
import logging
from dotenv import load_dotenv
from llmcompiler.custom_llms.deepseek import DeepSeekLLM
from llmcompiler.chat.run import RunLLMCompiler
from llmcompiler.result.chat import ChatRequest
from llmcompiler.tools.tools import DefineTools
from llmcompiler.utils.date.date import formatted_dt_now
from langchain.schema import HumanMessage, SystemMessage

# 配置日志
logging.basicConfig(level=logging.INFO)

# 加载环境变量
load_dotenv()

print("====== 测试1: 使用简单提示直接测试DeepSeek模型 ======")
deepseek_llm = DeepSeekLLM(
    model="deepseek-chat",
    temperature=0,
    max_retries=3,
    debug=True,
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE")
)

# 简单提示测试
simple_prompt = "介绍一下你自己"
try:
    response = deepseek_llm(simple_prompt)
    print(f"DeepSeek回应: {response}")
except Exception as e:
    print(f"简单提示测试失败: {str(e)}")

print("\n====== 测试2: 使用消息格式测试DeepSeek模型 ======")
try:
    # 创建消息列表，包含系统和用户消息
    messages = [
        SystemMessage(content="你是一个专业的金融助手"),
        HumanMessage(content="什么是ETF基金？")
    ]
    response = deepseek_llm.generate_prompt([messages])
    print(f"消息格式测试结果: {response}")
except Exception as e:
    print(f"消息格式测试失败: {str(e)}")

print("\n====== 测试3: 作为LLMCompiler组件测试 ======")
# 创建聊天请求
message = "简单介绍下股票市场"
chat = ChatRequest(message=message, session_id="session-id0", create_time=formatted_dt_now())

# 获取默认工具
tools = DefineTools().tools()

# 创建LLMCompiler实例
llm_compiler = RunLLMCompiler(chat, tools, deepseek_llm)

# 只生成计划
try:
    print("开始执行LLMCompiler规划...")
    tasks = llm_compiler.planer_invoke()
    print("生成的任务计划:")
    for task in tasks:
        print(f"任务: {task.name}, 参数: {task.args}, 依赖: {task.dependencies}")
except Exception as e:
    print(f"规划阶段出现错误: {str(e)}")