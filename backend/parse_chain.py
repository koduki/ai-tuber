from langchain.chains import LLMChain
from langchain.chains.base import Chain
from typing import Dict, List

class ParseChain(Chain):
    chain: LLMChain
    
    @property
    def input_keys(self) -> List[str]:
        return ['input']
    
    @property
    def output_keys(self) -> List[str]:
        return ["current_emotion", "character_reply"]
        
    def _call(self, inputs: Dict[str, str]) -> Dict[str, str]:
        print("call")
        print(inputs)
        output = self.chain.invoke(inputs)
        print(output)

        import json
        text = str(output['text']).replace("'", "\"")
        data = json.loads(text)
        data["current_emotion"] = data["current_emotion"].split(":")[0]
        print("parsed: " + str(data))

        print("/call")
        return data