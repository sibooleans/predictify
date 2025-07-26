from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import requests
import numpy as np
import pandas as pd
import os
import yfinance as yf

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# in-memory history store, will be updating this with calls eventuallly no time now
history = []

#response model for history (this the import from pydantic)
class Prediction(BaseModel):
    stock: str
    predicted_price: float
    confidence: int
    volatility: str
    trend: str
    sentiment: str
    timestamp: str
    #chart fields
    current_price: float
    price_change: float
    price_change_percent: float

class HistoricalData(BaseModel):
    date: str
    price: float

class PredictionResponse(BaseModel):
    prediction: Prediction
    historical_data: List[HistoricalData]
    prediction_timeline: List[Dict[str, Any]]

#helpers

analyzer = SentimentIntensityAnalyzer()

# US Market Holidays for 2025 - Update yearly
US_MARKET_HOLIDAYS_2025 = [
    "2025-01-01",  
    "2025-01-20",  
    "2025-02-17",  
    "2025-04-18",  
    "2025-05-26",  
    "2025-06-19",  
    "2025-07-04",  
    "2025-09-01",  
    "2025-11-27",  
    "2025-12-25",  
]

def is_trading_day(date):
    if isinstance(date, str):
        date = pd.to_datetime(date)
    
    # Check for weekend (Saturday=5, Sunday=6)
    if date.weekday() >= 5:
        return False
    
    # Check for holiday
    date_str = date.strftime("%Y-%m-%d")
    if date_str in US_MARKET_HOLIDAYS_2025:
        return False
    
    return True

def get_trading_date(start_date, trading_days_ahead):
    current_date = pd.to_datetime(start_date)
    trading_days_found = 0
    
    while trading_days_found < trading_days_ahead:
        current_date += timedelta(days=1)
        if is_trading_day(current_date):
            trading_days_found += 1
    
    return current_date

def get_trading_info(days_ahead):
    today = datetime.now()
    target_date = get_trading_date(today, days_ahead)
    calendar_days = (target_date - today).days
    
    return {
        "trading_days_ahead": days_ahead,
        "calendar_days_ahead": calendar_days,
        "target_date": target_date.strftime("%Y-%m-%d"),
        "target_date_formatted": target_date.strftime("%B %d, %Y"),
        "weekends_skipped": calendar_days - days_ahead,
        "is_trading_day_today": is_trading_day(today)
    }


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

def chart_timeframe(days_ahead: int):
    #refer to the prediction window to get length of data
    if days_ahead <= 3:
        return 30
    elif days_ahead <= 10:
        return 60
    elif days_ahead <= 30:
        return 90
    elif days_ahead <= 90:
        return 180
    else:
        return 365

def chart_title(days_ahead: int):
    if days_ahead <= 3:
        return "📊 Recent Price History (30 Days)"
    elif days_ahead <= 10:
        return "📊 Price History (2 Months)"
    elif days_ahead <= 30:
        return "📊 Price History (3 Months)"
    elif days_ahead <= 90:
        return "📊 Price History (6 Months)"
    else:
        return "📊 Price History (1 Year)"

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

def generate_pred_timeline(current_price: float, predicted_price: float, 
                           trading_days_ahead: int, volatility: str):
    #get data points
    timeline = []

    timeline.append({
        "day": 0,
        "price": current_price,
        "label": "Today",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "is_trading_day": True
    })

    price_change = predicted_price - current_price

    vol_factor = {
        "Low": 0.003,      # 1% daily variation
        "Moderate": 0.006, # 2% daily variation  
        "High": 0.012       # 4% daily variation
    }.get(volatility, 0.006)

    current_date = datetime.now()
    trading_days_counted = 0
    calendar_days_checked = 0

    while trading_days_counted < trading_days_ahead and calendar_days_checked < trading_days_ahead * 3:
        calendar_days_checked += 1
        current_date += timedelta(days=1)
        
        if is_trading_day(current_date):
            trading_days_counted += 1

        # linear progress         
        progress = trading_days_counted / trading_days_ahead
        base_price = current_price + (price_change * progress)
        
         # market noise based on volatility
        daily_variation = np.random.normal(0, current_price * vol_factor)
        price_point = base_price + daily_variation
        
        # non negativity or not too high constraints
        price_point = max(current_price * 0.5, base_price + daily_variation)
        price_point = min(current_price * 2.0, price_point)  # capped at 2x current price


        
        if trading_days_counted % max(1, trading_days_ahead // 5) == 0 or trading_days_counted == trading_days_ahead:
            label = f"+{trading_days_counted}d"
        else:
            label = ""
        
        timeline.append({
            "day": trading_days_counted,
            "price": float(price_point),
            "label": label,
            "date": current_date.strftime("%Y-%m-%d"),
            "is_trading_day": True
        })
    
    return timeline



def get_sentiment(symbol: str):
    #yet to use real tweets/reddit
    mock_headlines = [
        f"{symbol} shows strong growth potential!",
        f"Mixed opinions on {symbol} stock today.",
        f"Investors worry about Q3 earnings for {symbol}",
    ]

    scores = [analyzer.polarity_scores(text)["compound"] 
              for text in mock_headlines]
    
    avg = sum(scores) / len(scores)
    if avg > 0.2:
        return "Positive"
    elif avg < -0.2:
        return "Negative"
    else:
        return "Neutral"
    
def obtain_volatility(prices):
    if len(prices) < 2:
        return "Unknown"
    
    #daily returns
    returns = []
    for i in range (1, len(prices)):
        daily_return = (prices[i] - prices[i - 1]) / prices[i - 1]
        returns.append(daily_return)

    #sd
    vol = np.std(returns) * np.sqrt(252) #252 is avg no of trading days a yr

    if vol > 0.3:
        return "High"
    elif vol > 0.15:
        return "Moderate"
    else:
        return "Low"
    
def determine_period(days_ahead: int):
    if days_ahead <= 3:
        return "1mo"
    elif days_ahead <= 10:
        return "3mo"
    elif days_ahead <= 30:
        return "6mo"
    else:
        return "1y"    

    

# predict endpoint
@app.get("/predict")

def predict(stock: str = "AAPL", days_ahead: int = 1):
    try:
        trading_info = get_trading_info(days_ahead)

        history_period = determine_period(days_ahead)
        model_data, historical_data = fetch_historical_prices(stock,
            period = history_period, days_ahead = days_ahead)
        current_price_data = stock_current_price(stock)

        if model_data is None or current_price_data is None:
            return {"error": "Invalid stock symbol or unable ot fetch data."}
        
        x, y = model_data

        if len(x) < 10: #min data
            return {"error": "Insufficient historical data for prediction"}
        
        #split up data
        X_train, X_test, y_train, y_test = train_test_split(
            x, y.ravel(), test_size=0.2, shuffle=False, random_state=42
        )
        #Train model on training data
        model = RandomForestRegressor(n_estimators = 100, random_state = 42)
        model.fit(X_train, y_train)

        #confidence from text data
        test_score = model.score(X_test, y_test)
        #confidence capped from 30-85
        confidence = max(30, min(85, int(test_score * 100)))

        #prediction
        future_day = len(x) + days_ahead - 1
        predicted = model.predict([[future_day]])[0]

       #volatility
        prices = y.ravel().tolist()
        vol = obtain_volatility(prices)

        #prediction bounds
        current_price = current_price_data["current_price"]

        #prediction limited to not too high changes
        max_change = current_price * 0.20  # 20% max change
        min_price = current_price - max_change
        max_price = current_price + max_change

        predicted = max(min_price, min(max_price, predicted))

        result = Prediction(
            stock = stock.upper(),
            predicted_price = float(predicted),
            confidence = confidence,
            volatility = vol,
            trend = "Uptrend" if predicted > current_price_data["current_price"] else "Downtrend",
            sentiment = get_sentiment(stock),
            timestamp = datetime.now().isoformat(),
            current_price = current_price_data["current_price"],
            price_change = current_price_data["price_change"],
            price_change_percent = current_price_data["price_change_percent"]
        )
        #timeline
        pred_timeline = generate_pred_timeline(
            current_price_data["current_price"], 
            float(predicted), 
            days_ahead,
            vol
        )

        api_response = {
            "prediction": result.model_dump(),
            "historical_data": historical_data,
            "prediction_timeline": pred_timeline,
            "chart_info": {
                "title": chart_title(days_ahead),
                "timeframe_days": chart_timeframe(days_ahead),
                "data_period": history_period
            },
            "trading info": trading_info
        }

        history.append(result.model_dump())
        return api_response
        
    except Exception as e:
        print(f"Prediction error: {e}")
        return {"error": f"Prediction failed: {str(e)}"}


@app.head("/predict")

def head_predict(stock: str = "AAPL"):
    return {}

# history endpoint
@app.get("/history", response_model=List[Prediction])

def get_history():
    return history

@app.head("/history")

def head_history():
    return {}

#endpoint for js historical data
@app.get("/historical/{symbol}")
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


@app.get("/")

def root():
    print("[DEBUG] Hello from updated root!")
    return {"message": "Backend is running."}

@app.head("/")

def head_root():
    return {}
