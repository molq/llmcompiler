# -*- coding: utf-8 -*-
"""
@Author  : Yc-Ma
@Desc    : LLMCompiler
@Time    : 2024-08-02 09:30:49
"""
import inspect
import logging
from typing import Any, List, Optional, Tuple

from langchain.callbacks.manager import CallbackManagerForLLMRun, Callbacks
from langchain.llms.base import LLM
from langchain.schema import LLMResult, Generation, PromptValue


class Claude3LLM(LLM):
    # 温度值
    temperature: float = 0.0
    # 定义模型名称【使用Claude3哪个模型】anthropic.claude-3-sonnet-20240229-v1:0
    model: str = "anthropic.claude-3-haiku-20240307-v1:0"
    # 接口重试次数
    max_retries: int = 3
    # 接口超时时间，默认300s
    timeout = 300
    # 接口调用标签
    pl_tags: List = []
    # 提示词DEBUG模式
    debug: bool = False

    @property
    def _llm_type(self) -> str:
        return self.model

    def generate_prompt(
            self,
            prompts: List[PromptValue],
            stop: Optional[List[str]] = None,
            callbacks: Callbacks = None,
            **kwargs: Any,
    ) -> LLMResult:
        # prompt_strings = [p.to_string() for p in prompts]
        return self._generate(prompts, stop=stop, callbacks=callbacks, **kwargs)

    def _generate(
            self,
            prompts: List,
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> LLMResult:
        """Run the LLM on the given prompt and input."""
        # TODO: add caching here.
        generations = []
        new_arg_supported = inspect.signature(self._call).parameters.get("run_manager")

        for prompt in prompts:
            text = (
                self._call(prompt, stop=stop, run_manager=run_manager, **kwargs)
                if new_arg_supported
                else self._call(prompt, stop=stop, **kwargs)
            )
            generations.append([Generation(text=text)])
        return LLMResult(generations=generations)

    def _call(
            self,
            prompt: PromptValue,
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs
    ) -> str:
        # if stop is not None:
        #     raise ValueError("stop kwargs are not permitted.")
        return self.api(prompt)

    def api(self, prompt: PromptValue):
        """调用Claude API获取响应"""
        messages, system = self.pack(prompt)
        
        # 调试模式输出请求消息
        if self.debug:
            logging.info(f"Claude API Messages: {messages}")
            if system:
                logging.info(f"Claude API System: {system}")
        
        retries = 0
        
        # 添加Claude API的实际调用
        import anthropic
        client = anthropic.Anthropic()
        
        while retries < self.max_retries:
            try:
                # 构建Claude请求
                if system:
                    response = client.messages.create(
                        model=self.model,
                        system=system,
                        messages=messages,
                        temperature=self.temperature,
                        max_tokens=4096
                    )
                else:
                    response = client.messages.create(
                        model=self.model,
                        messages=messages,
                        temperature=self.temperature,
                        max_tokens=4096
                    )
                
                response_content = response.content[0].text
                
                # 添加大模型返回数据的日志记录
                logging.info(f"Claude API Response: {response_content}")
                
                return response_content
            except Exception as e:
                retries += 1
                if retries == self.max_retries:
                    logging.error(f"Claude API调用失败: {str(e)}")
                    return f"API请求在达到最大重试次数后失败: {str(e)}"
                else:
                    logging.debug(f"重试Claude API请求... (第{retries}次)")
        
        return "Claude API请求失败"
    
    def pack(self, prompt: PromptValue) -> Tuple[List, Optional[str]]:
        """将提示转换为Claude API格式的消息和系统提示"""
        messages = []
        system = None
        
        if hasattr(prompt, "to_messages"):
            mes = prompt.to_messages()
            for me in mes:
                if me.type == "system":
                    system = me.content
                elif me.type == "ai":
                    messages.append({"role": "assistant", "content": me.content})
                elif me.type == "human":
                    messages.append({"role": "user", "content": me.content})
                elif me.type == "function":
                    # 将工具/函数响应转为用户消息
                    messages.append({"role": "user", "content": f"工具结果: {me.content}"})
                else:
                    # 默认作为用户消息
                    messages.append({"role": "user", "content": me.content})
        else:
            # 处理字符串提示
            messages.append({"role": "user", "content": str(prompt)})
        
        return messages, system

    def debug_prompt(self, debug: bool):
        self.debug = debug
