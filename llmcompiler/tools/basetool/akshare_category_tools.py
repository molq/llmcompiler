# -*- coding: utf-8 -*-
"""
@Desc    : AKShare分类工具 - 按分类组织AKShare方法
"""
import re
import inspect
import logging
from typing import List, Dict, Optional, Set, Any, Type

from langchain_core.tools import BaseTool
from pydantic import Field, BaseModel

from llmcompiler.tools.basetool.akshare_dynamic_tool import (
    AKShareDynamicTool, 
    create_akshare_tool_for_method,
    AKSHARE_CATEGORIES,
    SubclassedBaseTool
)

logger = logging.getLogger(__name__)

try:
    import akshare as ak
except ImportError:
    raise ImportError(
        "The 'akshare' package is required to use this class. Please install it using 'pip install akshare'.")


# 方法名前缀与分类的映射
METHOD_PREFIX_CATEGORIES = {
    "stock_": "stock",
    "fund_": "fund",
    "bond_": "bond",
    "option_": "option",
    "futures_": "future",
    "future_": "future",
    "fx_": "fx",
    "currency_": "fx",
    "macro_": "macro",
    "index_": "index",
    "indices_": "index",
    "crypto_": "crypto",
}


def categorize_akshare_method(method_name: str) -> str:
    """
    根据方法名对AKShare方法进行分类
    
    Args:
        method_name: AKShare方法名
        
    Returns:
        分类名称
    """
    for prefix, category in METHOD_PREFIX_CATEGORIES.items():
        if method_name.startswith(prefix):
            return category
    
    # 没有匹配前缀，进一步检查方法名中的关键词
    keywords = {
        "stock": ["stock", "shares", "equity", "a_share", "hk_", "us_", "zh_a"],
        "fund": ["fund", "etf"],
        "bond": ["bond", "repo", "shibor"],
        "option": ["option"],
        "future": ["future", "futures", "cffex", "shfe", "czce", "dce"],
        "fx": ["fx", "currency", "cny", "exchange"],
        "macro": ["macro", "gdp", "cpi", "ppi", "pmi"],
        "index": ["index", "indices", "sz_", "sh_", "zz_"],
        "crypto": ["crypto", "bitcoin", "blockchain"],
    }
    
    for category, words in keywords.items():
        for word in words:
            if word in method_name:
                return category
    
    # 默认分类
    return "others"


def get_akshare_methods_by_category() -> Dict[str, List[str]]:
    """
    按类别获取AKShare所有方法
    
    Returns:
        按类别组织的方法名字典
    """
    # 获取所有方法
    all_methods = AKShareDynamicTool.get_available_methods()
    
    # 按类别组织
    categorized_methods = {category: [] for category in AKSHARE_CATEGORIES.keys()}
    
    for method_name in all_methods:
        category = categorize_akshare_method(method_name)
        categorized_methods[category].append(method_name)
    
    return categorized_methods


def get_common_akshare_methods() -> List[str]:
    """
    获取常用的AKShare方法列表
    
    Returns:
        常用方法名列表
    """
    return [
        # 股票
        "stock_zh_a_hist",  # A股历史数据
        "stock_zh_a_spot",  # A股实时行情
        "stock_individual_info_em",  # 个股信息
        "stock_zh_a_daily",  # A股日线行情
        "stock_zh_index_daily",  # A股指数日线行情
        
        # 基金
        "fund_em_open_fund_info",  # 开放式基金信息
        "fund_em_etf_fund_daily",  # ETF基金行情
        "fund_em_fund_name",  # 基金名称
        "fund_em_open_fund_daily",  # 开放式基金行情
        
        # 债券
        "bond_zh_hs_cov_daily",  # 可转债行情
        "bond_zh_hs_daily",  # 债券行情
        "bond_china_yield",  # 中国债券收益率曲线
        
        # 宏观经济
        "macro_china_cpi_yearly",  # 中国年度CPI
        "macro_china_ppi_yearly",  # 中国年度PPI
        "macro_china_gdp_yearly",  # 中国年度GDP
        "macro_china_pmi_yearly",  # 中国年度PMI
        
        # 外汇
        "fx_spot_quote",  # 外汇即期报价
        "currency_latest",  # 货币最新行情
        
        # 期货
        "futures_main_sina",  # 期货主力合约
        "futures_daily",  # 期货日线行情
        
        # 指数
        "index_zh_a_hist",  # A股指数历史行情
        "index_global",  # 全球指数数据
        
        # 加密货币
        "crypto_hist",  # 加密货币历史数据
    ]


class AKShareCategoryToolInput(BaseModel):
    """AKShare分类工具输入模型"""
    category_key: str = Field(description="分类名称键")


class AKShareCategoryTool(BaseTool):
    """
    AKShare分类工具基类
    """
    name: str = ""
    description: str = ""
    args_schema: Optional[Type[BaseModel]] = AKShareCategoryToolInput
    
    def __init__(self, category_key: str):
        """
        初始化分类工具
        
        Args:
            category_key: 分类名称键
        """
        # 获取分类信息
        category_name = AKSHARE_CATEGORIES.get(category_key, "未知分类")
        
        # 设置工具属性
        self.name = f"akshare_{category_key}_category"
        self.description = f"获取AKShare {category_name}分类下的所有可用方法信息"
        self._category_key = category_key
        self.category_name = category_name
        
        # 初始化基类
        super().__init__()
    
    def _run(self, **kwargs):
        """
        运行分类工具，列出该分类下的所有方法
        """
        try:
            categorized_methods = get_akshare_methods_by_category()
            methods = categorized_methods.get(self._category_key, [])
            
            result = {
                "category": self._category_key,
                "category_name": self.category_name,
                "method_count": len(methods),
                "methods": []
            }
            
            for method_name in methods[:30]:  # 只返回前30个方法
                try:
                    method_info = AKShareDynamicTool.get_method_info(method_name)
                    result["methods"].append({
                        "name": method_name,
                        "description": method_info.get("doc", "").split("\n")[0],
                        "parameter_count": len(method_info.get("parameters", {}))
                    })
                except Exception as e:
                    logger.error(f"获取方法 {method_name} 信息时出错: {str(e)}")
            
            return result
        except Exception as e:
            logger.error(f"执行AKShare分类工具出错: {str(e)}")
            return {"error": str(e)}

    async def _arun(self, **kwargs):
        """异步执行分类工具"""
        return self._run(**kwargs)


def get_akshare_category_tools() -> List[BaseTool]:
    """
    获取所有AKShare分类工具
    
    Returns:
        分类工具列表
    """
    tools = []
    
    for category_key in AKSHARE_CATEGORIES.keys():
        try:
            category_name = AKSHARE_CATEGORIES.get(category_key, "未知分类")
            
            # 为每个分类定义一个专门的工具类
            class AKShareCategoryToolForCategory(BaseTool):
                name = f"akshare_{category_key}_category"
                description = f"获取AKShare {category_name}分类下的所有可用方法信息"
                
                def _run(self, **kwargs) -> dict:
                    """
                    运行分类工具，列出该分类下的所有方法
                    
                    Returns:
                        包含分类方法信息的字典
                    """
                    try:
                        categorized_methods = get_akshare_methods_by_category()
                        methods = categorized_methods.get(category_key, [])
                        
                        result = {
                            "category": category_key,
                            "category_name": category_name,
                            "method_count": len(methods),
                            "methods": []
                        }
                        
                        for method_name in methods[:30]:  # 只返回前30个方法
                            try:
                                method_info = AKShareDynamicTool.get_method_info(method_name)
                                result["methods"].append({
                                    "name": method_name,
                                    "description": method_info.get("doc", "").split("\n")[0],
                                    "parameter_count": len(method_info.get("parameters", {}))
                                })
                            except Exception as e:
                                logger.error(f"获取方法 {method_name} 信息时出错: {str(e)}")
                        
                        return result
                    except Exception as e:
                        logger.error(f"执行AKShare分类工具出错: {str(e)}")
                        return {"error": str(e)}
                
                async def _arun(self, **kwargs):
                    """异步执行分类工具"""
                    return self._run(**kwargs)
            
            # 添加工具实例
            tools.append(AKShareCategoryToolForCategory())
        except Exception as e:
            logger.error(f"创建分类工具 {category_key} 时出错: {str(e)}")
    
    return tools


def get_common_akshare_tools(max_tools: int = 30) -> List[BaseTool]:
    """
    获取常用AKShare方法的工具
    
    Args:
        max_tools: 最大工具数量
        
    Returns:
        常用工具列表
    """
    common_methods = get_common_akshare_methods()
    tools = []
    
    for method_name in common_methods[:max_tools]:
        tool = create_akshare_tool_for_method(method_name)
        if tool:
            tools.append(tool)
    
    return tools


if __name__ == "__main__":
    # 测试分类方法
    categorized_methods = get_akshare_methods_by_category()
    for category, methods in categorized_methods.items():
        print(f"分类 {category} ({AKSHARE_CATEGORIES.get(category)}): {len(methods)} 个方法")
        if methods:
            print(f"  示例方法: {methods[:3]}")
    
    # 测试常用方法
    common_methods = get_common_akshare_methods()
    print(f"常用方法: {len(common_methods)} 个")
    print(f"  {common_methods}")
    
    # 测试创建工具
    common_tools = get_common_akshare_tools(max_tools=5)
    for tool in common_tools:
        print(f"工具: {tool.name}")
        print(f"描述: {tool.description}")
        print("-" * 50) 