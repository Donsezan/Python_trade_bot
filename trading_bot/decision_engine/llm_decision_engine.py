import openai
import google.generativeai as genai
from dashscope import Generation
from trading_bot.config import config
from trading_bot.interfaces import DecisionEngine as DecisionEngineInterface
from trading_bot.models import Decision
from typing import Dict, Any, List
import json
import re

class LLMDecisionEngine(DecisionEngineInterface):
    """Makes trading decisions using a multi-LLM debate."""

    def __init__(self):
        """Initialize the DecisionEngine and the LLM clients based on the config."""
        self.provider = config.get_llm_provider()
        llm_config_obj = config.get_llm_config()
        if isinstance(llm_config_obj, list):
             self.llm_config = {cfg['provider']: cfg for cfg in llm_config_obj}
        else:
             self.llm_config = llm_config_obj
        
        print(f"DEBUG: LLM Config: {self.llm_config}")


        if self.provider == 'openrouter':
            self.openai_model_name = self.llm_config.get("openai", {}).get("model_name")
            self.gemini_model_name = self.llm_config.get("gemini", {}).get("model_name")
            self.qwen_model_name = self.llm_config.get("qwen", {}).get("model_name")

            # For OpenRouter, we can use a generic client based on the OpenAI SDK
            openai_api_key = self.llm_config.get("openai", {}).get("api_key")
            if openai_api_key:
                self.llm_1 = openai.OpenAI(
                    base_url=self.llm_config.get("openai", {}).get("endpoint"),
                    api_key=openai_api_key
                )
            else:
                print("Warning: OpenAI API key not found. LLM 1 will not work.")
                self.llm_1 = None

            gemini_api_key = self.llm_config.get("gemini", {}).get("api_key")
            if gemini_api_key:
                self.llm_2 = openai.OpenAI(
                    base_url=self.llm_config.get("gemini", {}).get("endpoint"),
                    api_key=gemini_api_key
                )
            else:
                print("Warning: Gemini API key not found. LLM 2 will not work.")
                self.llm_2 = None

            qwen_api_key = self.llm_config.get("qwen", {}).get("api_key")
            if qwen_api_key:
                self.llm_3 = openai.OpenAI(
                    base_url=self.llm_config.get("qwen", {}).get("endpoint"),
                    api_key=qwen_api_key
                )
            else:
                print("Warning: Qwen API key not found. LLM 3 will not work.")
                self.llm_3 = None

        else:  # Native clients
            openai_api_key = self.llm_config.get("openai", {}).get("api_key")
            if openai_api_key:
                self.llm_1 = openai.OpenAI(api_key=openai_api_key)
            else:
                print("Warning: OpenAI API key not found. LLM 1 will not work.")
                self.llm_1 = None

            gemini_api_key = self.llm_config.get("gemini", {}).get("api_key")
            if gemini_api_key:
                genai.configure(api_key=gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
            else:
                print("Warning: Gemini API key not found. Gemini model will not work.")
                self.gemini_model = None

            self.qwen_api_key = self.llm_config.get("qwen", {}).get("api_key")

    def decide(self, context: Dict[str, Any]) -> Decision:
        """
        Make a trading decision by orchestrating a debate between multiple LLMs.
        """
        initial_prompt = self._build_initial_prompt(context)
        conversation_history = [{"role": "system", "content": "You are a trading expert. Analyze the data and debate the best action. Rate actions (BUY, SELL, HOLD, WAIT) on a 1-5 scale, where 1 is a strong no and 5 is a strong yes. Provide your reasoning."},
                                {"role": "user", "content": initial_prompt}]

        for _ in range(3): # 3 rounds of debate
            openai_response = self._get_openai_response(conversation_history)
            conversation_history.append({"role": "assistant", "name": "OpenAI", "content": openai_response})

            gemini_response = self._get_gemini_response(conversation_history)
            conversation_history.append({"role": "assistant", "name": "Gemini", "content": gemini_response})

            qwen_response = self._get_qwen_response(conversation_history)
            conversation_history.append({"role": "assistant", "name": "Qwen", "content": qwen_response})

        final_decision = self._parse_final_decision(conversation_history)
        return final_decision

    def _build_initial_prompt(self, context: Dict[str, Any]) -> str:
        """Build the initial prompt for the LLM debate."""
        news_str = "\n".join([f"- {n.get('title')}: {n.get('summary')}" for n in context.get("news", [])])
        return f"""
        Market Data:
        - Ticker: {context.get("ticker")}
        - Indicators: {context.get("indicators")}

        News:
        {news_str}

        Debate and decide on the next trading action.
        """

    def _get_openai_response(self, history: List[Dict]) -> str:
        """Get a response from the OpenAI model, either native or via OpenRouter."""
        try:
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
            model_name = self.openai_model_name if self.provider == 'openrouter' else "gpt-4-turbo"

            response = self.llm_1.chat.completions.create(model=model_name, messages=messages)
            return response.choices[0].message.content
        except Exception as e:
            return f"Error from OpenAI: {e}"

    def _get_gemini_response(self, history: List[Dict]) -> str:
        """Get a response from the Gemini model, either native or via OpenRouter."""
        try:
            if self.provider == 'openrouter':
                messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
                response = self.llm_2.chat.completions.create(model=self.gemini_model_name, messages=messages)
                return response.choices[0].message.content
            else:
                contents = [{"role": "user" if msg["role"] == "user" else "model", "parts": [{"text": msg["content"]}]} for msg in history]
                response = self.gemini_model.generate_content(contents)
                return response.text
        except Exception as e:
            return f"Error from Gemini: {e}"

    def _get_qwen_response(self, history: List[Dict]) -> str:
        """Get a response from the Qwen model, either native or via OpenRouter."""
        try:
            if self.provider == 'openrouter':
                messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
                response = self.llm_3.chat.completions.create(model=self.qwen_model_name, messages=messages)
                return response.choices[0].message.content
            else:
                messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
                response = Generation.call(model="qwen-turbo", messages=messages, api_key=self.qwen_api_key)
                return response.output.text
        except Exception as e:
            return f"Error from Qwen: {e}"

    def _parse_final_decision(self, history: List[Dict]) -> Decision:
        """Parse the conversation history to make a final decision."""
        scores = {"BUY": [], "SELL": [], "HOLD": [], "WAIT": []}
        for msg in history:
            if msg["role"] == "assistant":
                text = msg["content"].upper()
                for action in scores:
                    # Simple regex to find "ACTION: SCORE"
                    match = re.search(f"{action}:\\s*(\\d)", text)
                    if match:
                        scores[action].append(int(match.group(1)))

        avg_scores = {action: sum(s) / len(s) if s else 0 for action, s in scores.items()}
        best_action = max(avg_scores, key=avg_scores.get)

        return Decision(
            action=best_action,
            symbol="BTC/USDT",
            size=0.01, # Simplified size for now
            reason=f"Based on LLM debate. Average scores: {avg_scores}",
            confidence=avg_scores[best_action] / 5.0
        )

decision_engine = LLMDecisionEngine()
