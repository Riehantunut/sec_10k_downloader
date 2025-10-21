## SEC 10-K downloader

Downloads latest 10-K from SEC, using company tickers.

### How to run:
0. Create environment with Python 3.12
1. Run: ```pip install -r requirements.txt```
2. Run: ```python api_call.py```

This will download Apple's latest 10-K. To change company, modify the company ticker in the function call ```get_latest_10k_by_ticker('AAPL')``` at the bottom of "api_call.py".