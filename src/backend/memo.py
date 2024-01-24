
import backend.weather_tool
tools = [backend.weather_tool.weather_api]

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI

import os
import sys

os.environ["OPENAI_API_KEY"] = open(f"{os.environ['HOMEPATH']}\\.secret\\openai.txt", "r").read()

from langchain.memory import ConversationBufferWindowMemory
memory = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True, k=20)
llm = ChatOpenAI(model="gpt-4", temperature=0)

from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
)

# 出力フォーマットを定義
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

class Reply(BaseModel):
    current_emotion: str = Field(description="maxe")
    character_reply: str = Field(description="れん's reply to User")

parser = JsonOutputParser(pydantic_object=Reply)

# テンプレートとプロンプトエンジニアリング
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
)
prompt_system = open("backend\\prompt_system.txt", "r", encoding='utf-8').read()

prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(prompt_system),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
    HumanMessagePromptTemplate.from_template("{input}"), 
]).partial(format_instructions=parser.get_format_instructions())


from langchain.agents import AgentExecutor, create_openai_tools_agent
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, verbose=True, tools=tools, memory=memory)

agent_executor.invoke({"input": "どこに住んでるの？"})
agent_executor.invoke({"input": "今日の天気は？"})
agent_executor.invoke({"input": "明日のアメリカは？"})

