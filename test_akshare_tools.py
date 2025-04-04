#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Automated tests for AKShare tools
"""

import unittest
from llmcompiler.tools.basetool.akshare_stock_tool import AKShareStockTool
from llmcompiler.tools.basetool.akshare_fund_tool import AKShareFundTool
from llmcompiler.tools.basetool.akshare_macro_tool import AKShareMacroTool
from llmcompiler.tools.basetool.akshare_tools import get_akshare_tools
from llmcompiler.tools.generic.action_output import ActionOutput


class TestAKShareTools(unittest.TestCase):
    """Test cases for AKShare tools"""

    def test_tools_registry(self):
        """Test that all AKShare tools are properly registered"""
        tools = get_akshare_tools()
        self.assertGreaterEqual(len(tools), 3, "Should have at least 3 AKShare tools")
        tool_names = [tool.name for tool in tools]
        self.assertIn("akshare_stock_data", tool_names)
        self.assertIn("akshare_fund_data", tool_names)
        self.assertIn("akshare_macro_data", tool_names)

    def test_stock_tool_args(self):
        """Test that stock tool has correct arguments"""
        tool = AKShareStockTool()
        args = tool.args
        self.assertIn("symbol", args)
        self.assertIn("period", args)
        self.assertIn("start_date", args)
        self.assertIn("end_date", args)
        self.assertIn("adjust", args)

    def test_fund_tool_args(self):
        """Test that fund tool has correct arguments"""
        tool = AKShareFundTool()
        args = tool.args
        self.assertIn("symbol", args)
        self.assertIn("indicator", args)
        self.assertIn("start_date", args)
        self.assertIn("end_date", args)

    def test_macro_tool_args(self):
        """Test that macro tool has correct arguments"""
        tool = AKShareMacroTool()
        args = tool.args
        self.assertIn("indicator", args)
        self.assertIn("start_date", args)
        self.assertIn("end_date", args)
        self.assertIn("region", args)


if __name__ == "__main__":
    unittest.main() 