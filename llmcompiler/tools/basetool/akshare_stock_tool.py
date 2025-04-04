# -*- coding: utf-8 -*-
"""
@Desc    : AKShare Stock Tool - Fetches stock information using AKShare
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


class StockInfoInputSchema(BaseModel):
    symbol: str = Field(description="股票代码，例如：000001 或 sh000001")
    period: str = Field(default="daily", description="K线周期，可选值：daily, weekly, monthly")
    start_date: str = Field(default="", description="开始日期，格式：YYYY-MM-DD")
    end_date: str = Field(default="", description="结束日期，格式：YYYY-MM-DD")
    adjust: str = Field(default="qfq", description="复权类型，可选值：qfq前复权, hfq后复权, 空字符串不复权")


class AKShareStockTool(BaseTool):
    name = "akshare_stock_data"
    description = render_text_description(
        "功能：获取A股股票的历史行情数据，包括日K、周K、月K。"
        "输入参数：股票代码(如000001或sh000001)；K线周期(daily, weekly, monthly)；开始日期；结束日期；复权类型(qfq, hfq, '')。"
        "返回值：返回股票历史行情数据，包括日期、开盘价、最高价、最低价、收盘价、成交量等信息。"
    )
    args_schema: Type[BaseModel] = StockInfoInputSchema

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
            msg="无法获取股票数据，请告知用户数据获取失败，并建议检查股票代码是否正确。")

    def chart(self, **kwargs) -> Tuple[Chart, pd.DataFrame]:
        symbol = kwargs.get("symbol", "")
        period = kwargs.get("period", "daily")
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        adjust = kwargs.get("adjust", "qfq")
        
        try:
            # Stock data for A-shares using AKShare
            if symbol.startswith(('sh', 'sz', 'bj')):
                # Symbol already has prefix
                market_code = symbol
            else:
                # Add market prefix by determining exchange
                if symbol.startswith('6'):
                    market_code = f"sh{symbol}"
                elif symbol.startswith(('0', '3')):
                    market_code = f"sz{symbol}"
                elif symbol.startswith('8'):
                    market_code = f"bj{symbol}"
                else:
                    market_code = symbol  # Use as is

            if period == "daily":
                df = ak.stock_zh_a_hist(symbol=market_code, period="daily", start_date=start_date, 
                                         end_date=end_date, adjust=adjust)
            elif period == "weekly":
                df = ak.stock_zh_a_hist(symbol=market_code, period="weekly", start_date=start_date, 
                                         end_date=end_date, adjust=adjust)
            elif period == "monthly":
                df = ak.stock_zh_a_hist(symbol=market_code, period="monthly", start_date=start_date, 
                                         end_date=end_date, adjust=adjust)
            else:
                raise ValueError(f"Unsupported period: {period}")
                
            if not df.empty:
                columns = df.columns.values.tolist()
                result = {"labels": columns, "data": df.values.tolist()}
                return Chart(
                    type=ChartType.TABLE_WITH_HEADERS.value,
                    title=f"股票 {symbol} 历史行情数据",
                    data=result,
                    source=[Source(title="AKShare股票行情", 
                                   content=f"股票 {symbol} 的{period}行情数据",
                                   url="https://akshare.akfamily.xyz/")],
                    labels=["股票历史行情数据"]
                ), df
            else:
                raise ValueError(f"No data found for symbol: {symbol}")
        except Exception as e:
            logger.error(f"Error fetching stock data: {str(e)}")
            raise


if __name__ == '__main__':
    info = AKShareStockTool()
    print(info.name)
    print(info.description)
    print(info.args)
    print(info._run(symbol="000001", period="daily", start_date="2023-01-01", end_date="2023-01-10")) 