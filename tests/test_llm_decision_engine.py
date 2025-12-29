
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure the project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from trading_bot.decision_engine.llm_decision_engine import LLMDecisionEngine

class TestLLMDecisionEngine(unittest.TestCase):
    
    @patch('trading_bot.decision_engine.llm_decision_engine.config')
    @patch('trading_bot.decision_engine.llm_decision_engine.openai')
    @patch('trading_bot.decision_engine.llm_decision_engine.genai')
    def test_init_openrouter_llms(self, mock_genai, mock_openai, mock_config):
        """Test initialization with openrouter_llms provider."""
        
        # Setup config mock
        mock_config.get_llm_provider.return_value = 'openrouter_llms'
        mock_config.get_llm_config.return_value = {
            'openai': {'api_key': 'key1', 'model_name': 'gpt-3.5'},
            'gemini': {'api_key': 'key2', 'model_name': 'gemini-pro'},
            'qwen': {'api_key': 'key3', 'model_name': 'qwen-turbo'}
        }
        
        # Initialize
        engine = LLMDecisionEngine()
        
        # Verify provider
        self.assertEqual(engine.provider, 'openrouter_llms')
        
        # Verify OpenAI client calls
        # We expect 3 calls to openai.OpenAI (llm_1, llm_2, llm_3)
        self.assertEqual(mock_openai.OpenAI.call_count, 3)
        
        # Verify base_url for each
        calls = mock_openai.OpenAI.call_args_list
        # Check call arguments. We expect base_url='https://openrouter.ai/api/v1' for all if not provided
        for call in calls:
            kwargs = call.kwargs
            self.assertEqual(kwargs.get('base_url'), 'https://openrouter.ai/api/v1')

    @patch('trading_bot.decision_engine.llm_decision_engine.config')
    @patch('trading_bot.decision_engine.llm_decision_engine.openai')
    @patch('trading_bot.decision_engine.llm_decision_engine.genai')
    def test_init_native_llms(self, mock_genai, mock_openai, mock_config):
        """Test initialization with native_llms provider."""
        
        # Setup config mock
        mock_config.get_llm_provider.return_value = 'native_llms'
        mock_config.get_llm_config.return_value = {
            'openai': {'api_key': 'key1', 'model_name': 'gpt-3.5'},
            'gemini': {'api_key': 'key2', 'model_name': 'gemini-pro'},
            # Qwen without endpoint -> Native
            'qwen': {'api_key': 'key3', 'model_name': 'qwen-turbo'}
        }
        
        # Initialize
        engine = LLMDecisionEngine()
        
        # Verify provider
        self.assertEqual(engine.provider, 'native_llms')
        
        # Verify OpenAI client calls
        # Only llm_1 (OpenAI) should use openai.OpenAI
        # verify llm_2 (Gemini) uses genai
        # verify llm_3 (Qwen) uses None for openai client (falls back to native in `decide` if impl supports it, 
        # but in init llm_3 is None if no endpoint provided for native/qwen)
        
        # llm_1 should be initialized with OpenAI
        # We check calls to openai.OpenAI
        # Expected: 1 call for llm_1 (OpenAI)
        # Note: In native mode, if gemini/qwen don't have endpoint, they don't use OpenAI client.
        
        openai_calls = [c for c in mock_openai.OpenAI.call_args_list]
        self.assertEqual(len(openai_calls), 1, f"Expected 1 OpenAI call, got {len(openai_calls)}")
        
        # Verify GenAI configuration for Gemini
        mock_genai.configure.assert_called_with(api_key='key2')
        mock_genai.GenerativeModel.assert_called_with('gemini-pro')
        
    @patch('trading_bot.decision_engine.llm_decision_engine.config')
    @patch('trading_bot.decision_engine.llm_decision_engine.openai')
    def test_init_openrouter_custom_endpoint(self, mock_openai, mock_config):
        """Test openrouter with custom endpoint overridden."""
        mock_config.get_llm_provider.return_value = 'openrouter_llms'
        mock_config.get_llm_config.return_value = {
            'openai': {'api_key': 'key1', 'endpoint': 'https://custom.endpoint'},
        }
        
        engine = LLMDecisionEngine()
        
        # OpenAI should use custom endpoint
        mock_openai.OpenAI.assert_called_with(base_url='https://custom.endpoint', api_key='key1')

    @patch('trading_bot.decision_engine.llm_decision_engine.config')
    @patch('trading_bot.decision_engine.llm_decision_engine.openai')
    def test_decide_json_parsing(self, mock_openai, mock_config):
        """Test decide method with JSON responses."""
        
        # Setup config
        mock_config.get_llm_provider.return_value = 'openrouter_llms'
        mock_config.get_llm_config.return_value = {
            'openai': {'api_key': 'k1'},
            'gemini': {'api_key': 'k2'},
            'qwen': {'api_key': 'k3'}
        }

        # Setup mocks for LLM responses
        # We simulate 3 rounds of debate for 3 LLMs = 9 calls max, but since we mock the clients separately or same?
        # In init_openrouter_llms, it creates 3 separate OpenAI instances.
        
        # Mock instance
        mock_client_instance = MagicMock()
        mock_openai.OpenAI.return_value = mock_client_instance
        
        # Mock completions
        # We need a sequence of side_effects for the format:
        # Round 1: OpenAI, Gemini, Qwen
        # Round 2: ...
        # Round 3: ...
        
        # Successful JSON responses
        response_btc_buy = '{"Decision": "BUY", "Rating": 5, "Thinking": "Strong buy logic"}'
        response_btc_hold = '{"Decision": "HOLD", "Rating": 3, "Thinking": "Uncertain"}'
        response_btc_sell = '{"Decision": "SELL", "Rating": 4, "Thinking": "Bearish"}'
        
        # Mock the return value structure
        mock_message = MagicMock()
        mock_message.content = response_btc_buy
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        # Simpler approach: side_effect for create
        def side_effect(*args, **kwargs):
            # Return different decisions based on some logic or just cycle
            # For simplicity, let's make them all return valid JSON
            resp = MagicMock()
            resp.choices[0].message.content = '{"Decision": "BUY", "Rating": 4.5, "Thinking": "Consensus buy"}'
            return resp

        mock_client_instance.chat.completions.create.side_effect = side_effect
        
        engine = LLMDecisionEngine()
        context = {"ticker": "BTC/USDT", "indicators": {}, "news": []}
        
        decision = engine.decide(context)
        
        self.assertEqual(decision.action, "BUY")
        self.assertEqual(decision.confidence, 4.5/5.0)
        self.assertIn("Votes", decision.reason)

    @patch('trading_bot.decision_engine.llm_decision_engine.config')
    @patch('trading_bot.decision_engine.llm_decision_engine.openai')
    def test_decide_json_parsing_resilience(self, mock_openai, mock_config):
        """Test decide method resilience to markdown blocks and mixed content."""
        
        mock_config.get_llm_provider.return_value = 'openrouter_llms'
        mock_config.get_llm_config.return_value = {'openai': {'api_key': 'k1'}}
        
        mock_client_instance = MagicMock()
        mock_openai.OpenAI.return_value = mock_client_instance
        
        # Return a response with markdown code blocks
        markdown_response = 'Here is the JSON:\n```json\n{"Decision": "SELL", "Rating": 5, "Thinking": "Dump it"}\n```'
        
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = markdown_response
        mock_client_instance.chat.completions.create.return_value = mock_resp
        
        engine = LLMDecisionEngine()
        # Mock only 1 LLM enabled effectively for this simpler test, 
        # but the engine tries to init all.
        # Just override the other llms to None manually or let them fail gracefully if not configured 
        # (initial test setup provides only openai config, so others are None and will return Errors)
        
        # If others are None, they return "Error...". The parser handles them logging warnings but skipping.
        # OpenAI one returns the SELL decision.
        
        context = {"ticker": "BTC/USDT", "indicators": {}, "news": []}
        decision = engine.decide(context)
        
        self.assertEqual(decision.action, "SELL")
        self.assertEqual(decision.confidence, 1.0) # 5/5

if __name__ == '__main__':
    unittest.main()
