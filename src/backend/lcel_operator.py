from langchain.schema.agent import AgentFinish

def call_func(tools):
    def f(log):
        if isinstance(log, AgentFinish):
            return [(log, [])]
        else:
            tool = next(x for x in tools if x.name == log.tool)
            observation = tool.run(log.tool_input)
            return [(log, observation)]
        
    return f

def _format_messges(messages):
    import json

    rs = []
    for message in messages:
        content = json.loads(message.content)
        
        # HumanMessageの処理
        if "speaker" in content and "message" in content:
            rs.append({'speaker': content['speaker'], 'message': content['message']})
        
        # AIMessageの処理
        elif "current_emotion" in content and "character_reply" in content:
            rs.append({
                'speaker': "ai", 
                'message': content['character_reply'],
                'emotion': content['current_emotion']
            })

    return str(rs)

def _parse2json(json_text):
    import json
    import re

    try:
        text = json_text
        # parse non-JSON format
        if "{" not in text and "}" not in text:
            text = f'{{"current_emotion": "fun", "character_reply": "{text}"}}'

        # parse include markdown
        json_str = re.search(r'```json(.*?)```', text, re.DOTALL)
        text = json_str.group(1) if json_str else text

        # parse quartation
        text = text.replace("'", "\"")

        # transform and remove duplicate
        #print(text)
        split_output = text.split('\n')
        unique_output = []
        for item in split_output:
            item_json = json.loads(item)
            if item_json not in unique_output:
                unique_output.append(item_json)

        data = unique_output[0]

        # parse broken current_emotion format
        data["current_emotion"] = data["current_emotion"].split(":")[0]

        return json.dumps(data)
    except:
        print("parse error(reply): raw=" + json_text + " , parsed=" + text)
        return json.dumps({"current_emotion": "fun", "character_reply": "すまぬ。上手く応えられぬ。"})

def store_memory(memory):
    def f(response):
        # print(response)
        print("raw_output: " + str(response["return_values"].return_values['output']))
        print("history: " + _format_messges(response['chat_history']))

        input = {"input":response["input"]}
        output = {"output": _parse2json(response["return_values"].return_values['output'])}

        memory.save_context(input, output)
        return output
    
    return f

def to_json(response):
    import json

    return json.loads(response['output'])