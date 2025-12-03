import unittest
import sys
import os

# Add the parent directory to the python path so we can import the package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestEnvironment(unittest.TestCase):
    def test_import_trading_bot(self):
        """Test that the trading_bot package can be imported."""
        try:
            import trading_bot
            print("\nSuccessfully imported trading_bot package.")
        except ImportError as e:
            self.fail(f"Failed to import trading_bot: {e}")

    def test_import_dependencies(self):
        """Test that key dependencies can be imported."""
        dependencies = [
            'ccxt',
            'yaml',
            'sqlalchemy',
            'requests',
            'bs4',
            'openai',
            'ta'
        ]
        
        print("\nChecking dependencies:")
        for dep in dependencies:
            try:
                __import__(dep)
                print(f"  - {dep}: OK")
            except ImportError as e:
                self.fail(f"Failed to import dependency {dep}: {e}")

if __name__ == '__main__':
    unittest.main()
