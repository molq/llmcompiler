# -*- coding: utf-8 -*-
"""
@Desc    : AKShare Tools Registry - A collection of all AKShare tools
"""
import logging
from typing import List, Dict, Any
from langchain_core.tools import BaseTool

from llmcompiler.tools.basetool.akshare_stock_tool import AKShareStockTool
from llmcompiler.tools.basetool.akshare_fund_tool import AKShareFundTool
from llmcompiler.tools.basetool.akshare_macro_tool import AKShareMacroTool
from llmcompiler.tools.basetool.akshare_dynamic_tool import AKShareDynamicTool
from llmcompiler.tools.basetool.akshare_category_tools import (
    get_akshare_category_tools,
    get_common_akshare_tools
)

logger = logging.getLogger(__name__)

try:
    import akshare as ak
except ImportError:
    raise ImportError(
        "The 'akshare' package is required to use this class. Please install it using 'pip install akshare'.")


def get_akshare_tools(tool_mode: str = "essential") -> List[BaseTool]:
    """
    返回AKShare工具列表
    
    Args:
        tool_mode: 工具模式，可选值:
            - "essential": 只返回基本工具集
            - "common": 返回常用工具集
            - "categories": 返回分类工具集
            - "full": 返回所有可用工具集，包括动态工具和基本、分类工具
    
    Returns:
        AKShare工具列表
    """
    # 基本工具
    essential_tools = [
        AKShareStockTool(),
        AKShareFundTool(),
        AKShareMacroTool(),
    ]
    
    if tool_mode == "essential":
        logger.info(f"已注册 {len(essential_tools)} 个基本AKShare工具")
        return essential_tools
    
    # 将基本工具添加到结果列表
    result_tools = essential_tools.copy()
    
    # 添加动态工具
    dynamic_tool = AKShareDynamicTool()
    result_tools.append(dynamic_tool)
    
    if tool_mode == "common":
        # 添加常用工具
        common_tools = get_common_akshare_tools(max_tools=20)
        result_tools.extend(common_tools)
        logger.info(f"已注册 {len(result_tools)} 个AKShare工具 (基本 + 动态 + 常用)")
        return result_tools
    
    elif tool_mode == "categories":
        # 添加分类工具
        category_tools = get_akshare_category_tools()
        result_tools.extend(category_tools)
        logger.info(f"已注册 {len(result_tools)} 个AKShare工具 (基本 + 动态 + 分类)")
        return result_tools
    
    elif tool_mode == "full":
        # 添加常用工具和分类工具
        common_tools = get_common_akshare_tools(max_tools=20)
        category_tools = get_akshare_category_tools()
        result_tools.extend(common_tools)
        result_tools.extend(category_tools)
        logger.info(f"已注册 {len(result_tools)} 个AKShare工具 (基本 + 动态 + 常用 + 分类)")
        return result_tools
    
    else:
        logger.warning(f"未知工具模式: {tool_mode}，使用默认模式 'essential'")
        return essential_tools


def get_akshare_tool_stats() -> Dict[str, Any]:
    """
    获取AKShare工具统计信息
    
    Returns:
        包含工具统计信息的字典
    """
    try:
        from llmcompiler.tools.basetool.akshare_category_tools import get_akshare_methods_by_category
        
        # 获取分类后的方法
        categorized_methods = get_akshare_methods_by_category()
        
        # 计算每个分类的方法数量
        category_counts = {cat: len(methods) for cat, methods in categorized_methods.items()}
        
        # 计算总方法数
        total_methods = sum(category_counts.values())
        
        # 获取常用方法
        from llmcompiler.tools.basetool.akshare_category_tools import get_common_akshare_methods
        common_methods = get_common_akshare_methods()
        
        return {
            "total_methods": total_methods,
            "category_counts": category_counts,
            "common_method_count": len(common_methods),
            "akshare_version": ak.__version__
        }
    except Exception as e:
        logger.error(f"获取AKShare工具统计信息时出错: {str(e)}")
        return {"error": str(e)}


if __name__ == '__main__':
    # 测试不同模式下的工具数量
    for mode in ["essential", "common", "categories", "full"]:
        tools = get_akshare_tools(tool_mode=mode)
        print(f"Mode '{mode}': {len(tools)} 工具")
        
        # 打印工具名称
        tool_names = [tool.name for tool in tools]
        print(f"工具列表: {tool_names}")
        print("-" * 50)
    
    # 打印统计信息
    stats = get_akshare_tool_stats()
    print(f"AKShare统计信息:")
    for key, value in stats.items():
        print(f"{key}: {value}") 