import asyncio
import os
import sys
import json

from openai import OpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.settings import get_settings


async def main():
    settings = get_settings() 
    client = OpenAI(
        api_key=settings.interactive_api_key,
        base_url=settings.interactive_base_url,
    )
    
    completion = client.chat.completions.create(
        model = "moonshot-v1-8k",
        messages = [
            {"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"},
            {"role": "user", "content": "what is the temperature in paries。"}
        ],
        # tools = [{
        #     "type": "function",
        #     "function": {
        #         "name": "CodeRunner",
        #         "description": "代码执行器，支持运行 python 和 javascript 代码",
        #         "parameters": {
        #             "properties": {
        #                 "language": {
        #                     "type": "string",
        #                     "enum": ["python", "javascript"]
        #                 },
        #                 "code": {
        #                     "type": "string",
        #                     "description": "代码写在这里"
        #                 }
        #             },
        #         "type": "object"
        #         }
        #     }
        # }],
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_temperature",
                    "description": "Get the current temperature in a given location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                                "default": "fahrenheit"
                            }
                        },
                        "required": ["location"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_ceiling",
                    "description": "Get the current cloud ceiling in a given location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ],
        temperature = 0.3,
        stream = True
    )
    
    response_data = {
            "content": "",
            "reasoning_content": "",
            "is_tool": False,
            "tool_calls": [],
            "total_tokens": 0,
    }

    tool_call_buffer = {}  # 用于累加工具调用的参数
    for chunk in completion:
        choices = chunk.choices[0]
        delta = choices.delta

        # 处理 reasoning_content
        # if is_reasoning and delta.reasoning_content is not None:
        #     response_data["reasoning_content"] += delta.reasoning_content
        #     print(delta.reasoning_content, end="", flush=True)

        # 处理 content
        if delta.content is not None:
            response_data["content"] += delta.content
            print(delta.content, end="", flush=True)

        # 处理工具调用
        if delta.tool_calls:
            for tool_call in delta.tool_calls:
                index = tool_call.index
                if index not in tool_call_buffer:
                    tool_call_buffer[index] = {
                        "id": tool_call.id,
                        "function": {"name": "", "arguments": ""},
                    }

                # 累加工具调用信息
                if tool_call.id:
                    tool_call_buffer[index]["id"] = tool_call.id
                if tool_call.function:
                    if tool_call.function.name:
                        tool_call_buffer[index]["function"]["name"] = (
                            tool_call.function.name
                        )
                    if tool_call.function.arguments is not None:
                        tool_call_buffer[index]["function"]["arguments"] += (
                            tool_call.function.arguments
                        )

        # 处理 usage（如果 chunk 包含 usage 信息）
        if chunk.usage and chunk.usage.total_tokens:
            response_data["total_tokens"] = chunk.usage.total_tokens

    # 解析工具调用参数
    for _, tool_call in tool_call_buffer.items():
        try:
            # 将 arguments 字符串解析为 JSON
            tool_call["function"]["arguments"] = json.loads(
                tool_call["function"]["arguments"]
            )
            response_data["tool_calls"].append(tool_call)
        except json.JSONDecodeError:
            # 如果解析失败，保留原始字符串
            response_data["tool_calls"].append(tool_call)
    response_data["is_tool"] = len(response_data["tool_calls"]) > 0
    print("response_data", response_data)
    # completion_dict = {
    #     "id": completion.id,
    #     "created": completion.created,
    #     "model": completion.model,
    #     "choices": [{
    #         "finish_reason": choice.finish_reason,
    #         "index": choice.index,
    #         "message": {
    #             "content": choice.message.content,
    #             "role": choice.message.role,
    #             "tool_calls": [{
    #                 "id": tool_call.id,
    #                 "type": tool_call.type,
    #                 "function": {
    #                     "name": tool_call.function.name,
    #                     "arguments": json.loads(tool_call.function.arguments)
    #                 }
    #             } for tool_call in choice.message.tool_calls] if choice.message.tool_calls else None
    #         }
    #     } for choice in completion.choices],
    #     "usage": {
    #         "completion_tokens": completion.usage.completion_tokens,
    #         "prompt_tokens": completion.usage.prompt_tokens,
    #         "total_tokens": completion.usage.total_tokens
    #     }
    # }
    # print(json.dumps(completion_dict, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
