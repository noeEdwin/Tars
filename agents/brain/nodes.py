from dotenv import load_dotenv

from langgraph.graph import END, START, StateGraph
from agents.brain.schema import TarsState

# Importamos los nodos modularizados
from agents.brain.node_learning import lesson_prompt_node, lesson_check_node
from agents.brain.node_roleplay import actor_node

load_dotenv()

ACTOR         = "tars_actor"
LESSON_PROMPT = "lesson_prompt"
LESSON_CHECK  = "lesson_check"

# ─────────────────────────────────────────────────────────────────────────────
# Routing
# ─────────────────────────────────────────────────────────────────────────────
def route_lesson(state: TarsState) -> str:
    """Route to the correct node based on mode and lesson phase."""
    if state.get("user_mode") != "tars_normal":
        return ACTOR
    if state.get("awaiting_answer"):
        return LESSON_CHECK
    return LESSON_PROMPT

# ─────────────────────────────────────────────────────────────────────────────
# Graph assembly
# ─────────────────────────────────────────────────────────────────────────────
workflow = StateGraph(TarsState)

workflow.add_node(ACTOR,         actor_node)
workflow.add_node(LESSON_PROMPT, lesson_prompt_node)
workflow.add_node(LESSON_CHECK,  lesson_check_node)

workflow.add_conditional_edges(START, route_lesson, {
    ACTOR:         ACTOR,
    LESSON_PROMPT: LESSON_PROMPT,
    LESSON_CHECK:  LESSON_CHECK,
})

workflow.add_edge(ACTOR,         END)
workflow.add_edge(LESSON_PROMPT, END)
workflow.add_edge(LESSON_CHECK,  END)

config = {
    "configurable": {
        "thread_id": 1
    }
}