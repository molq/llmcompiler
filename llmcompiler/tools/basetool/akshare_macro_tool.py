# -*- coding: utf-8 -*-
"""
@Desc    : AKShare Macro Tool - Fetches macroeconomic indicators using AKShare
"""
import logging
import pandas as pd
from langchain_core.tools import BaseTool
from pydantic import Field, BaseModel
from typing import Type, List, Union, Tuple, Optional

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


class MacroInputSchema(BaseModel):
    indicator: str = Field(description="宏观经济指标类型，可选值：CPI, PPI, GDP, 货币供应量, 社会融资规模存量, 工业增加值, 社会消费品零售总额, PMI")
    start_date: str = Field(default="", description="开始日期，格式：YYYY-MM-DD")
    end_date: str = Field(default="", description="结束日期，格式：YYYY-MM-DD")
    region: str = Field(default="中国", description="国家或地区，默认为中国")


class AKShareMacroTool(BaseTool):
    name = "akshare_macro_data"
    description = render_text_description(
        "功能：获取宏观经济数据，如CPI、PPI、GDP等重要经济指标。"
        "输入参数：宏观经济指标类型（CPI, PPI, GDP, 货币供应量, 社会融资规模存量, 工业增加值, 社会消费品零售总额, PMI）；开始日期；结束日期；国家或地区。"
        "返回值：返回宏观经济指标的历史数据。"
    )
    args_schema: Type[BaseModel] = MacroInputSchema

    @tool_set_pydantic_default
    @tool_kwargs_filter
    def _run(self, **kwargs) -> ActionOutput:
        """Use the tool."""
        try:
            result = self.chart(**kwargs)
            tuple = action_output_charts_df_parse([result])
            charts = tuple[0]
            if charts:
                return ActionOutput(any=charts)
        except Exception as e:
            logging.error(str(e))
        return ActionOutputError(
            msg="无法获取宏观经济数据，请告知用户数据获取失败。")

    def chart(self, **kwargs) -> Tuple[Chart, pd.DataFrame]:
        indicator = kwargs.get("indicator", "")
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        region = kwargs.get("region", "中国")
        
        try:
            df = None
            title = f"{region}{indicator}数据"
            
            # Get macroeconomic data based on indicator type
            if indicator == "CPI":
                df = ak.macro_china_cpi_yearly() if region == "中国" else None
            elif indicator == "PPI":
                df = ak.macro_china_ppi_yearly() if region == "中国" else None
            elif indicator == "GDP":
                df = ak.macro_china_gdp_yearly() if region == "中国" else None
            elif indicator == "货币供应量":
                df = ak.macro_china_money_supply() if region == "中国" else None
            elif indicator == "社会融资规模存量":
                df = ak.macro_china_shrzgm() if region == "中国" else None
            elif indicator == "工业增加值":
                df = ak.macro_china_industrial_production_yearly() if region == "中国" else None
            elif indicator == "社会消费品零售总额":
                df = ak.macro_china_retail_sales_yearly() if region == "中国" else None
            elif indicator == "PMI":
                df = ak.macro_china_pmi_yearly() if region == "中国" else None
            else:
                raise ValueError(f"Unsupported indicator: {indicator}")
                
            # Filter by date if provided
            if start_date and end_date and df is not None:
                date_columns = [col for col in df.columns if '日期' in col or 'year' in col.lower()]
                if date_columns:
                    date_col = date_columns[0]
                    df[date_col] = pd.to_datetime(df[date_col])
                    df = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]
            
            if df is not None and not df.empty:
                columns = df.columns.values.tolist()
                result = {"labels": columns, "data": df.values.tolist()}
                return Chart(
                    type=ChartType.TABLE_WITH_HEADERS.value,
                    title=title,
                    data=result,
                    source=[Source(title="AKShare宏观经济数据", 
                                   content=f"{region}的{indicator}数据",
                                   url="https://akshare.akfamily.xyz/")],
                    labels=["宏观经济数据"]
                ), df
            else:
                raise ValueError(f"No data found for indicator: {indicator} in region: {region}")
        except Exception as e:
            logger.error(f"Error fetching macro data: {str(e)}")
            raise


if __name__ == '__main__':
    info = AKShareMacroTool()
    print(info.name)
    print(info.description)
    print(info.args)
    print(info._run(indicator="CPI", region="中国")) 