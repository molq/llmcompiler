# -*- coding: utf-8 -*-
"""
@Author  : Yc-Ma
@Desc    : 时间工具
@Time    : 2024-08-02 09:30:49
"""
import datetime
from typing import Dict, List, Optional
from langchain.tools import BaseTool
from pydantic.v1 import BaseModel, Field


class TimeToolBase(BaseTool):
    """时间工具基类"""
    
    def _parse_output(self, output: str) -> str:
        """工具输出格式化"""
        return output


class GetCurrentTime(TimeToolBase):
    """获取当前时间工具"""
    name = "get_current_time"
    description = """获取当前时间。
    
参数:
- format: 时间格式，默认为'%Y-%m-%d %H:%M:%S'。可选格式：'%Y-%m-%d'(仅日期)，'%H:%M:%S'(仅时间)等
- timezone: 时区，支持'local'(本地时区)，'utc'(UTC时间)
    
返回:
- 指定格式的当前时间字符串"""
    
    def _run(self, format: str = "%Y-%m-%d %H:%M:%S", timezone: str = "local", **kwargs) -> str:
        """执行工具逻辑"""
        print("================================ GetCurrentTime {format} ================================")
        if timezone.lower() == "utc":
            current_time = datetime.datetime.now(datetime.UTC)
            timezone_info = "UTC"
        else:  # 默认使用本地时区
            current_time = datetime.datetime.now()
            timezone_info = "本地时区"
        
        formatted_time = current_time.strftime(format)
        return f"{formatted_time} ({timezone_info})"
    
    async def _arun(self, format: str = "%Y-%m-%d %H:%M:%S", timezone: str = "local") -> str:
        """异步执行工具逻辑"""
        return self._run(format, timezone)


class GetDateInfo(TimeToolBase):
    """获取日期详细信息工具"""
    name = "get_date_info"
    description = """获取当前日期的详细信息，包括年、月、日、星期、是否周末、季度等。
    
返回:
- 包含日期详细信息的字典"""
    
    def _run(self, **kwargs) -> Dict[str, str]:
        """执行工具逻辑"""
        now = datetime.datetime.now()
        
        # 获取当前是星期几
        weekday = now.weekday()
        weekday_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        
        # 判断是否周末
        is_weekend = weekday >= 5
        
        # 判断当前季度
        quarter = (now.month - 1) // 3 + 1
        
        # 格式化月份和日期，确保两位数
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
    
    async def _arun(self, **kwargs) -> Dict[str, str]:
        """异步执行工具逻辑"""
        return self._run()


# 创建工具实例
get_current_time = GetCurrentTime()
get_date_info = GetDateInfo()


def time_tool_factory() -> List[BaseTool]:
    """
    创建时间相关工具集
    
    返回:
    - 时间工具列表
    """
    tools = [
        get_current_time,
        get_date_info
    ]
    return tools 