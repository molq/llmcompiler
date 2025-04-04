# -*- coding: utf-8 -*-
"""
@Author  : Yc-Ma
@Desc    : DeepSeek LLM Implementation
@Time    : 2024-08-02 09:30:49
"""
import inspect
import logging
from typing import Any, List, Optional, Tuple, Mapping, Dict

from langchain.callbacks.manager import CallbackManagerForLLMRun, Callbacks
from langchain.llms.base import LLM
from langchain.schema import LLMResult, Generation, PromptValue, SystemMessage, HumanMessage
from openai import OpenAI


class DeepSeekLLM(LLM):
    temperature: float = 0.0

    # 模型标记字段
    type: str = "deepseek-chat"
    # 定义模型名称
    model: str = "deepseek-chat"
    # 内部标记模型类别
    model_name: str = "deepseek-chat"

    # 提示词DEBUG模式
    debug: bool = False

    # 接口调用标签
    pl_tags: List = []
    # 接口重试次数
    max_retries: int = 3
    # 接口超时时间，默认300s
    timeout = 300
    # API KEY
    api_key: Optional[str] = None
    # 基础URL(可选)
    base_url: Optional[str] = None

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
        return self._generate(prompts, stop=stop, callbacks=callbacks, **kwargs)

    def _generate(
            self,
            prompts: List,
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> LLMResult:
        """运行LLM，处理给定的提示和输入。"""
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
        return self.api(prompt, stop=stop)

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """获取标识参数。"""
        return {"type": self.type, "model": self.model}

    def api(self, prompt: PromptValue, stop: Optional[List[str]] = None) -> str:
        """调用DeepSeek API。"""
        messages = self.pack(prompt)
        
        # 调试模式输出消息内容
        if self.debug:
            logging.info(f"DeepSeek API Messages: {messages}")
            
        client_params = {"api_key": self.api_key}
        if self.base_url:
            client_params["base_url"] = self.base_url
            
        client = OpenAI(**client_params)
        
        retries = 0
        result = None
        
        while retries < self.max_retries:
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    stop=stop,
                    timeout=self.timeout
                )
                response_content = response.choices[0].message.content
                
                # 添加大模型返回数据的日志记录
                logging.info(f"DeepSeek API Response: {response_content}")
                
                return response_content
            except Exception as e:
                retries += 1
                if retries == self.max_retries:
                    logging.error(f"API调用失败: {str(e)}")
                    return f"API请求在达到最大重试次数后失败: {str(e)}"
                else:
                    logging.debug(f"重试API请求... (第{retries}次)")
        
        return "API请求失败"

    def pack(self, prompt):
        messages = []
        if isinstance(prompt, list) and all(isinstance(m, (SystemMessage, HumanMessage)) for m in prompt):
            # 处理消息列表
            for me in prompt:
                if isinstance(me, SystemMessage):
                    data = {"role": "system", "content": me.content}
                elif isinstance(me, HumanMessage):
                    data = {"role": "user", "content": me.content}
                # ... 其他类型
                messages.append(data)
        elif hasattr(prompt, "to_messages"):
            # 处理 PromptValue 对象
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
                elif me.type == "function":
                    # 关键修改：将function角色转换为tool角色
                    # data = {
                    #     "role": "tool",
                    #     "content": me.content
                    # }
                    data = {
                        "role": "user",
                        "content": f"工具结果: {me.content}"
                    }
                elif me.type == "human":
                    data = {
                        "role": "user",
                        "content": me.content
                    }
                else:
                    # 处理其他类型的消息，如ChatMessage
                    role = me.type
                    # 如果角色是'function'，转换为'tool'
                    if role == "function":
                        role = "tool"
                    data = {
                        "role": role,
                        "content": me.content
                    }
                messages.append(data)
        else:
            # 处理字符串或其他类型
            data = {"role": "user", "content": str(prompt)}
            messages.append(data)
        return messages

    def debug_prompt(self, debug: bool):
        """设置调试模式。"""
        self.debug = debug