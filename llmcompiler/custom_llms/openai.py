# -*- coding: utf-8 -*-
"""
@Author  : Yc-Ma
@Desc    : LLMCompiler
@Time    : 2024-08-02 09:30:49
"""
import inspect
import logging
from typing import Any, List, Optional, Tuple, Mapping

from langchain.callbacks.manager import CallbackManagerForLLMRun, Callbacks
from langchain.llms.base import LLM
from langchain.schema import LLMResult, Generation, PromptValue


class OpenaiLLM(LLM):
    temperature: float = 0.0

    # 模型标记字段
    type: str = "jsfund-gpt-3.5-turbo"
    # 定义模型名称【使用openai哪个模型】
    model: str = "gpt-3.5-turbo"
    # 内部标记模型类别
    model_name: str = "jsfund-gpt-3.5-turbo"

    # 提示词DEBUG模式
    debug: bool = False

    # 接口调用标签
    pl_tags: List = []
    # 接口重试次数
    max_retries: int = 3
    # 接口超时时间，默认300s
    timeout = 300

    @property
    def _llm_type(self) -> str:
        return self.type

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

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {"type": self.type}

    def api(self, prompt: PromptValue):
        """调用OpenAI API获取响应"""
        messages = self.pack(prompt)
        
        # 调试模式输出请求消息
        if self.debug:
            logging.info(f"OpenAI API Messages: {messages}")
        
        retries = 0
        
        # 从此处开始添加OpenAI API的实际调用
        import openai
        client = openai.OpenAI()
        
        while retries < self.max_retries:
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    timeout=self.timeout
                )
                response_content = response.choices[0].message.content
                
                # 添加大模型返回数据的日志记录
                logging.info(f"OpenAI API Response: {response_content}")
                
                return response_content
            except Exception as e:
                retries += 1
                if retries == self.max_retries:
                    logging.error(f"OpenAI API调用失败: {str(e)}")
                    return f"API请求在达到最大重试次数后失败: {str(e)}"
                else:
                    logging.debug(f"重试OpenAI API请求... (第{retries}次)")
        
        return "OpenAI API请求失败"

    def pack(self, prompt: PromptValue) -> List:
        messages = []
        if type(prompt) != str:
            mes = prompt.to_messages()
            for me in mes:
                if me.type == "system":
                    data = {
                        "role": "system",
                        "content": me.content
                    }
                elif me.type == "ai":
                    data = {
                        "role": "assistant",
                        "content": me.content
                    }
                else:
                    data = {
                        "role": "user",
                        "content": me.content
                    }

                messages.append(data)
        else:
            data = {
                "role": "user",
                "content": prompt
            }
            messages.append(data)
        return messages

    def debug_prompt(self, debug: bool):
        self.debug = debug
