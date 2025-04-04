# -*- coding: utf-8 -*-
"""
@Desc    : AKShare Dynamic Tool - 支持动态调用AKShare的所有方法
"""
import inspect
import logging
import pandas as pd
from langchain_core.tools import BaseTool
from pydantic import Field, BaseModel, create_model
from typing import Type, List, Dict, Any, Callable, Optional, Tuple, Union
import warnings
from typing import cast, ClassVar

from llmcompiler.tools.configure.tool_decorator import tool_kwargs_filter, tool_set_pydantic_default
from llmcompiler.tools.generic.action_output import ChartType, Chart, \
    action_output_charts_df_parse, Source
from llmcompiler.tools.generic.action_output import ActionOutput, ActionOutputError
from llmcompiler.tools.generic.render_description import render_text_description

logger = logging.getLogger(__name__)

try:
    import akshare as ak
except ImportError:
    raise ImportError(
        "The 'akshare' package is required to use this class. Please install it using 'pip install akshare'.")


# 定义AKShare函数的分类
AKSHARE_CATEGORIES = {
    "stock": "股票数据",
    "fund": "基金数据",
    "bond": "债券数据",
    "macro": "宏观经济数据",
    "fx": "外汇数据",
    "option": "期权数据",
    "future": "期货数据",
    "index": "指数数据",
    "crypto": "加密货币数据",
    "others": "其他数据"
}


class AKShareDynamicInputSchema(BaseModel):
    """AKShare动态工具的基础输入模式"""
    method_name: str = Field(description="要调用的AKShare方法名称，例如：stock_zh_a_hist")
    params: dict = Field(default={}, description="传递给AKShare方法的参数，格式为JSON对象")


class AKShareDynamicTool(BaseTool):
    """
    AKShare动态工具 - 可以调用AKShare的任何方法
    """
    name = "akshare_dynamic_tool"
    description = render_text_description(
        "功能：调用AKShare的任何方法获取金融数据。"
        "输入参数：method_name - AKShare方法名；params - 传递给方法的参数。"
        "返回值：根据调用的AKShare方法返回相应的数据。"
        "可用方法示例：stock_zh_a_hist（A股历史行情）, fund_em_open_fund_info（基金信息）, "
        "bond_zh_hs_cov_daily（可转债行情）, macro_china_cpi_yearly（CPI年度数据）, "
        "fx_spot_quote（外汇报价）等。"
    )
    args_schema: Type[BaseModel] = AKShareDynamicInputSchema
    
    @tool_set_pydantic_default
    @tool_kwargs_filter
    def _run(self, **kwargs) -> ActionOutput:
        """运行AKShare动态工具"""
        try:
            method_name = kwargs.get("method_name", "")
            params = kwargs.get("params", {})
            
            if not method_name:
                return ActionOutputError(msg="未提供AKShare方法名")
            
            result = self.execute_akshare_method(method_name, params)
            if isinstance(result, tuple) and len(result) == 2:
                chart, df = result
                tuple_result = action_output_charts_df_parse([(chart, df)])
                charts = tuple_result[0]
                if charts:
                    return ActionOutput(any=charts)
            
            return ActionOutputError(msg=f"调用AKShare方法 {method_name} 未返回有效数据")
        except Exception as e:
            logging.error(str(e))
            return ActionOutputError(msg=f"调用AKShare方法失败: {str(e)}")
    
    def execute_akshare_method(self, method_name: str, params: Dict[str, Any]) -> Tuple[Chart, pd.DataFrame]:
        """
        执行指定的AKShare方法
        
        Args:
            method_name: AKShare方法名
            params: 传递给方法的参数
            
        Returns:
            图表和数据框的元组
        """
        if not hasattr(ak, method_name):
            raise ValueError(f"AKShare没有名为 {method_name} 的方法")
        
        # 获取方法对象
        method = getattr(ak, method_name)
        
        # 调用AKShare方法
        try:
            df = method(**params)
            
            # 确保结果是DataFrame
            if not isinstance(df, pd.DataFrame):
                if isinstance(df, (list, tuple)) and len(df) > 0 and isinstance(df[0], pd.DataFrame):
                    df = df[0]  # 有些AKShare方法返回DataFrame列表
                else:
                    raise ValueError(f"AKShare方法 {method_name} 没有返回DataFrame")
            
            if not df.empty:
                columns = df.columns.values.tolist()
                result = {"labels": columns, "data": df.values.tolist()}
                
                # 创建图表
                return Chart(
                    type=ChartType.TABLE_WITH_HEADERS.value,
                    title=f"AKShare {method_name} 数据",
                    data=result,
                    source=[Source(
                        title="AKShare数据",
                        content=f"使用AKShare的 {method_name} 方法获取的数据",
                        url="https://akshare.akfamily.xyz/"
                    )],
                    labels=[f"AKShare {method_name} 数据"]
                ), df
            else:
                raise ValueError(f"AKShare方法 {method_name} 返回的DataFrame为空")
        except Exception as e:
            logger.error(f"执行AKShare方法 {method_name} 出错: {str(e)}")
            raise
    
    @staticmethod
    def get_available_methods() -> List[str]:
        """
        获取AKShare提供的所有可用方法名称
        
        Returns:
            可用方法名称列表
        """
        return [name for name, obj in inspect.getmembers(ak)
                if inspect.isfunction(obj) and not name.startswith('_')]
    
    @staticmethod
    def get_method_info(method_name: str) -> Dict[str, Any]:
        """
        获取指定AKShare方法的详细信息
        
        Args:
            method_name: 方法名称
            
        Returns:
            包含方法信息的字典
        """
        if not hasattr(ak, method_name):
            return {"error": f"方法 {method_name} 不存在"}
        
        method = getattr(ak, method_name)
        if not inspect.isfunction(method):
            return {"error": f"{method_name} 不是一个函数"}
        
        sig = inspect.signature(method)
        
        return {
            "name": method_name,
            "doc": inspect.getdoc(method) or "无文档",
            "parameters": {
                name: {
                    "annotation": str(param.annotation) if param.annotation != param.empty else "未知",
                    "default": str(param.default) if param.default != param.empty else "必填",
                }
                for name, param in sig.parameters.items()
            }
        }


class AKShareMethodToolSchema(BaseModel):
    """AKShare方法工具输入模式基类"""
    method_name: str = Field(description="AKShare方法名称")


class SubclassedBaseTool(BaseTool):
    """一个不进行Pydantic校验的基础工具类"""
    
    _no_validation_error_message = "Error binding arguments: "
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        super().__init__()


class AKShareMethodTool(BaseTool):
    """
    AKShare方法工具 - 针对特定AKShare方法生成的工具
    """
    name: str = ""
    description: str = ""
    args_schema: Optional[Type[BaseModel]] = None
    
    def __init__(self, method_name: str):
        """
        初始化AKShare方法工具
        
        Args:
            method_name: AKShare方法名称
        """
        # 确认方法存在
        if not hasattr(ak, method_name):
            raise ValueError(f"AKShare没有名为 {method_name} 的方法")
        
        # 获取方法对象和信息
        method = getattr(ak, method_name)
        method_info = AKShareDynamicTool.get_method_info(method_name)
        method_doc = method_info.get("doc", "")
        
        # 生成方法描述
        description_lines = []
        method_desc = method_doc.split("\n")[0] if method_doc else f"调用AKShare {method_name}方法获取数据"
        description_lines.append(f"功能：{method_desc}")
        description_lines.append(f"返回：调用AKShare {method_name}方法获取的数据")
        
        # 获取参数信息
        params_info = method_info.get("parameters", {})
        if params_info:
            description_lines.append("参数：")
            for param_name, param_info in params_info.items():
                param_default = param_info.get("default", "必填")
                param_desc = f"{param_name} - {param_default}"
                description_lines.append(f"  - {param_desc}")
        
        # 设置属性
        self.name = f"akshare_method_{method_name}"
        self.description = "\n".join(description_lines)
        self._method = method
        self._method_name = method_name
        self._params_info = params_info
        
        # 初始化基类
        super().__init__()
    
    def _run(self, **kwargs) -> dict:
        """
        运行AKShare方法
        
        Args:
            **kwargs: 传递给AKShare方法的参数
            
        Returns:
            格式化后的方法执行结果
        """
        try:
            # 调用AKShare方法
            result = self._method(**kwargs)
            
            # 确保结果是DataFrame
            if not isinstance(result, pd.DataFrame):
                if isinstance(result, (list, tuple)) and len(result) > 0 and isinstance(result[0], pd.DataFrame):
                    result = result[0]  # 有些AKShare方法返回DataFrame列表
                else:
                    return {"error": f"AKShare方法 {self._method_name} 没有返回DataFrame"}
            
            if not result.empty:
                # 格式化输出结果
                return {
                    "method": self._method_name,
                    "data_shape": result.shape,
                    "columns": result.columns.tolist(),
                    "data": result.head(10).to_dict(orient="records"),  # 仅返回前10行数据
                    "total_rows": len(result)
                }
            else:
                return {"error": f"AKShare方法 {self._method_name} 返回的DataFrame为空"}
        except Exception as e:
            logger.error(f"执行AKShare方法 {self._method_name} 出错: {str(e)}")
            return {"error": str(e)}
    
    async def _arun(self, **kwargs):
        """异步执行AKShare方法"""
        return self._run(**kwargs)


def create_akshare_tool_for_method(method_name: str) -> Optional[BaseTool]:
    """
    为指定的AKShare方法创建工具
    
    Args:
        method_name: AKShare方法名
        
    Returns:
        创建的工具实例，如果方法不存在则返回None
    """
    if not hasattr(ak, method_name):
        logger.error(f"AKShare没有名为 {method_name} 的方法")
        return None
    
    try:
        # 获取方法对象和信息
        akshare_method = getattr(ak, method_name)
        method_info = AKShareDynamicTool.get_method_info(method_name)
        method_doc = method_info.get("doc", "")
        
        # 生成方法描述
        description_lines = []
        method_desc = method_doc.split("\n")[0] if method_doc else f"调用AKShare {method_name}方法获取数据"
        description_lines.append(f"功能：{method_desc}")
        description_lines.append(f"返回：调用AKShare {method_name}方法获取的数据")
        
        # 获取参数信息
        params_info = method_info.get("parameters", {})
        if params_info:
            description_lines.append("参数：")
            for param_name, param_info in params_info.items():
                param_default = param_info.get("default", "必填")
                param_desc = f"{param_name} - {param_default}"
                description_lines.append(f"  - {param_desc}")
                
        # 创建专门的工具类
        class AKShareMethodToolForMethod(BaseTool):
            name = f"akshare_method_{method_name}"
            description = "\n".join(description_lines)
            
            def _run(self, **kwargs) -> dict:
                """
                运行AKShare方法
                
                Args:
                    **kwargs: 传递给AKShare方法的参数
                    
                Returns:
                    格式化后的方法执行结果
                """
                try:
                    # 调用AKShare方法
                    result = akshare_method(**kwargs)
                    
                    # 确保结果是DataFrame
                    if not isinstance(result, pd.DataFrame):
                        if isinstance(result, (list, tuple)) and len(result) > 0 and isinstance(result[0], pd.DataFrame):
                            result = result[0]  # 有些AKShare方法返回DataFrame列表
                        else:
                            return {"error": f"AKShare方法 {method_name} 没有返回DataFrame"}
                    
                    if not result.empty:
                        # 格式化输出结果
                        return {
                            "method": method_name,
                            "data_shape": result.shape,
                            "columns": result.columns.tolist(),
                            "data": result.head(10).to_dict(orient="records"),  # 仅返回前10行数据
                            "total_rows": len(result)
                        }
                    else:
                        return {"error": f"AKShare方法 {method_name} 返回的DataFrame为空"}
                except Exception as e:
                    logger.error(f"执行AKShare方法 {method_name} 出错: {str(e)}")
                    return {"error": str(e)}
            
            async def _arun(self, **kwargs):
                """异步执行AKShare方法"""
                return self._run(**kwargs)
        
        # 创建并返回工具实例
        return AKShareMethodToolForMethod()
        
    except Exception as e:
        logger.error(f"为方法 {method_name} 创建工具时出错: {str(e)}")
        return None


if __name__ == '__main__':
    # 测试动态工具
    dynamic_tool = AKShareDynamicTool()
    print(f"动态工具名称: {dynamic_tool.name}")
    print(f"动态工具描述: {dynamic_tool.description}")
    
    # 获取所有可用方法
    methods = dynamic_tool.get_available_methods()
    print(f"AKShare提供了 {len(methods)} 个方法")
    print(f"前10个方法: {methods[:10]}")
    
    # 获取特定方法信息
    method_info = dynamic_tool.get_method_info("stock_zh_a_hist")
    print(f"方法信息: {method_info}")
    
    # 测试为特定方法创建工具
    stock_tool = create_akshare_tool_for_method("stock_zh_a_hist")
    if stock_tool:
        print(f"创建的工具名称: {stock_tool.name}")
        print(f"创建的工具描述: {stock_tool.description}") 