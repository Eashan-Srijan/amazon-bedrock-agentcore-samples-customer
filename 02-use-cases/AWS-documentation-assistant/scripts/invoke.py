#!/usr/bin/env python3

import argparse
import json
import sys
import boto3
from boto3.session import Session


def get_aws_region():
    """Get AWS region from boto3 session."""
    boto_session = Session()
    return boto_session.region_name


def find_agent_runtime_arn(agent_name: str):
    """Find agent runtime ARN by name.

    Args:
        agent_name: Name of the agent runtime to find

    Returns:
        str: Agent runtime ARN
    """
    region = get_aws_region()

    try:
        agentcore_control_client = boto3.client(
            "bedrock-agentcore-control", region_name=region
        )
    except Exception as e:
        print(f"Error creating AWS control client: {e}", file=sys.stderr)
        sys.exit(1)

    agent_arn = None
    found = False
    next_token = None

    print(f"Searching for agent runtime: {agent_name}")

    try:
        while True:
            kwargs = {"maxResults": 20}
            if next_token:
                kwargs["nextToken"] = next_token

            agent_runtimes = agentcore_control_client.list_agent_runtimes(**kwargs)

            for agent_runtime in agent_runtimes.get("agentRuntimes", []):
                if agent_runtime["agentRuntimeName"] == agent_name:
                    agent_arn = agent_runtime["agentRuntimeArn"]
                    found = True
                    break

            if found:
                break

            next_token = agent_runtimes.get("nextToken")
            if not next_token:
                break

    except Exception as e:
        print(f"Error listing agent runtimes: {e}", file=sys.stderr)
        sys.exit(1)

    if not found:
        print(f"Agent runtime '{agent_name}' not found", file=sys.stderr)
        sys.exit(1)

    print(f"Found agent runtime '{agent_name}' with ARN: {agent_arn}")
    return agent_arn


def invoke_agent(agent_name: str, prompt: str):
    """Invoke an AWS Bedrock agent with a prompt.

    Args:
        agent_name: Name of the agent to invoke
        prompt: Prompt to send to the agent
    """

    region = get_aws_region()
    print(f"Using AWS region: {region}")

    # Find agent runtime ARN
    agent_arn = find_agent_runtime_arn(agent_name)

    # Create agentcore client for invocation
    try:
        boto_session = Session()
        agentcore_client = boto_session.client("bedrock-agentcore")
    except Exception as e:
        print(f"Error creating agentcore client: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Invoking agent with prompt: {prompt}")
    try:
        boto3_response = agentcore_client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            qualifier="DEFAULT",
            payload=json.dumps({"prompt": prompt}),
        )
    except Exception as e:
        print(f"Error invoking agent: {e}", file=sys.stderr)
        sys.exit(1)

    # Process and print the response
    if "text/event-stream" in boto3_response.get("contentType", ""):
        # Handle streaming response
        print("Streaming response:")
        content = []
        for line in boto3_response["response"].iter_lines(chunk_size=10):
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    line = line[6:]
                    print(line)
                    content.append(line)
        print("\nComplete response:", "\n".join(content))

    elif boto3_response.get("contentType") == "application/json":
        # Handle standard JSON response
        content = []
        for chunk in boto3_response.get("response", []):
            content.append(chunk.decode("utf-8"))
        response_data = json.loads("".join(content))
        print("JSON response:")
        print(json.dumps(response_data, indent=2))

    else:
        # Print raw response for other content types
        print("Raw response:")
        print(boto3_response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Invoke AWS Bedrock agent with a prompt"
    )
    parser.add_argument("agent_name", help="Name of the agent to invoke")
    parser.add_argument("prompt", help="Prompt to send to the agent")
    args = parser.parse_args()

    invoke_agent(args.agent_name, args.prompt)
