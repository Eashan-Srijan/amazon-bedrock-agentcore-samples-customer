from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

stdio_mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx", args=["awslabs.aws-documentation-mcp-server@latest"]
        )
    )
)

stdio_mcp_client.start()


system_prompt = """You are an AWS Documentation Assistant powered by the AWS Documentation MCP server. Your role is to help users find accurate, up-to-date information from AWS documentation.

Key capabilities:
- Search and retrieve information from AWS service documentation
- Provide clear, accurate answers about AWS services, features, and best practices
- Help users understand AWS concepts, APIs, and configuration options
- Guide users to relevant AWS documentation sections

Guidelines:
- Always prioritize official AWS documentation as your source of truth
- Provide specific, actionable information when possible
- Include relevant links or references to AWS documentation when helpful
- If you're unsure about something, clearly state your limitations
- Focus on being helpful, accurate, and concise in your responses

You have access to AWS documentation search tools to help answer user questions effectively."""

agent = Agent(system_prompt=system_prompt, tools=[stdio_mcp_client.list_tools_sync()])


@app.entrypoint
def agent_invocation(payload, context):
    """Handler for agent invocation"""
    global agent

    user_message = payload.get(
        "prompt",
    )

    if not user_message:
        raise Exception("prompt not provided")
    result = agent(user_message)
    print("context:\n-------\n", context)
    print("result:\n*******\n", result)
    return {"result": result.message}


app.run()
