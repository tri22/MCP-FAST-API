import asyncio
import json
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI
from typing import Any, Dict, List

session = None
openai_client = AsyncOpenAI()
model = "gpt-4o"
reader = None
writer = None


async def connect_to_server():
    global session, reader, writer

    async with AsyncExitStack() as exit_stack:
        # Khởi động server qua stdio
        server_params = StdioServerParameters(command="python", args=["server.py"])
        stdio_transport = await exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        reader, writer = stdio_transport

        # Tạo session
        session = await exit_stack.enter_async_context(ClientSession(reader, writer))

        # Initialize kết nối
        await session.initialize()

        print("Connected to MCP server")


async def get_mcp_tools() -> List[Dict[str, Any]]:
    global session

    tools_result = await session.list_tools()
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            },
        }
        for tool in tools_result.tools
    ]


async def process_query(query: str) -> str:
    tool_list = await get_mcp_tools()

    # Initial OpenAI API call
    response = await openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": query}],
        tools=tool_list,
        tool_choice="auto",
    )

    

    """
{
    "role": "assistant",
    "content": null,   // không có text trực tiếp
    "tool_calls": [
        {
            "id": "call_1",   // id duy nhất cho lần gọi tool
            "type": "function",
            "function": {
                "name": "add",   // tên tool mà model muốn gọi
                "arguments": "{ \"a\": 2, \"b\": 3 }"  // tham số (JSON string)
            }
        }
    ]
}

    """

    """
        result 
        {
          "content": [
            {
              "type": "text",
              "text": "5"
            }
          ]
        }
    """

    # Get assistant's response
    assistant_message = response.choices[0].message

    # Initialize conversation with user query and assistant response
    messages = [
        {"role": "user", "content": query},
        assistant_message,
    ]

    # Handle tool calls if present
    if assistant_message.tool_calls:
        if assistant_message.tool_calls in tool_list:
            for tool_called in assistant_message.tool_calls:
                result = await session.call_tool(
                    tool=tool_called,
                    arguments=json.loads(tool_called.function.arguments),
                )

                # Add tool response to conversation
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_called.id,
                        "content": result.content[0].text,
                    }
                )

        final_response = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tool_list,
            tool_choice="none"
        )

        return final_response.choices[0].message.content
    
    # No tool calls, just return the direct response
    return assistant_message.content


async def cleanup():
    """Clean up resources."""
    global exit_stack
    await exit_stack.aclose()

async def main():
    # connect to server
    await connect_to_server()

    # query = {"a": 7, "b": 5}
    # print(f"\nQuery: {query}")

    # response = await process_query(query)
    # print(f"\nResponse: {response}")

    await cleanup()


if __name__ == "__main__":
    asyncio.run(main())
