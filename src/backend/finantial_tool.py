import yfinance as yf
import json

def get_finance_index():
    tickers = {
        "ドル円為替レート": 'JPY=X',  # ドル円のティッカーシンボル
        "TOPIX": '1306.T',  # TOPIX連動ETFのティッカーシンボル
        "全米インデックス": 'VTI',  # 全米インデックスのティッカーシンボル
        "オルカン": 'ACWI',  # ACWIのティッカーシンボル
        "S&P500": '^GSPC',  # S&P500のティッカーシンボル
        "Bitcoin": 'BTC-USD',  # ビットコインのティッカーシンボル
    }

    results = {}
    
    for name, ticker in tickers.items():
        try:
            price, change, percent_change = get_stock_price_and_change(ticker)
            results[name] = {
                "price": int(price) ,
                "percent_change": round(percent_change, 1)  # 小数点1桁までに丸める
            }
        except ValueError as e:
            results[name] = {
                "error": str(e)
            }
        except Exception as e:
            results[name] = {
                "error": f"An unexpected error occurred: {e}"
            }

    # JSON形式で出力
    return json.dumps(results, ensure_ascii=False, indent=2)

def get_stock_price_and_change(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="5d", interval="1d")  # 直近5日間のデータを取得
    #
    if len(hist) < 2:
        raise ValueError(f"Not enough data to calculate change for ticker {ticker}")
    #
    # 最新の終値と前日の終値を取得
    latest_close = hist['Close'].iloc[-1]
    previous_close = hist['Close'].iloc[-2]
    #
    # 前日比を計算
    change = latest_close - previous_close
    percent_change = (change / previous_close) * 100
    #
    return latest_close, change, percent_change