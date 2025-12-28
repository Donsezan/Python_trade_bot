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

        # Model Names
        self.openai_model_name = self.llm_config.get("openai", {}).get("model_name")
        self.gemini_model_name = self.llm_config.get("gemini", {}).get("model_name")
        self.qwen_model_name = self.llm_config.get("qwen", {}).get("model_name")

        # Initialize LLM 1 (OpenAI Role)
        # Supports: Native (OpenAI), OpenRouter (OpenAI-compatible)
        openai_conf = self.llm_config.get("openai", {})
        openai_api_key = openai_conf.get("api_key")
        if openai_api_key:
            base_url = openai_conf.get("endpoint") or openai_conf.get("base_url")
            if self.provider == 'openrouter_llms' and not base_url:
                base_url = "https://openrouter.ai/api/v1"
            
            self.llm_1 = openai.OpenAI(
                base_url=base_url,
                api_key=openai_api_key
            )
        else:
            print("Warning: OpenAI API key not found. LLM 1 will not work.")
            self.llm_1 = None

        # Initialize LLM 2 (Gemini Role)
        # Supports: Native (OpenAI-compatible/Local), Google GenAI, OpenRouter (OpenAI-compatible)
        gemini_conf = self.llm_config.get("gemini", {})
        gemini_api_key = gemini_conf.get("api_key")
        self.llm_2 = None
        self.gemini_model = None
        
        if gemini_api_key:
            endpoint = gemini_conf.get("endpoint") or gemini_conf.get("base_url")
            
            if self.provider == 'openrouter_llms':
                 base_url = endpoint or "https://openrouter.ai/api/v1"
                 self.llm_2 = openai.OpenAI(
                    base_url=base_url,
                    api_key=gemini_api_key
                )
            elif endpoint:
                # User provided specific endpoint (e.g. local or proxy), treat as OpenAI compatible
                self.llm_2 = openai.OpenAI(
                    base_url=endpoint,
                    api_key=gemini_api_key
                )
            else:
                # Native or native_llms without endpoint -> Use Google GenAI
                genai.configure(api_key=gemini_api_key)
                self.gemini_model = genai.GenerativeModel(self.gemini_model_name or 'gemini-pro')
        else:
            print("Warning: Gemini API key not found. LLM 2 will not work.")

        # Initialize LLM 3 (Qwen Role)
        # Supports: Native (OpenAI-compatible/Local), Dashscope, OpenRouter (OpenAI-compatible)
        qwen_conf = self.llm_config.get("qwen", {})
        self.qwen_api_key = qwen_conf.get("api_key")
        self.llm_3 = None

        if self.qwen_api_key:
            endpoint = qwen_conf.get("endpoint") or qwen_conf.get("base_url")
            
            if self.provider == 'openrouter_llms':
                 base_url = endpoint or "https://openrouter.ai/api/v1"
                 self.llm_3 = openai.OpenAI(
                    base_url=base_url,
                    api_key=self.qwen_api_key
                )
            elif endpoint:
                 self.llm_3 = openai.OpenAI(
                    base_url=endpoint,
                    api_key=self.qwen_api_key
                )
            # Else falls back to self.qwen_api_key usage in _get_qwen_response for native dashscope
        else:
            print("Warning: Qwen API key not found. LLM 3 will not work.")

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
        """Get a response from the OpenAI model."""
        try:
            if not self.llm_1:
                return "Error: OpenAI client not initialized."
                
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
            # Use configured model name or default
            model_name = self.openai_model_name or "gpt-3.5-turbo"

            response = self.llm_1.chat.completions.create(model=model_name, messages=messages)
            return response.choices[0].message.content
        except Exception as e:
            return f"Error from OpenAI: {e}"

    def _get_gemini_response(self, history: List[Dict]) -> str:
        """Get a response from the Gemini model."""
        try:
            if self.llm_2: # OpenAI Compatible
                messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
                model_name = self.gemini_model_name or "gemini-pro"
                response = self.llm_2.chat.completions.create(model=model_name, messages=messages)
                return response.choices[0].message.content
            elif self.gemini_model: # Google GenAI Native
                contents = [{"role": "user" if msg["role"] == "user" else "model", "parts": [{"text": msg["content"]}]} for msg in history]
                response = self.gemini_model.generate_content(contents)
                return response.text
            else:
                 return "Error: Gemini client not initialized."
        except Exception as e:
            return f"Error from Gemini: {e}"

    def _get_qwen_response(self, history: List[Dict]) -> str:
        """Get a response from the Qwen model."""
        try:
            if self.llm_3: # OpenAI Compatible
                messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
                model_name = self.qwen_model_name or "qwen-turbo"
                response = self.llm_3.chat.completions.create(model=model_name, messages=messages)
                return response.choices[0].message.content
            elif self.qwen_api_key: # Dashscope Native
                messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
                # Fallback to dashscope if no openai client for Qwen
                response = Generation.call(model="qwen-turbo", messages=messages, api_key=self.qwen_api_key)
                return response.output.text
            else:
                return "Error: Qwen client not initialized."
        except Exception as e:
            return f"Error from Qwen: {e}"

    def _parse_final_decision(self, history: List[Dict]) -> Decision:
        """
        Parse the conversation history to make a final decision.
        Considers only the final (last) response of each LLM.
        """
        # 1. Identify the last response from each distinct LLM
        last_responses = {}
        for msg in history:
            if msg["role"] == "assistant":
                # Use 'name' to distinguish LLMs (OpenAI, Gemini, Qwen)
                name = msg.get("name", "Unknown")
                last_responses[name] = msg["content"]
        
        scores = {"BUY": [], "SELL": [], "HOLD": [], "WAIT": []}
        
        # Regex to find "Final Decision: ACTION (Rating: SCORE/5)" patterns
        # Robust enough to handle "**Final Verdict:** **HOLD (4/5)**" and variations
        regex = r"Final\s*(?:Decision|Verdict).*?[:\s]+\**\s*(BUY|SELL|HOLD|WAIT)\**.*?[(\[]?(?:Rating\s*:?)?\s*(\d+(?:\.\d+)?)\s*/\s*5"

        for llm_name, content in last_responses.items():
            # Find all matches, but we prioritize the LAST match in the text
            # as it represents the "Final" conclusion of the LLM
            matches = re.findall(regex, content, re.IGNORECASE | re.DOTALL)
            
            if matches:
                # Take the last match found in the response
                action, rating = matches[-1]
                action = action.upper()
                rating = float(rating)
                
                # Check if action is valid (regex should ensure this, but double check)
                if action in scores:
                    scores[action].append(rating)
                print(f"DEBUG: Parsed {llm_name} -> Action: {action}, Rating: {rating}")
            else:
                print(f"WARNING: Could not parse Final Decision from {llm_name}")

        # 2. Aggregate scores
        # We calculate the total score for each action to determine the winner
        # (Frequency * Strength) logic
        total_scores = {action: sum(s) for action, s in scores.items()}
        
        # Determine best action
        # If no scores recorded, default to WAIT
        if not any(total_scores.values()):
            return Decision(
                action="WAIT",
                symbol="BTC/USDT",
                size=0.01,
                reason="Failed to parse any valid decisions from LLMs.",
                confidence=0.0
            )

        best_action = max(total_scores, key=total_scores.get)
        
        # Calculate confidence based on the average rating of the winning action
        winning_ratings = scores[best_action]
        avg_rating = sum(winning_ratings) / len(winning_ratings) if winning_ratings else 0
        confidence = avg_rating / 5.0

        return Decision(
            action=best_action,
            symbol="BTC/USDT",
            size=0.01, # Simplified size for now
            reason=f"Based on LLM debate. Votes: {dict(scores)}. Totals: {total_scores}",
            confidence=confidence
        )

decision_engine = LLMDecisionEngine()
