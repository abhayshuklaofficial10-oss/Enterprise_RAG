import logfire
from app.agents.state import AgentState
from app.services.retrieval.qdrant_service import search_enterprise_knowledge

def retrieve_node(state: AgentState):
    """
    Performs vector search in Qdrant for technical queries.
    """

    query = state["current_query"]

    with logfire.span("🔍 Knowledge Retrieval"):

        logfire.info(f"Searching Qdrant for: {query}")

        # Retrieve top 5 relevant documents directly
        raw_results = search_enterprise_knowledge(query, limit=5)

        logfire.info(
            f"Retrieved {len(raw_results)} documents from Qdrant."
        )

        # Extract document content
        doc_contents = [
            doc["content"]
            for doc in raw_results
        ]

        # Format retrieved documents
        formatted_docs = [
            f"CONTENT: {doc}"
            for doc in doc_contents
        ]

    return {
        "documents": formatted_docs,
        "status": "Technical context retrieved.",
        "plan": state["plan"] + ["Context Retrieved"]
    }
