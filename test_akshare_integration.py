#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AKShare集成测试 - 测试AKShare工具的各种功能
"""

import unittest
import pandas as pd
from pprint import pprint

# 导入AKShare工具
from llmcompiler.tools.basetool.akshare_tools import get_akshare_tools, get_akshare_tool_stats
from llmcompiler.tools.basetool.akshare_dynamic_tool import AKShareDynamicTool
from llmcompiler.tools.basetool.akshare_category_tools import (
    get_akshare_methods_by_category,
    get_common_akshare_methods,
    get_common_akshare_tools,
    get_akshare_category_tools
)


class TestAKShareIntegration(unittest.TestCase):
    """AKShare集成测试类"""
    
    def test_basic_tool_loading(self):
        """测试加载基本AKShare工具"""
        tools = get_akshare_tools(tool_mode="essential")
        self.assertGreaterEqual(len(tools), 3, "基本工具应该至少包含3个工具")
        tool_names = [tool.name for tool in tools]
        self.assertIn("akshare_stock_data", tool_names, "应包含股票数据工具")
        self.assertIn("akshare_fund_data", tool_names, "应包含基金数据工具")
        self.assertIn("akshare_macro_data", tool_names, "应包含宏观数据工具")
    
    def test_dynamic_tool(self):
        """测试动态AKShare工具"""
        dynamic_tool = AKShareDynamicTool()
        self.assertEqual(dynamic_tool.name, "akshare_dynamic_tool", "动态工具名称不正确")
        
        # 获取可用方法
        methods = dynamic_tool.get_available_methods()
        self.assertGreater(len(methods), 100, "AKShare应该提供超过100个方法")
        
        # 获取方法信息
        stock_info = dynamic_tool.get_method_info("stock_zh_a_hist")
        self.assertIn("parameters", stock_info, "方法信息应包含参数列表")
    
    def test_method_categorization(self):
        """测试方法分类"""
        categorized_methods = get_akshare_methods_by_category()
        
        # 检查是否所有分类都有方法
        for category, methods in categorized_methods.items():
            # 有些分类可能没有方法，但主要分类应该有
            if category in ["stock", "fund", "macro"]:
                self.assertGreater(len(methods), 0, f"{category} 分类应该有方法")
        
        # 检查常用方法
        common_methods = get_common_akshare_methods()
        self.assertGreater(len(common_methods), 10, "常用方法应该超过10个")
    
    def test_category_tools(self):
        """测试分类工具"""
        category_tools = get_akshare_category_tools()
        self.assertGreaterEqual(len(category_tools), 5, "分类工具应该至少有5个")
        
        # 检查是否包含主要分类
        tool_names = [tool.name for tool in category_tools]
        self.assertIn("akshare_stock_category", tool_names, "应包含股票分类工具")
        self.assertIn("akshare_fund_category", tool_names, "应包含基金分类工具")
    
    def test_common_tools(self):
        """测试常用工具"""
        common_tools = get_common_akshare_tools(max_tools=5)
        self.assertEqual(len(common_tools), 5, "应该生成5个常用工具")
    
    def test_full_tool_set(self):
        """测试完整工具集"""
        full_tools = get_akshare_tools(tool_mode="full")
        self.assertGreater(len(full_tools), 10, "完整工具集应该超过10个工具")
    
    def test_tool_stats(self):
        """测试工具统计"""
        stats = get_akshare_tool_stats()
        self.assertIn("total_methods", stats, "统计信息应包含方法总数")
        self.assertIn("category_counts", stats, "统计信息应包含分类计数")
        self.assertGreater(stats["total_methods"], 100, "AKShare应该提供超过100个方法")


def main():
    """主函数：运行所有测试或打印工具信息"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--info":
        # 打印工具信息
        print("\n=== AKShare工具统计 ===")
        stats = get_akshare_tool_stats()
        pprint(stats)
        
        print("\n=== 分类方法统计 ===")
        categories = get_akshare_methods_by_category()
        for category, methods in categories.items():
            print(f"{category}: {len(methods)} 个方法")
            if methods and len(methods) > 0:
                print(f"  示例: {methods[0]}")
        
        print("\n=== 常用方法 ===")
        common = get_common_akshare_methods()
        print(f"共 {len(common)} 个常用方法")
        print(common[:5])
    else:
        # 运行单元测试
        unittest.main()


if __name__ == "__main__":
    main() 