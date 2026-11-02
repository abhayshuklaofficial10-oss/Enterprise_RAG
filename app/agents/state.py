from typing import TypedDict, List,Annotated
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    current_query: str
    documents: List[str]
    final_answer:str
    status:str
    plan: str

