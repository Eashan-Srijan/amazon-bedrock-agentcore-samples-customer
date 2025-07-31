#!/usr/bin/env python3

import argparse
import sys
import boto3
from boto3.session import Session


def get_aws_region():
    """Get AWS region from boto3 session."""
    boto_session = Session()
    return boto_session.region_name


def delete_agent_runtime(agent_name: str, dry_run: bool = False):
    """Delete an agent runtime by name from AWS Bedrock AgentCore.

    Args:
        agent_name: Name of the agent runtime to delete
        dry_run: Show what would be deleted without actually deleting
    """

    region = get_aws_region()
    print(f"Using AWS region: {region}")

    try:
        agentcore_control_client = boto3.client(
            "bedrock-agentcore-control", region_name=region
        )
    except Exception as e:
        print(f"Error creating AWS client: {e}", file=sys.stderr)
        sys.exit(1)

    agent_id = None
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
                    agent_id = agent_runtime["agentRuntimeId"]
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

    if found:
        print(f"Found agent runtime '{agent_name}' with ID: {agent_id}")

        if dry_run:
            print(f"[DRY RUN] Would delete agent runtime: {agent_name}")
            return

        try:
            agentcore_control_client.delete_agent_runtime(agentRuntimeId=agent_id)
            print(f"Successfully deleted agent runtime: {agent_name}")
        except Exception as e:
            print(f"Error deleting agent runtime: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Agent runtime '{agent_name}' not found", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Delete an agent runtime from AWS Bedrock AgentCore"
    )
    parser.add_argument("agent_name", help="Name of the agent runtime to delete")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    args = parser.parse_args()

    delete_agent_runtime(args.agent_name, args.dry_run)
