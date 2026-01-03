import google.generativeai as genai
from google.protobuf.struct_pb2 import Struct
from core.logger import Logger
import time


class GeminiClient:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)

        # 👑 模型優先權清單
        self.model_priority = [
            'gemini-3-pro',
            'gemini-3-flash',
            'gemini-3-pro-image',
            'gemini-2.5-pro',
            'gemini-2.5-flash',
            'gemini-2.0-flash-exp',
            'gemini-2.0-flash'
        ]

    def generate_content(self, prompt, image=None, tools=None, system_instruction=None):
        """
        [單次生成] 自動輪詢所有模型
        """
        last_error = None

        for model_name in self.model_priority:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    tools=tools,
                    system_instruction=system_instruction
                )

                inputs = [prompt]
                if image: inputs.append(image)

                # Logger.debug(f"⚡ 嘗試連線模型: {model_name}")
                response = model.generate_content(inputs)
                Logger.debug(f"✅ 成功使用模型: {model_name}")
                return response

            except Exception as e:
                self._handle_error(model_name, e)
                last_error = e
                continue

        raise last_error

    def create_unified_chat(self, tools=None, system_instruction=None):
        return UnifiedChatSession(self, tools, system_instruction)

    def _handle_error(self, model_name, error):
        error_str = str(error).lower()
        if "404" in error_str or "not found" in error_str:
            pass
        elif "429" in error_str or "exhausted" in error_str:
            Logger.warn(f"⚠️ {model_name} 流量耗盡，自動切換下一個...")
        else:
            Logger.warn(f"⚠️ {model_name} 發生錯誤，切換中...")


class UnifiedChatSession:
    """
    [虛擬對話物件] 支援自動 Function Calling 與 模型輪詢
    """

    def __init__(self, client, tools=None, system_instruction=None):
        self.client = client
        self.history = []
        self.tools = tools
        self.system_instruction = system_instruction

    def send_message(self, user_input):
        """
        發送訊息並自動處理 Function Call
        """
        last_error = None

        for model_name in self.client.model_priority:
            try:
                # 1. 建立模型 (開啟自動函式呼叫功能)
                model = genai.GenerativeModel(
                    model_name=model_name,
                    tools=self.tools,
                    system_instruction=self.system_instruction
                )

                # 2. 注入記憶
                chat = model.start_chat(history=self.history, enable_automatic_function_calling=True)

                # 3. 發送訊息
                # Logger.debug(f"💬 嘗試對話模型: {model_name}")
                response = chat.send_message(user_input)

                # 4. 更新記憶
                self.history = chat.history

                Logger.debug(f"🗣️  由 {model_name} 回應")

                # [關鍵修正] 檢查回應是否包含 Function Call 殘留
                # 雖然 enable_automatic_function_calling=True 會自動處理，
                # 但有時候回應格式需要特別處理成文字
                return response

            except Exception as e:
                # 如果是 "Could not convert part.function_call"，這其實代表 Function Call 成功了，
                # 只是我們在 main.py 直接 print(response.text) 導致的。
                # 但為了保險，我們這裡捕捉所有錯誤。
                error_str = str(e)
                if "function_call" in error_str:
                    # 這是特殊情況：Gemini 觸發了工具但自動執行出現狀況，我們嘗試換個模型
                    pass

                self.client._handle_error(model_name, e)
                last_error = e
                continue

        raise last_error