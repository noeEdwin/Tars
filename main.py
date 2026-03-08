import os
import sys
import uuid
from pathlib import Path

# Add project root, agents, and brain directories to sys.path
project_root = str(Path(__file__).resolve().parent)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "agents"))
sys.path.insert(0, os.path.join(project_root, "agents", "brain"))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Load environment variables
load_dotenv()

from agents.brain.nodes import workflow, config
from agents.RAG.ingest_document import ingest_pdf
from agents.RAG.save_memory import get_db_uri, save_long_term_memory
from ChatMessage.infraestructure.stt.openai_stt import record_and_transcribe
from langgraph.checkpoint.postgres import PostgresSaver
from dataBase.main_queries import get_user_id_from_username, get_roleplay_contexts, get_scene_from_filename
from dataBase.user_management import get_or_create_active_conversation

def main():

    DB_URI = get_db_uri()
    
    input_mode = "text" # Default to text
    
    user_name = input("Enter your username: ").strip()
    
    db_user_id = get_user_id_from_username(user_name)
    if db_user_id is None:
        print(f"User '{user_name}' not found in database. Entering guest mode (user_id=1).")
        user_id = "1"
    else:
        user_id = str(db_user_id)
        
    print("\nSelect Mode:")
    print("1. Normal Mode (HSK Tutor - single continuous conversation)")
    print("2. Roleplay Mode (Immersive Scenarios - new conversation)")
    mode_choice = input("Choice (1/2): ").strip()

    thread_id = ""
    user_role = ""
    tars_role = ""
    scene = ""
    current_mode = ""

    if mode_choice == "2":
        print("\nRoleplay Context Options:")
        print("1. See files already uploaded")
        print("2. Upload a new one")
        rp_choice = input("Choice (1/2): ").strip()
        
        doc_id = None
        if rp_choice == "2":
            file_path = input("Enter the path to the PDF file: ").strip()
            if os.path.exists(file_path):
                ingest_pdf(file_path, user_id=int(user_id))
                filename = os.path.basename(file_path)
                doc_id, scene = get_scene_from_filename(user_id, filename)
                print(f"Loaded context from newly uploaded file: {filename}")
            else:
                print("File not found. Using empty custom scene.")
                scene = input("Custom Scene Description: ").strip()
        else:
            filenames = get_roleplay_contexts(user_id)
            if not filenames:
                print("No roleplay contexts found in document_store for this user. Using default scene.")
                scene = input("Scene Description: ").strip()
            else:
                print("\nAvailable Contexts in Database:")
                for i, filename in enumerate(filenames):
                    print(f"{i+1}. {filename}")
                print(f"{len(filenames)+1}. Custom Scene")
                
                doc_choice = input(f"Select context [1-{len(filenames)+1}]: ").strip()
                try:
                    choice_idx = int(doc_choice) - 1
                    if 0 <= choice_idx < len(filenames):
                        selected_filename = filenames[choice_idx]
                        doc_id, scene = get_scene_from_filename(user_id, selected_filename)
                        print(f"Loaded context from: {selected_filename}")
                    else:
                        scene = input("Scene Description: ").strip()
                except ValueError:
                    scene = input("Scene Description: ").strip()
            
        tars_role = input("Tars' Character Role: ").strip()
        user_role = input("Your Character Role: ").strip()
        
        # New Unique thread ID for branch
        thread_id = f"{user_id}_roleplay_{uuid.uuid4().hex[:8]}"
        current_mode = "tars_roleplay"
        print(f"\n✅ Setup complete. Tars will play {tars_role} in this scenario. Start chatting!")
    else:
        # Standard persistent thread ID for the user
        thread_id = f"{user_id}_normal"
        current_mode = "tars_normal"
        print("\n✅ Normal Mode Started. Tars is your HSK tutor.")
        
    conversation_id = get_or_create_active_conversation(int(user_id), current_mode)
        
    # Update config with new thread_id
    config["configurable"]["thread_id"] = thread_id

    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        checkpointer.setup()
        app = workflow.compile(checkpointer=checkpointer)
        
        # Initialize state based on mode
        if mode_choice == "2":
            sys_msg_text = f"SYSTEM UPDATE: User has initiated a roleplay.\nSCENE: {scene}\nUSER ROLE: {user_role}\nTARS ROLE: {tars_role}\n\n PLEASE ADOPT THIS PERSONA IMMEDIATELY."
            current_state_update = {
                "user_mode": "tars_roleplay",
                "active_expert": "tars_roleplay",
                "user_id": int(user_id),
                "scene_context": scene,
                "user_role": user_role,
                "selected_role": tars_role,
                "selected_source": str(doc_id) if doc_id else None,
                "messages": [HumanMessage(content=sys_msg_text)]
            }
            # App invoke to get the first greeting from Tars
            result = app.invoke(current_state_update, config=config)
            output_messages = result.get("messages", [])
            if output_messages:
                last_msg = output_messages[-1]
                if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                    for tc in last_msg.tool_calls:
                        if tc['name'] == 'TarsResponse':
                            final_answer = tc['args'].get('message', 'No message content')
                            print(f"Tars ({tars_role}): {final_answer}")
                            save_long_term_memory(conversation_id, "assistant", final_answer)
                elif isinstance(last_msg, AIMessage) and not getattr(last_msg, 'tool_calls', None):
                    print(f"Tars ({tars_role}): {last_msg.content}")

        # Auto-recovery logic from nodes.py
        snapshot = app.get_state(config)
        if snapshot.values and "messages" in snapshot.values:
            last_msg = snapshot.values["messages"][-1]
            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                print("System: Detected interrupted session. healing connection...")
                tool_msgs = []
                for tc in last_msg.tool_calls:
                    tool_msgs.append(
                        ToolMessage(
                            content="System: The tool execution was interrupted by the user in the previous session.",
                            tool_call_id=tc["id"]
                        )
                    )
                app.update_state(config, {"messages": tool_msgs})

        while True:
            try:
                if input_mode == "voice":
                    user_input = record_and_transcribe()
                    if not user_input:
                        continue
                    print(f"User (Voice): {user_input}")
                else:
                    user_input = input("User: ").strip()
                    if not user_input:
                        continue
            except KeyboardInterrupt:
                break
                
            lowercase_input = user_input.lower()
            if lowercase_input in ["/exit", "exit", "quit", "end"]:
                break
                
            if lowercase_input == "/voice":
                input_mode = "voice"
                print("🎙️ Switched to Voice Input mode. (Press Enter to start/stop recording)")
                continue
                
            if lowercase_input == "/text":
                input_mode = "text"
                print("⌨️ Switched to Text Input mode.")
                continue
                
            if user_input.startswith("/upload "):
                file_path = user_input.replace("/upload ", "").strip()
                if os.path.exists(file_path):
                    ingest_pdf(file_path)
                    print(f"✅ Uploaded {file_path}. You can now ask questions about it.")
                else:
                    print(f"❌ File not found: {file_path}")
                continue

            # Standard Chat Interaction
            save_long_term_memory(conversation_id, "user", user_input)
            
            # Formally declare the user mode in the state payload 
            current_state_update = {
                "user_mode": current_mode,
                "active_expert": current_mode,
                "user_id": int(user_id),
                "messages": [HumanMessage(content=user_input)]
            }
            
            # Get current state to calculate offset
            snapshot = app.get_state(config)
            current_values = snapshot.values if snapshot.values else {}
            existing_messages = current_values.get("messages", [])
            start_len = len(existing_messages)
            
            result = app.invoke(
                current_state_update, 
                config=config
            )
            
            output_messages = result.get("messages", [])
            new_messages = output_messages[start_len:]
            
            for msg in new_messages:
                # Logic for TOOL CALLS (TarsResponse)
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        if tc['name'] == 'TarsResponse':
                            final_answer = tc['args'].get('message', 'No message content')
                            print(f"Tars: {final_answer}")
                            save_long_term_memory(conversation_id, "assistant", final_answer)
                
                # Logic for TEXT RESPONSES
                if isinstance(msg, AIMessage) and not getattr(msg, 'tool_calls', None):
                    print("Tars: " + msg.content)

if __name__ == "__main__":
    main()
