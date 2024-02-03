import time
import os
from .parse_chain import ParseChain
from . import weather_tool
from . import short_talk_tool

from langchain.schema.agent import AgentFinish
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

        llm = ChatOpenAI(temperature=0, model='gpt-4-0613')
        llm_with_tools = ChatOpenAI(temperature=0, model='gpt-3.5-turbo').bind(functions=[format_tool_to_openai_function(t) for t in tools])

        def call_func(log):
            if isinstance(log, AgentFinish):
                return [(log, [])]
            else:
                tool = next(x for x in tools if x.name == log.tool)
                observation = tool.run(log.tool_input)
                return [(log, observation)]

        def store_memory(response):
            print(response)

            input = {"input":response["input"]}
            output = {"output": response["return_values"].return_values['output']}
            memory.save_context(input, output)
            return output
        
        def to_json(response):
            import json
            import re
            text = response['output']

            # parse non-JSON format
            if "{" not in text and "}" not in text:
                text = f'{{"current_emotion": "fun", "character_reply": "{text}"}}'

            # parse include markdown
            json_str = re.search(r'```json(.*?)```', text, re.DOTALL)
            text = json_str.group(1) if json_str else text

            # parse quartation
            text = text.replace("'", "\"")

            # transform and remove duplicate
            print(text)
            split_output = text.split('\n')
            unique_output = []
            for item in split_output:
                item_json = json.loads(item)
                if item_json not in unique_output:
                    unique_output.append(item_json)

            data = unique_output[0]

            # parse broken current_emotion format
            data["current_emotion"] = data["current_emotion"].split(":")[0]

            return data

        agent = (
            RunnablePassthrough().assign(
                chat_history=RunnableLambda(memory.load_memory_variables) | itemgetter("chat_history"),
                agent_scratchpad=prompt_for_tools | llm_with_tools | OpenAIFunctionsAgentOutputParser() | call_func | format_to_openai_functions
            )| RunnablePassthrough().assign(
                return_values=prompt_for_chat | llm | OpenAIFunctionsAgentOutputParser(),
            )| store_memory | to_json
        )

        self.chat_chain = agent

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

