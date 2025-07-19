from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

# Create CDK MCP client
cdk_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx", args=["awslabs.cdk-mcp-server@latest"]
        )
    )
)

# Initialize Bedrock model
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    temperature=0.7,
)

# Define system prompt for CDK agent
SYSTEM_PROMPT = """
You are an AWS CDK expert. Your role is to help customers build infrastructure as code using AWS CDK.
You can generate CDK code in TypeScript, Python, Java, C#, or Go based on customer requirements.
Always follow AWS best practices and security guidelines when generating CDK code.
"""

def run_cdk_agent(query):
    """
    Run the CDK agent with the given query.
    
    Args:
        query (str): The user's query about CDK
        
    Returns:
        str: The agent's response
    """
    with cdk_client:
        # Get all available tools from the CDK MCP server
        tools = cdk_client.list_tools_sync()
        
        # Create the agent with the tools and model
        agent = Agent(tools=tools, model=bedrock_model, system_prompt=SYSTEM_PROMPT)
        
        # Process the query and return the response
        response = agent(query)
        return response

if __name__ == "__main__":
    # Example usage
    user_query = "Create a CDK stack that deploys an S3 bucket with versioning enabled"
    result = run_cdk_agent(user_query)
    print(result)