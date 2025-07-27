import yfinance as yf
import numpy as np
from utils.helpers import chart_timeframe

def stock_current_price(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="2d")  #make sure got 2 days of data
        
        if data.empty:
            return None
            
        current = float(data['Close'].iloc[-1])
        previous = float(data['Close'].iloc[-2]) if len(data) > 1 else current
        
        change = current - previous

        if previous != 0:
            change_percent = (change / previous) * 100
        else:
            change_percent = 0
        
        return {
            "current_price": current,
            "price_change": change,
            "price_change_percent": change_percent
        }
        
    except Exception as e:
        print(f"Error getting current price for {symbol}: {e}")
        return None
    
def fetch_historical_prices(symbol: str, period: str, days_ahead: int):
    #tackling both chart data and model data in this function
    try:
        data = yf.download(symbol, period = period)

        if data.empty or "Close" not in data.columns:
            return None
    
        prices_series = data["Close"].squeeze().dropna()
        prices = prices_series.tolist()

        if len(prices) < 2:
            return None
        #train model
        x = np.array(range(len(prices))).reshape(-1, 1)
        y = np.array(prices).reshape(-1, 1)

        chart_no_days = chart_timeframe(days_ahead)
        chart_data = data.tail(chart_no_days)

        historical_data = []
        for date in chart_data.index:
            price_value = chart_data.loc[date, "Close"]
            if hasattr(price_value, 'iloc'):
                price = float(price_value.iloc[0])
            else:
                price = float(price_value)

            historical_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": price
            })
            
        return (x, y), historical_data
    
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def get_historical_data(symbol: str, period: str = "1mo"):
    try:
        _, historical_data = fetch_historical_prices(symbol, period)
        current_price_data = stock_current_price(symbol)
        
        if historical_data is None:
            return {"error": "Unable to fetch historical data"}
            
        return {
            "symbol": symbol.upper(),
            "historical_data": historical_data,
            "current_price_data": current_price_data
        }
        
    except Exception as e:
        return {"error": f"Failed to fetch historical data: {str(e)}"}
    
