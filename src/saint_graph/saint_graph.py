import copy
import json
import asyncio
from typing import List, Optional

from google.genai import types
from google.adk.models import Gemini
from google.adk.models.llm_request import LlmRequest

from .config import logger, MODEL_NAME, HISTORY_LIMIT
from .mcp_client import MCPClient

class SaintGraph:
    def __init__(self, mcp_client: MCPClient, system_instruction: str, tools: List[types.Tool], model: Optional[Gemini] = None):
        self.client = mcp_client
        self.model = model or Gemini(model=MODEL_NAME)
        self.chat_history: List[types.Content] = []

        # テンプレートリクエストを作成
        self.base_request = LlmRequest(
            model=MODEL_NAME,
            contents=[],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=tools,
                temperature=1.0,
            )
        )
        logger.info(f"SaintGraph initialized with model {MODEL_NAME}")

    def add_history(self, content: types.Content):
        """チャット履歴に追加し、制限を超えたら古いものを削除します。"""
        self.chat_history.append(content)
        if len(self.chat_history) > HISTORY_LIMIT:
            self.chat_history = self.chat_history[-HISTORY_LIMIT:]

    async def process_turn(self, user_input: str):
        """
        1回の対話ターン（Inner Loop）を処理します。
        ユーザー入力 -> モデル生成 -> (ツール実行 -> モデル生成)* -> 終了
        """
        logger.info(f"Turn started. Input: {user_input[:30]}...")

        # ユーザー入力を履歴に追加
        self.add_history(types.Content(role="user", parts=[types.Part(text=user_input)]))

        # ベースリクエストをコピーして現在の履歴をセット
        llm_request = copy.deepcopy(self.base_request)
        llm_request.contents = self.chat_history

        # Inner Loop (モデルとの往復)
        while True:
            # 内部ループのたびにリクエストをコピー (更新された履歴を反映するため)
            req = copy.deepcopy(llm_request)

            # ストリーミング受信と蓄積
            final_content = await self._generate_and_accumulate(req)

            if final_content is None or not getattr(final_content, "parts", None):
                logger.warning("Empty or missing final response from model; aborting this Inner Loop.")
                break

            # SaintGraphの応答を履歴に追加
            self.add_history(final_content)

            # 関数呼び出しの確認
            fcs = [p.function_call for p in final_content.parts if getattr(p, "function_call", None)]
            if not fcs:
                break # ツール呼び出しがなければこのターンは終了

            # ツール実行
            tool_results = await self._execute_tools(fcs)

            # ツール結果を履歴に追加して次のループへ
            self.add_history(types.Content(role="user", parts=tool_results))

            # リクエストのコンテンツを更新
            llm_request.contents = self.chat_history

    async def _generate_and_accumulate(self, req: LlmRequest) -> Optional[types.Content]:
        """モデルからストリーミング生成を行い、結果を蓄積して返します。"""
        accum_parts = []
        accum_text = ""
        printed_len = 0
        final_content = None

        try:
            async for chunk in self.model.generate_content_async(req, stream=True):
                # エラーチェック
                error_code = getattr(chunk, 'error_code', None)
                if error_code:
                    error_msg = getattr(chunk, 'error_message', 'Unknown error')
                    logger.error(f"LLM Error: {error_code} - {error_msg}")
                    return None
                
                if getattr(chunk, "content", None) and getattr(chunk.content, "parts", None):
                    for p in chunk.content.parts:
                        accum_parts.append(p)
                        if getattr(p, "text", None):
                            accum_text += p.text

                # ログ出力 (増分のみ)
                if len(accum_text) > printed_len:
                    logger.info(f"Gemini: {accum_text[printed_len:]}")
                    printed_len = len(accum_text)

                # ストリーム完了判定
                if not getattr(chunk, "partial", False):
                    final_content = types.Content(role="assistant", parts=accum_parts)
                    break
        except Exception as e:
            logger.error(f"Error during LLM generation: {e}", exc_info=True)
            return None

        return final_content

    async def _execute_tools(self, fcs: List[types.FunctionCall]) -> List[types.Part]:
        """関数呼び出しを実行し、結果をPartのリストとして返します。"""
        tool_results = []
        for fc in fcs:
            logger.info(f"ACTION: {fc.name}({fc.args})")
            args = fc.args
            # 引数の正規化
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    pass # JSONでなければそのまま

            # Use standardized call_tool method
            try:
                res = await self.client.call_tool(fc.name, args or {})
                tool_results.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=fc.name,
                            response={"result": str(res)}
                        )
                    )
                )
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                tool_results.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=fc.name,
                            response={"error": str(e)}
                        )
                    )
                )
        return tool_results
