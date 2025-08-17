import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
import re
from llm_utils import generate_issue_title

JIRA_MCP_URL = "http://localhost:9000/mcp"

async def perform_jira_action(intent: str, user_input: str):
    headers = {
        "accept": "text/event-stream" 
    }

    async with streamablehttp_client(JIRA_MCP_URL, headers=headers) as (reader, writer, _):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            # print(await session.list_tools())
            print(intent)
            summary = generate_issue_title(user_input)
            try:
                if  intent == "Create Issue":
                    return await session.call_tool("jira_create_issue", {
                        "project_key": "AIDEVOPS",
                        "issue_type": "Task",
                        "summary": summary,
                        "description": user_input
                    })
                elif intent == "Get Issue":
                    # Match Jira issue key: uppercase letters + hyphen + number (e.g., DEVOPS-101)
                    match = re.search(r"\b([A-Z][A-Z0-9]+-\d+)\b", user_input)
        
                    if match:
                        issue_key = match.group(1)
                        return await session.call_tool("jira_get_issue", {"issue_key": issue_key})
                    else:
                        return {"error": "No valid Jira issue key found in your message."}
                else:
                    return {"error": f"Intent '{intent}' not recognized."}
            except Exception as e:
                print("Encountered an error:", e)
                


