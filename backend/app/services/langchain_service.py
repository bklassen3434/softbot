from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langsmith import Client
from langchain.callbacks.tracers import LangChainTracer
from langchain.callbacks.manager import CallbackManager
from langchain_community.chat_message_histories import RedisChatMessageHistory
from app.core.config import settings

# LangSmith setup
client = Client()
tracer = LangChainTracer(project_name="softball-chatbot", client=client)
callback_manager = CallbackManager([tracer])

# LLM setup
llm = ChatOpenAI(
    model=settings.MODEL_NAME,
    temperature=settings.TEMPERATURE,
    max_tokens=settings.MAX_TOKENS,
    openai_api_key=settings.OPENAI_API_KEY,
    callback_manager=callback_manager
)

# Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{input}")
])

# Base chain
# chain = prompt | llm
chain = llm

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Get or create a Redis-based chat history for the given session."""
    history = RedisChatMessageHistory(
        session_id=session_id,
        url=settings.REDIS_URL
    )

    if len(history.messages) == 0:
        history.clear()
    return history

# Final runnable
chat = RunnableWithMessageHistory(
    runnable=chain,
    get_session_history=get_session_history,
    input_key="input"
)

# Main entry point
def run_chain(user_input: str, session_id: str = "default") -> str:
    """Run the conversation chain with Redis-backed history."""
    return chat.invoke(
        {"input": user_input},
        config={"configurable": {"session_id": session_id}}
    ).content
