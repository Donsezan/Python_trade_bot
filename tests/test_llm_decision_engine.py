
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

if __name__ == '__main__':
    unittest.main()
