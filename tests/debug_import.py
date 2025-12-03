print("Starting debug import...", flush=True)
try:
    from trading_bot.news.news_ingestor import NewsIngestor
    print("Import successful", flush=True)
except Exception as e:
    print(f"Import failed: {e}", flush=True)
