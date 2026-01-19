import json
from typing import List, Dict, Any
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage, HumanMessage
from langchain_community.tools import TavilySearchResults

tavily_tool = TavilySearchResults(max_results=5)

def execute_tools(state: List[BaseMessage]) -> List[BaseMessage]:
    last_ai_message: AIMessage = state[-1]

    if not hasattr(last_ai_message, "tool_calls") or not last_ai_message.tool_calls:
        return []
    
    tool_messages = []

    for tool_call in last_ai_message.tool_calls:
        if tool_call["name"] in ["AnswerQuestiton", "ReviseAnswer"]:
            call_id = tool_call["id"]
            search_queries = tool_call["args"].get("search_queries", [])

            query_results = {}
            for query in search_queries:
                result = tavily_tool.invoke(query) 
                query_results[query] = result
            
            tool_messages.append(
                ToolMessage(
                    content=json.dumps(query_results),
                    tool_call_id=call_id
                )
            )
    return tool_messages

test_state = [
    HumanMessage(
        content="Write about how small business can leverage AI to grow"
    ),
    AIMessage(
        content="",
        tool_calls=[
            {
                "name":"AnswerQuestion",
                "args":{
                    'answer':'',
                    'search_queries': [
                        'AI tools for small business',
                        'AI in small business marketing',
                        'AI automation for small business'
                    ],
                    'reflection':{
                        'missing':'',
                        'superfluous':''
                    },
                    "id":'call_KpYHichFFEmLitHFvFhKy1Ra'
                }
            }
        ]
    )
]

results = execute_tools(test_state)