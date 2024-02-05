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

def store_memory(memory):
    def f(response):
        print(response)

        input = {"input":response["input"]}
        output = {"output": response["return_values"].return_values['output']}
        memory.save_context(input, output)
        return output
    
    return f

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