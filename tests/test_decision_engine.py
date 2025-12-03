import unittest
from unittest.mock import MagicMock, patch
import os
import sys


# Add the parent directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import trading_bot.decision_engine.llm_decision_engine

class TestLLMDecisionEngine(unittest.TestCase):
    def setUp(self):
        # Set config path to test config
        os.environ['CONFIG_PATH'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.test.yaml'))

        # Mock config to return native provider
        self.config_patcher = patch('trading_bot.decision_engine.llm_decision_engine.config')
        self.mock_config = self.config_patcher.start()
        self.mock_config.get_llm_provider.return_value = 'native'
        self.mock_config.get_llm_config.return_value = {
            'openai': {'api_key': 'dummy', 'model_name': 'gpt-4'},
            'gemini': {'api_key': 'dummy', 'model_name': 'gemini-pro'},
            'qwen': {'api_key': 'dummy', 'model_name': 'qwen-turbo'}
        }
        
        # Mock LLM clients
        self.openai_patcher = patch('trading_bot.decision_engine.llm_decision_engine.openai')
        self.genai_patcher = patch('trading_bot.decision_engine.llm_decision_engine.genai')
        self.dashscope_patcher = patch('trading_bot.decision_engine.llm_decision_engine.Generation')
        
        self.mock_openai = self.openai_patcher.start()
        self.mock_genai = self.genai_patcher.start()
        self.mock_dashscope = self.dashscope_patcher.start()
        
        from trading_bot.decision_engine.llm_decision_engine import LLMDecisionEngine
        self.engine = LLMDecisionEngine()

    def tearDown(self):
        self.config_patcher.stop()
        self.openai_patcher.stop()
        self.genai_patcher.stop()
        self.dashscope_patcher.stop()

    def test_decide_flow(self):
        """Test the full decision flow with mocked LLM responses."""
        context = {
            "ticker": {"last": 50000},
            "indicators": {"rsi": 30},
            "news": []
        }
        
        # Mock responses to simulate a debate leading to a BUY decision
        # Round 1
        self.mock_openai.OpenAI.return_value.chat.completions.create.return_value.choices[0].message.content = "I think we should BUY: 4. The RSI is low."
        self.mock_genai.GenerativeModel.return_value.generate_content.return_value.text = "I agree, BUY: 5. Market is oversold."
        self.mock_dashscope.call.return_value.output.text = "Cautious but positive. BUY: 3."
        
        # We need to handle multiple calls if we want different responses per round, 
        # but for now constant responses are enough to test parsing.
        
        from trading_bot.models import Decision
        decision = self.engine.decide(context)
        
        self.assertIsInstance(decision, Decision)
        self.assertEqual(decision.action, "BUY")
        self.assertGreater(decision.confidence, 0)
        
        # Verify interactions
        # OpenAI called 3 times (3 rounds)
        self.assertEqual(self.mock_openai.OpenAI.return_value.chat.completions.create.call_count, 3)

    def test_parse_final_decision_regex(self):
        """Test the regex parsing logic specifically."""
        history = [
            {"role": "assistant", "content": "Analysis: Strong buy signal. BUY: 5. SELL: 1."},
            {"role": "assistant", "content": "I disagree. Market is volatile. HOLD: 5. BUY: 2."},
            {"role": "assistant", "content": "Neutral stance. WAIT: 5. BUY: 3."}
        ]
        
        # Scores:
        # BUY: 5, 2, 3 -> Avg: 3.33
        # SELL: 1 -> Avg: 1
        # HOLD: 5 -> Avg: 5
        # WAIT: 5 -> Avg: 5
        
        # Wait, the logic is:
        # scores[action].append(int(match.group(1)))
        # It finds the FIRST match for each action in the text.
        
        decision = self.engine._parse_final_decision(history)
        
        # HOLD and WAIT both have avg 5. max() will pick one (usually the first one encountered in iteration order or stable sort).
        # In the code: `best_action = max(avg_scores, key=avg_scores.get)`
        # avg_scores keys order depends on dict insertion order (Python 3.7+).
        # scores keys are initialized: BUY, SELL, HOLD, WAIT.
        # So max will pick the first one if values are equal? No, max returns the first one if multiple are maximal.
        # If HOLD and WAIT are both 5.
        
        self.assertIn(decision.action, ["HOLD", "WAIT"])
        self.assertEqual(decision.confidence, 1.0) # 5/5

if __name__ == '__main__':
    unittest.main()
