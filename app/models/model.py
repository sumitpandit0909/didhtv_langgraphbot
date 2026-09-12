from langgraph.graph import MessageGraph
from typing import Annotated,Literal,Optional ,List
from pydantic import Field, BaseModel
from langgraph.graph.message import add_messages


#supervisor output model
class RouteDecision(BaseModel):
    next_node: Literal[
        "product_inquiry",
        "company_info",
        "recharge_request",
        "history_check",
        "escalate_support",
        "technical_troubleshoot",
        "general_chat"
    ] = Field(..., description="next specialis node that should handle the request")
    reason :str =Field(...,description="Short justification for routing choice")

#recharge model

class RechargeSlots(BaseModel):
    amount:Optional[int] =Field(None,description="recharge amout in INR(eg:299,499)")
    package_name:Optional[str]= Field(None,description="Nameof the pack/plan (eg: entertainment pack,family pack )")
    user_id:Optional[str]=Field(None,description="user_id or VC number")
    is_confirmed:Optional[bool]=Field(False,description="flag to indicate if user confirmed the recharge amount")


class AgentState(BaseModel):
    messages:Annotated[list,add_messages]
    user_id:str
    conversation_id:str
    next_node:Optional[str]=None

    recharge_slots:RechargeSlots =Field(default_factory=RechargeSlots)
    awaiting_recharge_confirmation:bool =False
    sentiment_score:Literal[
        "neutral",
        "positive",
        "negative"
    ] = "neutral"
    repititive_issue_counter:int=0

    source_url:Optional[str]=None


class ChatRequest(BaseModel):
    message:str
    user_id:str
    conversation_id:str

class ChatResponse(BaseModel):
    response :str
    source:Optional[str]=None
    status:str="success"


    
