import time
import os
from .parse_chain import ParseChain
from . import weather_tool
from . import short_talk_tool

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
        # テンプレートとプロンプトエンジニアリング
        from langchain.prompts import (
            ChatPromptTemplate,
            HumanMessagePromptTemplate,
            SystemMessagePromptTemplate,
            MessagesPlaceholder,
        )

        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'prompt_system.txt')
        prompt_system = open(file_path, "r", encoding='utf-8').read()

        parser = self._mk_parser()
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(prompt_system),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            HumanMessagePromptTemplate.from_template("{input}"), 
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
        prompt = self._mk_prompt4chat()
        tools = [weather_tool.weather_api, short_talk_tool.talk]

        from langchain.agents import AgentExecutor, create_openai_tools_agent
        agent = create_openai_tools_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, verbose=True, tools=tools, memory=memory, max_iterations=3)

        self.chat_chain = ParseChain(chain=agent_executor, verbose=False)

    #
    # methods
    #
    def _say(self, comment):
        print("start:llm")
        ls = time.perf_counter()
        res = self.chat_chain.invoke(comment) # {"speaker":c.author.name, "message":c.message}
        le = time.perf_counter()
        print("finish:llm response(sec): " + str(le - ls))
        print("res: " + str(res))

        return res

    def say_short_talk(self):
        msg = "「ちょっと小話でもしようかの」と言って、talk_contentsで400文字程度の雑談をしてください。その際にキャラクターらしさを含めた内容になるようにしてください。"

        return self._say({"speaker":"system", "message":msg})

    def say_chat(self, comment):
        return self._say(comment)

