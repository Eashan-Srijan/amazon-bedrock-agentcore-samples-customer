#!/usr/bin/env python3

import argparse
import sys
import time
from boto3.session import Session
from bedrock_agentcore_starter_toolkit import Runtime


def get_aws_region():
    """Get AWS region from boto3 session."""
    boto_session = Session()
    return boto_session.region_name


def configure_agent(agent_name: str):
    """Configure an AWS Bedrock agent.

    Args:
        agent_name: Name of the agent to configure
    """

    region = get_aws_region()
    print(f"Using AWS region: {region}")

    print("Initializing AgentCore Runtime")
    try:
        agentcore_runtime = Runtime()
    except Exception as e:
        print(f"Error initializing AgentCore Runtime: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Configuring agent: {agent_name}")
    try:
        _ = agentcore_runtime.configure(
            agent_name=agent_name,
            entrypoint="main.py",
            auto_create_execution_role=True,
            auto_create_ecr=True,
            requirements_file="requirements.txt",
            region=region,
        )
        print(f"Successfully configured agent: {agent_name}")
        return agentcore_runtime
    except Exception as e:
        print(f"Error configuring agent: {e}", file=sys.stderr)
        sys.exit(1)


def launch_agent(agentcore_runtime, use_codebuild: bool = True):
    """Launch an AWS Bedrock agent.

    Args:
        agentcore_runtime: Already initialized Runtime instance
        use_codebuild: Whether to use CodeBuild for launching
    """

    print(f"Launching agent with CodeBuild: {use_codebuild}")
    try:
        launch_result = agentcore_runtime.launch(use_codebuild=use_codebuild)
        print(f"Launch initiated successfully: {launch_result}")
    except Exception as e:
        print(f"Failed to launch agent: {e}", file=sys.stderr)
        sys.exit(1)

    print("Checking initial status")
    try:
        status_response = agentcore_runtime.status()
        status = status_response.endpoint["status"]
        print(f"Initial status: {status}")
    except Exception as e:
        print(f"Failed to get initial status: {e}", file=sys.stderr)
        sys.exit(1)

    end_status = ["READY", "CREATE_FAILED", "DELETE_FAILED", "UPDATE_FAILED"]
    print(f"Monitoring status until one of: {end_status}")

    while status not in end_status:
        print("Waiting 10 seconds before next status check...")
        time.sleep(10)

        try:
            status_response = agentcore_runtime.status()
            status = status_response.endpoint["status"]
            print(f"Current status: {status}")
        except Exception as e:
            print(f"Failed to get status: {e}", file=sys.stderr)
            break

    if status in ["READY"]:
        print("Agent launched successfully!")
    elif status in ["CREATE_FAILED", "DELETE_FAILED", "UPDATE_FAILED"]:
        print(f"Agent launch failed with status: {status}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"Monitoring stopped with unexpected status: {status}", file=sys.stderr)

    print(f"Final status: {status}")
    return status


def deploy_agent(agent_name: str, use_codebuild: bool = True):
    """Configure and launch an AWS Bedrock agent.

    Args:
        agent_name: Name of the agent to configure and launch
        use_codebuild: Whether to use CodeBuild for launching
    """
    print(f"Starting deployment of agent: {agent_name}")
    print("=" * 50)

    # Step 1: Configure
    print("Step 1: Configuring agent...")
    agentcore_runtime = configure_agent(agent_name)

    print("\n" + "=" * 50)

    # Step 2: Launch
    print("Step 2: Launching agent...")
    status = launch_agent(agentcore_runtime, use_codebuild)

    print("\n" + "=" * 50)
    print(f"Deployment completed with status: {status}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Configure and launch AWS Bedrock agent"
    )
    parser.add_argument("agent_name", help="Name of the agent to configure and launch")
    parser.add_argument(
        "--no-codebuild", action="store_true", help="Launch without CodeBuild"
    )
    args = parser.parse_args()

    deploy_agent(args.agent_name, use_codebuild=not args.no_codebuild)
