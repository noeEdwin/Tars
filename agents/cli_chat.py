import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the agents directory to sys.path so sibling packages can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Add agents/brain to sys.path so schema and chains can be imported directly
sys.path.insert(0, str(Path(__file__).resolve().parent / "brain"))


load_dotenv()

from agents.brain.nodes import workflow, config, TarsState
from agents.RAG.ingest_document import ingest_pdf
from langchain_core.messages import HumanMessage, AIMessage

def main():
    print("🤖 Tars CLI - RAG Edition")
    print("commands:")
    print("  /upload <path_to_pdf>  - Ingest a PDF file")
    print("  /exit                  - Quit")
    print("  <message>              - Chat with Tars")
    print("-" * 50)

    # Initialize the app
    from langgraph.checkpoint.postgres import PostgresSaver
    from agents.dataBase.connection import get_db_connection
    from agents.RAG.save_memory import get_db_uri
    
    DB_URI = get_db_uri() # This function is in save_memory.py, let's import it or just build it
    # Actually get_db_uri is in RAG/save_memory.py. Let's fix that import if needed.
    # checking imports... nodes.py imports get_db_uri from RAG.save_memory
    from agents.RAG.save_memory import get_db_uri

    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        checkpointer.setup()
        app = workflow.compile(checkpointer=checkpointer)
        
        while True:
            try:
                user_input = input("User: ").strip()
            except KeyboardInterrupt:
                break
                
            if not user_input:
                continue
                
            if user_input.lower() in ["/exit", "exit", "quit"]:
                break
                
            if user_input.startswith("/upload "):
                file_path = user_input.replace("/upload ", "").strip()
                if os.path.exists(file_path):
                    ingest_pdf(file_path)
                    print(f"✅ Uploaded {file_path}. You can now ask questions about it.")
                else:
                    print(f"❌ File not found: {file_path}")
                continue

            # Roleplay Setup
            if user_input.lower() == "/roleplay":
                print("\n🎭 Roleplay Setup")
                scene = input("Scene Description: ").strip()
                user_role = input("Your Character Name: ").strip()
                tars_role = input("Tars' Character Name: ").strip()
                
                print(f"✅ Setup complete. Tars will play {tars_role} in '{scene}'. Start chatting!")
                
                # We need to inject this into the state. We can do it by sending a hidden system message or just updating config?
                # Best way is to pass these keys in the input dict of the next invoke.
                # However, to make it immediate, we can trigger an 'initialization' turn or just wait for next user input.
                # Let's wait for next user input but store these changes to be sent then.
                
                # We can inject a system message to prime the context immediately.
                sys_msg = f"SYSTEM UPDATE: User has initiated a roleplay.\nSCENE: {scene}\nUSER ROLE: {user_role}\nTARS ROLE: {tars_role}\n\n प्लीज ADOPT THIS PERSONA IMMEDIATELY."
                
                # Update state variables for persistence
                current_state_update = {
                    "user_mode": "tars_roleplay",
                    "active_expert": "tars_roleplay",
                    "scene_context": scene,
                    "user_role": user_role,
                    "selected_role": tars_role,
                    "messages": [HumanMessage(content=sys_msg)]
                }
                
                result = app.invoke(current_state_update, config=config)
                 # Print response
                output_messages = result.get("messages", [])
                if output_messages:
                    last_msg = output_messages[-1]
                    if isinstance(last_msg, AIMessage):
                        print(f"Tars ({tars_role}): {last_msg.content}")
                continue

            # Standard Chat Interaction
            # We need to manually construct the state update
            messages = [HumanMessage(content=user_input)]
            
            # The workflow expects a dict with "messages"
            # We need to get the current state to append correctly or let LangGraph handle it
            
            result = app.invoke(
                {"messages": messages}, 
                config=config
            )
            
            # Print the LAST AI message
            # The graph returns the full state or updates. result['messages'] contains the full history usually?
            # Let's check how nodes.py does it. It slices.
            
            # But app.invoke returns the final state.
            output_messages = result.get("messages", [])
            if output_messages:
                last_msg = output_messages[-1]
                if isinstance(last_msg, AIMessage):
                    print(f"Tars: {last_msg.content}")

if __name__ == "__main__":
    main()
