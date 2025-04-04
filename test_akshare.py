#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for AKShare tools
"""

try:
    import akshare as ak
    print("AKShare version:", ak.__version__)
    
    from llmcompiler.tools.basetool.akshare_tools import get_akshare_tools
    tools = get_akshare_tools()
    print(f"Successfully loaded {len(tools)} AKShare tools:")
    for tool in tools:
        print(f"- {tool.name}")
except Exception as e:
    print(f"Error: {str(e)}") 