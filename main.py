import os
import sys
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
from agents.RAG.save_memory import save_memory, get_db_uri
from ChatMessage.infraestructure.stt.openai_stt import record_and_transcribe
from agents.dataBase.user_management import create_user, get_user_data, ensure_conversation_exists
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres import PostgresSaver

def main():
    print("🤖 Tars CLI - Multi-Modal Edition")
    print("commands:")
    print("  /upload <path_to_pdf>  - Ingest a PDF file")
    print("  /roleplay              - Setup a roleplay scenario")
    print("  /voice                 - Toggle Voice Input (STT)")
    print("  /text                  - Toggle Text Input")
    print("  /exit, quit            - Quit")
    print("-" * 50)

    DB_URI = get_db_uri()
    
    input_mode = "text" # Default to text

    # 1. Configuración inicial de Usuario (Estructura Noe)
    nombre_usuario = input("Who are you?: ").strip()
    if not nombre_usuario:
        nombre_usuario = "diego"
        
    password_usuario = "mi_clave_segura_123" # <--- Default as requested
    
    # Registramos al usuario si no existe con nivel inicial
    create_user(nombre_usuario, password_usuario, hsk_level=1, interest_area="Ingeniería")
    user_info = get_user_data(nombre_usuario)
    
    if not user_info:
        print("❌ Could not load user. Exiting.")
        return

    # 2. Definimos el ID de conversación (Relacional)
    current_conv_id = 2
    ensure_conversation_exists(current_conv_id, user_info['id'])
    
    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        checkpointer.setup()
        
        # Guardaremos el ID de coversacion en la config del checkpointer
        config = {
            "configurable": {
                "thread_id": str(current_conv_id) # Usa current_conv_id para aislar estados
            }
        }
        
        app = workflow.compile(checkpointer=checkpointer)
        
        # Auto-recovery logic: Deep heal any unresolved tool calls across full history
        snapshot = app.get_state(config)
        if snapshot.values and "messages" in snapshot.values:
            messages = snapshot.values["messages"]
            msgs_to_update = []
            
            for i, msg in enumerate(messages):
                if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                    # Check if the next message is a ToolMessage
                    has_tool_response = False
                    if i + 1 < len(messages):
                        next_msg = messages[i+1]
                        if isinstance(next_msg, ToolMessage):
                            has_tool_response = True
                            
                    if not has_tool_response:
                        print(f"System: Healing unresolved tool call in history (Msg ID: {msg.id})...")
                        # Flatten the tool calls into the message content and remove tool calls
                        fallback_content = msg.content
                        if not fallback_content:
                            for tc in msg.tool_calls:
                                if tc.get("name") == "TarsResponse":
                                    fallback_content = "Tars: " + str(tc.get("args", {}).get("message", ""))
                                    break
                                    
                        msgs_to_update.append(
                            AIMessage(
                                id=msg.id,
                                content=fallback_content or "[Unresolved Tool Call]",
                                tool_calls=[]
                            )
                        )
            
            if msgs_to_update:
                app.update_state(config, {"messages": msgs_to_update})

        while True:
            try:
                if input_mode == "voice":
                    user_input = record_and_transcribe()
                    if not user_input:
                        continue
                    print(f"User (Voice): {user_input}")
                else:
                    user_input = input(f"User ({user_info['username']}): ").strip()
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

            # Roleplay Setup
            if lowercase_input == "/roleplay":
                print("\n🎭 Roleplay Setup")
                scene = input("Scene Description: ").strip()
                user_role = input("Your Character Name: ").strip()
                tars_role = input("Tars' Character Name: ").strip()
                
                print(f"✅ Setup complete. Tars will play {tars_role} in '{scene}'. Start chatting!")
                
                sys_msg = f"SYSTEM UPDATE: User has initiated a roleplay.\nSCENE: {scene}\nUSER ROLE: {user_role}\nTARS ROLE: {tars_role}\n\n प्लीज ADOPT THIS PERSONA IMMEDIATELY."
                
                current_state_update = {
                    "user_mode": "tars_roleplay",
                    "active_expert": "tars_roleplay",
                    "scene_context": scene,
                    "user_role": user_role,
                    "selected_role": tars_role,
                    "messages": [HumanMessage(content=sys_msg)]
                }
                
                result = app.invoke(current_state_update, config=config)
                # Output handling for roleplay initiation
                output_messages = result.get("messages", [])
                if output_messages:
                    last_msg = output_messages[-1]
                    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                        for tc in last_msg.tool_calls:
                            if tc['name'] == 'TarsResponse':
                                final_answer = tc['args'].get('message', 'No message content')
                                print(f"Tars ({tars_role}): {final_answer}")
                                save_memory("assistant", final_answer)
                    elif isinstance(last_msg, AIMessage) and not getattr(last_msg, 'tool_calls', None):
                        print(f"Tars ({tars_role}): {last_msg.content}")
                continue

            # Standard Chat Interaction
            save_memory("user", user_input, current_conv_id)
            messages = [HumanMessage(content=user_input)]
            
            # Get current state to calculate offset
            snapshot = app.get_state(config)
            current_values = snapshot.values if snapshot.values else {}
            existing_messages = current_values.get("messages", [])
            start_len = len(existing_messages)
            
            # Pasamos user_info junto con los mensajes al estado
            result = app.invoke(
                {
                    "messages": messages,
                    "user_info": user_info
                }, 
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
                            save_memory("assistant", final_answer, current_conv_id)
                
                # Logic for TEXT RESPONSES
                if isinstance(msg, AIMessage) and not getattr(msg, 'tool_calls', None):
                    print("Tars: " + msg.content)

if __name__ == "__main__":
    main()
