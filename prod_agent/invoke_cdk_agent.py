#!/usr/bin/env python3
"""
Script to invoke the CDK agent using boto3 directly.
This provides an alternative to using the agentcore CLI tool.
"""

import argparse
import boto3
import json
import sys
import os
import logging
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_agent_runtime_arn(agent_name, region=None):
    """
    Get the ARN of the agent runtime by name.
    
    Args:
        agent_name (str): Name of the agent runtime
        region (str, optional): AWS region
        
    Returns:
        str: ARN of the agent runtime or None if not found
    """
    client = boto3.client('bedrock-agentcore-control', region_name=region)
    
    try:
        response = client.list_agent_runtimes()
        for runtime in response.get('agentRuntimeSummaries', []):
            if runtime['agentRuntimeName'] == agent_name:
                return runtime['agentRuntimeArn']
                
        # If we get here, the agent wasn't found
        logger.error(f"Agent runtime '{agent_name}' not found")
        return None
    except Exception as e:
        logger.error(f"Error getting agent runtime ARN: {e}")
        return None

def invoke_agent(agent_arn, prompt, session_id=None, region=None):
    """
    Invoke the agent with a prompt.
    
    Args:
        agent_arn (str): ARN of the agent runtime
        prompt (str): Prompt to send to the agent
        session_id (str, optional): Session ID for continuing conversations
        region (str, optional): AWS region
        
    Returns:
        dict: Response from the agent
    """
    client = boto3.client('bedrock-agentcore', region_name=region)
    
    # Create a session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
        logger.info(f"Created new session ID: {session_id}")
    
    # Prepare the payload
    payload = json.dumps({"prompt": prompt}).encode()
    
    try:
        # Invoke the agent
        logger.info(f"Invoking agent with prompt: {prompt}")
        response = client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            runtimeSessionId=session_id,
            payload=payload
        )
        
        # Parse and return the response
        response_body = json.loads(response['payload'].read().decode())
        return {
            'response': response_body,
            'session_id': session_id
        }
    except Exception as e:
        logger.error(f"Error invoking agent: {e}")
        return {
            'error': str(e),
            'session_id': session_id
        }

def main():
    """
    Main function to parse arguments and invoke the agent.
    """
    parser = argparse.ArgumentParser(description='Invoke CDK Agent')
    parser.add_argument('--agent-name', type=str, default='cdk-agent',
                        help='Name of the agent (default: cdk-agent)')
    parser.add_argument('--prompt', type=str, required=True,
                        help='Prompt to send to the agent')
    parser.add_argument('--session-id', type=str,
                        help='Session ID for continuing conversations')
    parser.add_argument('--region', type=str,
                        help='AWS region')
    parser.add_argument('--profile', type=str,
                        help='AWS profile to use')
    
    args = parser.parse_args()
    
    # Set AWS profile if provided
    if args.profile:
        os.environ['AWS_PROFILE'] = args.profile
    
    # Get the agent ARN
    agent_arn = get_agent_runtime_arn(args.agent_name, args.region)
    if not agent_arn:
        return 1
    
    # Invoke the agent
    result = invoke_agent(agent_arn, args.prompt, args.session_id, args.region)
    
    # Print the result
    print(json.dumps(result, indent=2))
    
    # Save the session ID for future use
    with open('last_session_id.txt', 'w') as f:
        f.write(result['session_id'])
    
    return 0

if __name__ == "__main__":
    sys.exit(main())