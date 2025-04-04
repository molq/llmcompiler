# -*- coding: utf-8 -*-
"""
@Author  : Yc-Ma
@Desc    : 测试时间工具
@Time    : 2024-08-02 09:30:49
"""
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

from llmcompiler.custom_llms.deepseek import DeepSeekLLM
from llmcompiler.result.chat import ChatRequest
from llmcompiler.chat.run import RunLLMCompiler
from llmcompiler.tools.tools import DefineTools
from llmcompiler.utils.date.date import formatted_dt_now

# 测试1: 直接调用工具函数的原始版本
def test_time_functions():
    print("\n===== 测试时间工具函数 =====")
    # 导入原始未装饰的函数
    import datetime
    
    # 实现与工具函数相同的功能，但直接调用未装饰的函数版本
    # 获取当前时间
    def get_time(format_str="%Y-%m-%d %H:%M:%S", timezone="local"):
        if timezone.lower() == "utc":
            current_time = datetime.datetime.utcnow()
            timezone_info = "UTC"
        else:
            current_time = datetime.datetime.now()
            timezone_info = "本地时区"
        formatted_time = current_time.strftime(format_str)
        return f"{formatted_time} ({timezone_info})"
    
    # 获取日期信息
    def get_date_details():
        now = datetime.datetime.now()
        weekday = now.weekday()
        weekday_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        is_weekend = weekday >= 5
        quarter = (now.month - 1) // 3 + 1
        month_formatted = f"{now.month:02d}"
        day_formatted = f"{now.day:02d}"
        
        return {
            "year": str(now.year),
            "month": month_formatted,
            "day": day_formatted,
            "weekday": weekday_names[weekday],
            "is_weekend": "是" if is_weekend else "否",
            "quarter": f"Q{quarter}",
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "full_time": now.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    print("当前时间 (默认格式):", get_time())
    print("当前时间 (仅日期):", get_time("%Y-%m-%d"))
    print("当前时间 (仅时间):", get_time("%H:%M:%S"))
    print("UTC时间:", get_time(timezone="utc"))
    
    date_info = get_date_details()
    print("\n日期详细信息:")
    for key, value in date_info.items():
        print(f"  {key}: {value}")

# 测试2: 通过LLMCompiler调用工具
def test_llm_compiler():
    print("\n===== 测试LLMCompiler调用时间工具 =====")
    
    # 创建请求 - 查询当前时间
    message = "现在是几点？今天是几号？是星期几？是否周末？"
    chat = ChatRequest(message=message, session_id="session-id0", create_time=formatted_dt_now())
    
    # 获取工具
    tools = DefineTools().tools()
    
    # 打印工具列表，确认时间工具已注册
    print("已注册的工具:")
    for i, tool in enumerate(tools):
        print(f"  {i+1}. {tool.name} - {tool.description.split('.')[0] if tool.description else ''}")
    
    # 创建DeepSeekLLM实例
    deepseek_llm = DeepSeekLLM(
        model="deepseek-chat",
        temperature=0,
        max_retries=3,
        debug=True,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE")
    )
    
    # 创建LLMCompiler实例
    llm_compiler = RunLLMCompiler(chat, tools, deepseek_llm)
    
    # 生成任务计划
    print("\n生成任务计划:")
    tasks = llm_compiler.planer_invoke()
    for task in tasks:
        if isinstance(task, dict):
            print(f"任务: {task.get('tool')}, 参数: {task.get('args')}, 依赖: {task.get('dependencies')}")
        else:
            print(f"任务: {task}")
    
    # 执行任务并获取结果
    try:
        print("\n执行任务:")
        results = llm_compiler.planer_invoke_output()
        for task, result in results:
            if isinstance(task, dict):
                print(f"任务: {task.get('tool')}, 结果: {result}")
            else:
                print(f"任务: {task}, 结果: {result}")
    except Exception as e:
        print(f"执行任务出错: {str(e)}")

if __name__ == "__main__":
    print("开始测试时间工具")
    
    # 测试工具函数
    test_time_functions()
    
    # 测试LLMCompiler调用
    test_llm_compiler()
    
    print("\n测试完成") 