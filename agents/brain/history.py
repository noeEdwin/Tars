from langchain_core.messages import BaseMessage, SystemMessage

MAX_TURNS = 15

def truncate_messages(messages: list[BaseMessage], max_turns: int = MAX_TURNS) -> list[BaseMessage]:
    """Keep last max_turns messages. Preserves SystemMessages at the front."""
    if len(messages) <= max_turns:
        return messages

    system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    non_system = [m for m in messages if not isinstance(m, SystemMessage)]

    kept = non_system[-max_turns:]
    return system_msgs + kept
