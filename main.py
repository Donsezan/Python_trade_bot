import argparse
import os
import sys
# Delay import of Orchestrator until after config is set

import argparse
import yaml
from pathlib import Path

def main():
    """Main function to run the trading bot."""
    parser = argparse.ArgumentParser(description='Run the trading bot.')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    args = parser.parse_args()

    if args.test:
        print("Running in TEST mode")
        os.environ['CONFIG_PATH'] = os.path.abspath('config.test.yaml')
        
    # Import Orchestrator after setting env var
    from trading_bot.orchestrator import Orchestrator
    orchestrator = Orchestrator(backtesting=args.test)
    orchestrator.run()

if __name__ == "__main__":
    main()
