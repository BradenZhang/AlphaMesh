from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.services.llm.schemas import LLMMessage


def to_langchain_messages(messages: list[LLMMessage]) -> list[BaseMessage]:
    mapped: list[BaseMessage] = []
    for message in messages:
        if message.role == "system":
            mapped.append(SystemMessage(content=message.content))
        elif message.role == "assistant":
            mapped.append(AIMessage(content=message.content))
        else:
            mapped.append(HumanMessage(content=message.content))
    return mapped
