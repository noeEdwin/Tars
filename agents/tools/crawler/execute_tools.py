from brain.schema import TarsState
import json
from langchain_core.messages import AIMessage, ToolMessage
from schema import FileAction
from tools.crawler.hands import TarsHands
import os

hands = TarsHands()


def execute_tools(state: TarsState) -> TarsState:
    last_ai_message: AIMessage = state["messages"][-1]

    if not hasattr(last_ai_message, "tool_calls") or not last_ai_message.tool_calls:
        return {"messages": []}
    
    tool_messages = []

    for tool_call in last_ai_message.tool_calls:
        call_id = tool_call["id"]
        tool_name = tool_call["name"]
        args = tool_call["args"]
        
        result = "Error: Internal processing failure."

        if tool_name == "TarsResponse":
            paths_to_check = args.get("identified_paths", [])
            verification_results = {}

            for p in paths_to_check:
                if hands._is_safe(p):
                    verification_results[p] = "Exists" if os.path.exists(p) else "Not Found on Disk"
                else:
                    verification_results[p] = "Access Denied (Unsafe)"

            content_report = {
                "status": "Verification Complete",
                "disk_check": verification_results,
                "note": "Inform the user if any identified paths were missing from the physical disk."
            }

            tool_messages.append(
                ToolMessage(
                    content=json.dumps(content_report), 
                    tool_call_id=call_id
                )
            )

        elif tool_name == "TarsAction":
            action_type = args.get("action_type")
            path = args.get("source_path")
            content = args.get("content", "")
            dest = args.get("destination_path")

            if not hands._is_safe(path):
                tool_messages.append(
                    ToolMessage(content="Error: Path is outside allowed boundaries.", tool_call_id=call_id)
                )
                continue

            try:
                if action_type == FileAction.CREATE:
                    result = hands.create_file(path, content)
                elif action_type == FileAction.UPDATE:
                    result = hands.update_file(path, content, mode=args.get("mode", "append"))
                elif action_type == FileAction.DELETE:
                    result = hands.delete_path(path)
                elif action_type == FileAction.MOVE:
                    result = hands.move_path(path, dest)
                elif action_type == FileAction.LIST:
                    result = hands.list_files(path)
                    result = str(result) + "\n\nSYSTEM HINT: If you see [DIR] entries relevant to your search, you must LIST them next. Do not stop yet."
                elif action_type == FileAction.READ:
                    result = hands.read_code(path)
                elif action_type == FileAction.CREATE_DIRECTORY:
                    result = hands.create_directory(path)
                elif action_type == FileAction.READ_DOC:
                    result = hands.read_document(path)
                elif action_type == FileAction.EXECUTE:
                    result = FileAction.execute_command(content)
                else:
                    result = f"Action {action_type} not implemented."
            except Exception as e:
                result = f"Execution Error: {str(e)}"
                
            tool_messages.append(
                ToolMessage(content=str(result), tool_call_id=call_id)
            )
        
        # Catch any unhandled tools to prevent corrupted state
        else:
            print(f"[WARNING] Unhandled tool: '{tool_name}'")
            tool_messages.append(
                ToolMessage(
                    content=f"Error: Unknown tool '{tool_name}'. Only TarsResponse and TarsAction are supported.",
                    tool_call_id=call_id
                )
            )

    return {"messages": tool_messages}