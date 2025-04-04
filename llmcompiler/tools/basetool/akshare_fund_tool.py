# -*- coding: utf-8 -*-
"""
@Desc    : AKShare Fund Tool - Fetches fund information using AKShare
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


class FundInfoInputSchema(BaseModel):
    symbol: str = Field(description="基金代码，例如：000001 或者 110011")
    indicator: str = Field(default="单位净值走势", description="指标类型，可选值：单位净值走势, 累计净值走势, 累计收益率走势, 同类排名走势, 同类排名百分比, 分红送配详情, 拆分详情")
    start_date: str = Field(default="", description="开始日期，格式：YYYY-MM-DD")
    end_date: str = Field(default="", description="结束日期，格式：YYYY-MM-DD")


class AKShareFundTool(BaseTool):
    name = "akshare_fund_data"
    description = render_text_description(
        "功能：获取基金详细数据，包括净值、收益率、排名等信息。"
        "输入参数：基金代码；指标类型（单位净值走势, 累计净值走势, 累计收益率走势, 同类排名走势, 同类排名百分比, 分红送配详情, 拆分详情）；开始日期；结束日期。"
        "返回值：返回基金的历史数据，数据内容根据选择的指标类型有所不同。"
    )
    args_schema: Type[BaseModel] = FundInfoInputSchema

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
            msg="无法获取基金数据，请告知用户数据获取失败，并建议检查基金代码是否正确。")

    def chart(self, **kwargs) -> Tuple[Chart, pd.DataFrame]:
        symbol = kwargs.get("symbol", "")
        indicator = kwargs.get("indicator", "单位净值走势")
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        
        try:
            # Map indicator to AKShare function parameters
            indicator_map = {
                "单位净值走势": "单位净值走势",
                "累计净值走势": "累计净值走势",
                "累计收益率走势": "累计收益率走势",
                "同类排名走势": "同类排名走势",
                "同类排名百分比": "同类排名百分比",
                "分红送配详情": "分红送配详情",
                "拆分详情": "拆分详情"
            }
            
            ak_indicator = indicator_map.get(indicator, "单位净值走势")
            
            # Get fund data using AKShare
            df = ak.fund_em_open_fund_info(fund=symbol, indicator=ak_indicator)
            
            # Filter by date if provided
            if start_date and end_date and '净值日期' in df.columns:
                df['净值日期'] = pd.to_datetime(df['净值日期'])
                df = df[(df['净值日期'] >= start_date) & (df['净值日期'] <= end_date)]
            
            if not df.empty:
                columns = df.columns.values.tolist()
                result = {"labels": columns, "data": df.values.tolist()}
                return Chart(
                    type=ChartType.TABLE_WITH_HEADERS.value,
                    title=f"基金 {symbol} {indicator}数据",
                    data=result,
                    source=[Source(title="AKShare基金数据", 
                                  content=f"基金 {symbol} 的{indicator}数据",
                                  url="https://akshare.akfamily.xyz/")],
                    labels=["基金历史数据"]
                ), df
            else:
                raise ValueError(f"No data found for fund: {symbol}")
        except Exception as e:
            logger.error(f"Error fetching fund data: {str(e)}")
            raise


if __name__ == '__main__':
    info = AKShareFundTool()
    print(info.name)
    print(info.description)
    print(info.args)
    print(info._run(symbol="000001", indicator="单位净值走势", start_date="2023-01-01", end_date="2023-01-10")) 