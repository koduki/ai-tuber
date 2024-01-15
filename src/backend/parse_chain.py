from langchain.chains import LLMChain
from langchain.chains.base import Chain
from typing import Dict, List, Any
import json

class ParseChain(Chain):
    chain: LLMChain

    def __init__(__pydantic_self__, **data: Any) -> None:
        if len(data) == 0:
            print("引数が渡されていません。テストコードとして実行します。")
        else:
            super().__init__(**data)
    
    @property
    def input_keys(self) -> List[str]:
        return ["speaker", "message"]
    
    @property
    def output_keys(self) -> List[str]:
        return ["current_emotion", "character_reply"]
        
    def _call(self, inputs: Dict[str, str]) -> Dict[str, str]:
        print("call")
        print(inputs)
        msg = json.dumps(inputs)
        output = self.chain.invoke(msg)
        print(output)

        data = self._parse(str(output['text']))
        print("parsed: " + str(data))

        print("/call")
        return data
    
    def _parse(self, text):
        import re

        # parse non-JSON format
        text = text.replace('\n', '')
        if "{" not in text and "}" not in text:
            text = f'{{"current_emotion": "fun", "character_reply": "{text}"}}'

        # parse include markdown
        json_str = re.search(r'```json(.*?)```', text, re.DOTALL)
        text = json_str.group(1) if json_str else text

        # parse quartation
        text = text.replace("'", "\"")

        # transform
        print(text)
        data = json.loads(text)

        # parse broken current_emotion format
        data["current_emotion"] = data["current_emotion"].split(":")[0]
        
        return data
    
if __name__ == "__main__":
    # GPT 3 may return broken JSON
    chain = ParseChain()
    text='```json\n{"current_emotion": "fun: 3", "character_reply": "あら、どこから 来たのじゃ？"}\n```'
    print(chain._parse(text))

    chain = ParseChain()
    text='よくきたのじゃ！わらわは紅月 れんと申すのじゃ。どうぞよろしくのじゃ♪'
    print(chain._parse(text))