import asyncio
import json
from contextlib import AsyncExitStack
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client
from openai import AsyncOpenAI

load_dotenv()

# Get OpenAI API key from environment and set it
openai_api_key = os.getenv('OPENAI_API_KEY')

class MCPOpenAIClient:
    """Client for interacting with OpenAI models using MCP tools."""

    def __init__(self, model: str = "gpt-4o"):
        self.session: Optional[ClientSession] = None
        self.openai_client = AsyncOpenAI()
        self.model = model
        self.exit_stack = AsyncExitStack()
        self.host = os.getenv('MCP_HOST')
        self.port = os.getenv('MCP_PORT')
        self.stdio: Optional[Any] = None
        self.write: Optional[Any] = None

    async def connect_to_server(self):
        """Connect to the MCP server via SSE."""
        if self.exit_stack is not None:
            await self.cleanup()
        self.exit_stack = AsyncExitStack()
        
        try:
            sse_transport = await self.exit_stack.enter_async_context(
                sse_client(f"http://{self.host}:{self.port}/sse")
            )
            self.stdio, self.write = sse_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )
            
            await self.session.initialize()
            
        except Exception as e:
            await self.cleanup()
            raise e


    async def get_mcp_tools(self) -> List[Dict[str, Any]]:
        tools_result = await self.session.list_tools()
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

    async def process_query(self, query: str) -> str:
        tools = await self.get_mcp_tools()

        response = await self.openai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": query}],
            tools=tools,
            tool_choice="auto",
        )

        llm_message = response.choices[0].message

        messages = [
            {"role": "user", "content": query},
            llm_message,
        ]

        if llm_message.tool_calls:
            for tool_call in llm_message.tool_calls:
                result = await self.session.call_tool(
                    tool_call.function.name,
                    arguments=json.loads(tool_call.function.arguments),
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result.content[0].text,
                    }
                )

            final_response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="none",
            )

            return final_response.choices[0].message.content

        return llm_message.content

    async def cleanup(self):
        """Clean up resources."""
        if self.exit_stack:
            try:
                await asyncio.sleep(0.1)
                await self.exit_stack.aclose()
            except Exception as e:
                print(f"Warning: Error during cleanup: {e}")
            finally:
                self.exit_stack = None
                self.session = None
                self.stdio = None
                self.write = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()


async def main():
    async with MCPOpenAIClient() as client:
        try:
            await client.connect_to_server()
            print("Connected to MCP server successfully!")

            access_token = input('Please enter your access token: ')
            file_id = input('Please enter your file id: ')
            query = f"get the summary \n\nFile id: {file_id}\n\nAccess Token: {access_token}"

            response = await client.process_query(query)
            print(f"\nResponse: {response}")
            
        except Exception as e:
            print(f"Error: {e}")
        

if __name__ == "__main__":
    asyncio.run(main())