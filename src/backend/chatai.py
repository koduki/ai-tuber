import time
import os
from . import weather_tool
from . import short_talk_tool
from .lcel_operator import call_func
from .lcel_operator import store_memory
from .lcel_operator import to_json

from langchain.tools.render import format_tool_to_openai_function
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from operator import itemgetter

class ChatAI:

    def __init__(self, llm_model) -> None:
        self.use_llm(llm_model)
    
    def _mk_parser(self):
        # 出力フォーマットを定義
        from langchain_core.output_parsers import JsonOutputParser
        from langchain_core.pydantic_v1 import BaseModel, Field

        class Reply(BaseModel):
            current_emotion: str = Field(description="maxe")
            character_reply: str = Field(description="れん's reply to User")

        return JsonOutputParser(pydantic_object=Reply)
    
    def _mk_prompt4chat(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'prompt_system.txt')
        prompt_system = open(file_path, "r", encoding='utf-8').read()

        parser = self._mk_parser()

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_system),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="chat_history"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]).partial(format_instructions=parser.get_format_instructions())

        return prompt
        
    def use_llm(self, llm_model):
        self.llm_model = llm_model
        print("use model: " + llm_model)

        # モデルの準備
        from langchain_openai import ChatOpenAI
        from langchain_google_genai import ChatGoogleGenerativeAI

        if llm_model == 'gpt4':
            llm = ChatOpenAI(model_name="gpt-4", temperature=0)
        elif llm_model == 'gpt3':
            llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k", temperature=0)
        elif llm_model == 'gemini':
            llm = ChatGoogleGenerativeAI(model="gemini-pro", convert_system_message_to_human=True)
        else:
            llm = None

        # チェインを作成
        from langchain.memory import ConversationBufferWindowMemory
        memory = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True, k=20)
        prompt_for_tools = ChatPromptTemplate.from_messages([
            ("system", "You are agentai"),
            ("user", "{input}"),
        ])
        prompt_for_chat = self._mk_prompt4chat()

        tools = [weather_tool.weather_api, short_talk_tool.talk]

        llm_for_chat = ChatOpenAI(temperature=0, model='gpt-4-0613')
        llm_with_tools = ChatOpenAI(temperature=0, model='gpt-3.5-turbo').bind(functions=[format_tool_to_openai_function(t) for t in tools])

        rooter = (
            RunnablePassthrough().assign(
                chat_history=RunnableLambda(memory.load_memory_variables) | itemgetter("chat_history"),
                agent_scratchpad=prompt_for_tools | llm_with_tools | OpenAIFunctionsAgentOutputParser() | call_func(tools) | format_to_openai_functions
            )| RunnablePassthrough().assign(
                return_values=prompt_for_chat | llm_for_chat | OpenAIFunctionsAgentOutputParser(),
            )| store_memory(memory) | to_json
        )

        self.chat_chain = rooter

    #
    # methods
    #
    def _say(self, comment):
        import json

        print("start:llm")
        ls = time.perf_counter()
        msg = json.dumps(comment)
        res = self.chat_chain.invoke({"input":msg}) # {"speaker":c.author.name, "message":c.message}
        le = time.perf_counter()
        print("finish:llm response(sec): " + str(le - ls))
        print("res: " + str(res))

        return res

    def say_short_talk(self):
        msg = "「ちょっと小話でもしようかの」と言って、talk_contentsで400文字程度の雑談をしてください。その際にキャラクターらしさを含めた内容になるようにしてください。"

        return self._say({"speaker":"system", "message":msg})

    def say_chat(self, comment):
        return self._say(comment)

