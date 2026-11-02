
from langchain_groq import ChatGroq
import logfire

from app.agents.state import AgentState
from app.config import settings


# Initialize Groq model directly
llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0.1,
)


def generate_node(state: AgentState):
    """
    Generates a response using technical documentation
    and conversation history.
    Uses Groq directly without any API gateway.
    """

    query = state["current_query"]

    # Build conversation history
    history_str = ""

    for msg in state["messages"][:-1]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"

    user_msg = (
        state["messages"][-1]["content"]
        if state["messages"]
        else ""
    )

    # Conversational response
    if query == "CONVERSATIONAL":

        logfire.info("Generating conversational response using memory.")

        prompt = f"""
        You are a friendly and helpful Enterprise AI Assistant.

        Answer the user's latest message using the
        CONVERSATION HISTORY below.

        CONVERSATION HISTORY:
        {history_str}

        LATEST MESSAGE:
        "{user_msg}"
        """

    # Technical RAG response
    else:

        logfire.info("Generating technical RAG response.")

        max_context_chars = 25000
        full_context = ""

        for doc in state["documents"]:
            if len(full_context) + len(doc) < max_context_chars:
                full_context += doc + "\n\n"
            else:
                logfire.warning(
                    "Context truncated to fit Groq TPM limits."
                )
                break

        prompt = f"""
        You are a Senior Technical Architect.

        Answer the question using the TECHNICAL CONTEXT provided.
        If the context does not contain the answer, clearly say so.

        TECHNICAL CONTEXT:
        {full_context}

        CONVERSATION HISTORY:
        {history_str}

        USER QUESTION:
        "{user_msg}"
        """

    # Generate response using Groq
    with logfire.span("✍️ LLM Synthesis"):
        try:
            response = llm.invoke(prompt)

            content = response.content

            logfire.info("Response generated successfully.")

            return {
                "final_answer": content,
                "status": "Response generated.",
                "messages": [
                    {
                        "role": "assistant",
                        "content": content
                    }
                ]
            }

        except Exception as e:
            logfire.error(f"LLM Generation failed: {e}")
            raise
