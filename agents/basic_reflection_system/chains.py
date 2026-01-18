from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

generation_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
                You are a twitter techie influencer asssistant tasked with writing
                excellent twitter posts.
            """
            "Generate the best twitter post possible for the user's request."
            """
                If the user provides critique, respond with a revised version of your previous
                attempts
            """,
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

reflection_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
                You're a viral twitter influencer grading a tweet. Generate critique and
                recomendations for the user's tweet
            """
            """
                Always provide detailed recommendations, including requests for length,
                virality, style, etc.
            """,
        ),
        MessagesPlaceholder(variable_name="messages")
    ]
)

llm = ChatOpenAI(model_name="gpt-4")

generation_chain = generation_prompt | llm
reflection_chain = reflection_prompt | llm