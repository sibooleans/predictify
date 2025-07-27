from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from statsmodels.tsa.arima.model import ARIMA
import requests
import numpy as np
import pandas as pd
import os
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

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

def stock_smart_constraint(historical_volatility: float, days_ahead: int):
    #auto-determining a stocks constraint based in its own behaviour
    annual_vol = historical_volatility * np.sqrt(252)
    time_factor = np.sqrt(days_ahead / 30)
    monthly_expected_move = annual_vol / np.sqrt(12)

    if days_ahead <= 30:  
        max_change = monthly_expected_move * time_factor * 1.5  # 1.5x buffer
    elif days_ahead <= 60: 
        max_change = monthly_expected_move * time_factor * 1.3  # Less buffer 
    else:  
        max_change = monthly_expected_move * time_factor * 1.2  # Even less buffer
    
    # limits
    if days_ahead <= 30:
        absolute_max = 0.20  # 20% absolute max for 1 month
    elif days_ahead <= 60:
        absolute_max = 0.30  # 30% absolute max for 2 months
    else:
        absolute_max = 0.40  # 40% absolute max for longer
    
    # final constraint
    final_max = min(max_change, absolute_max)

#ARIMA Model

def simple_arima_prediction(prices: list, days_ahead: int, current_price: float):
    try:
        # Convert to returns (more stable than raw prices)
        returns = []
        for i in range(1, len(prices)):
            daily_return = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(daily_return)
        
        # Use last 30 days of returns
        recent_returns = returns[-30:] if len(returns) > 30 else returns
        
        if len(recent_returns) < 10:
            # Fallback to average
            avg_return = np.mean(recent_returns) if recent_returns else 0
            predicted_price = current_price * (1 + avg_return * days_ahead * 0.1)
            return {
                'predicted_price': predicted_price,
                'confidence': 45,
                'method': 'simple_average_fallback',
                'model_params': 'fallback'
            }
        
        # simple ARIMA models
        best_model = None
        best_aic = float('inf')
        best_params = None
        
        # simple combinations
        simple_params = [(1,1,1), (2,1,1), (1,1,2), (2,1,2), (0,1,1)]
        
        for params in simple_params:
            try:
                model = ARIMA(recent_returns, order=params)
                fitted = model.fit()
                if fitted.aic < best_aic:
                    best_aic = fitted.aic
                    best_model = fitted
                    best_params = params
            except:
                continue
        
        if best_model is None:
            # fallback to moving average
            avg_return = np.mean(recent_returns[-7:])  # last week
            predicted_price = current_price * (1 + avg_return * days_ahead * 0.5)
            return {
                'predicted_price': predicted_price,
                'confidence': 50,
                'method': 'moving_average_fallback',
                'model_params': 'ma_fallback'
            }
        
        # prediction
        forecast = best_model.forecast(steps=days_ahead)
        
        predicted_price = current_price
        for return_pred in forecast:
            predicted_price *= (1 + return_pred)
        
        # confidence
        confidence = 60  # Base confidence
        if best_aic < -50:
            confidence += 10
        if len(recent_returns) > 20:
            confidence += 5
        
        # realistic constraints
        max_change = 0.15 if days_ahead <= 3 else 0.25
        min_price = current_price * (1 - max_change)
        max_price = current_price * (1 + max_change)
        predicted_price = max(min_price, min(max_price, predicted_price))
        
        return {
            'predicted_price': predicted_price,
            'confidence': min(75, confidence),
            'method': 'ARIMA',
            'model_params': best_params
        }
        
    except Exception as e:
        print(f"ARIMA error: {e}")
        avg_return = np.mean(np.diff(prices[-10:]) / prices[-11:-1]) if len(prices) > 10 else 0
        predicted_price = current_price * (1 + avg_return * days_ahead * 0.2)
        return {
            'predicted_price': predicted_price,
            'confidence': 40,
            'method': 'error_fallback',
            'model_params': 'error'
        }
    
def random_forest_prediction(prices: list, days_ahead: int, current_price: float):
    try:
        if len(prices) < 30:
            # no data for rf
            if len(prices) > 5:
                # conservative
                recent_trend = (prices[-1] - prices[-10]) / 10 if len(prices) >= 10 else 0
                predicted_price = current_price + (recent_trend * days_ahead * 0.1)  
            else:
                predicted_price = current_price

            return {
                'predicted_price': predicted_price,
                'confidence': 45,
                'method': 'trend_extrapolation'
            }
        
        daily_returns = []
        for i in range(1, min(len(prices), 252)):  # Last year of data max
            daily_return = (prices[-i] - prices[-i-1]) / prices[-i-1]
            daily_returns.append(daily_return)
        
        if not daily_returns:
            return {
                'predicted_price': current_price,
                'confidence': 40,
                'method': 'no_returns_data'
            }
        
        # realistic constraints based on historical volatility
        historical_volatility = np.std(daily_returns)
        annual_volatility = historical_volatility * np.sqrt(252)  # Annualized volatility
        
        # annual volatility for realistic bounds
        time_factor = days_ahead / 252  # Fraction of a year
        expected_volatility = annual_volatility * np.sqrt(time_factor)
        #pretty much the same method as under the predict function, just now moving it out.
        
        X = []
        y = []
        
        size = 20
        for i in range(size, len(prices) - days_ahead):
            window = prices[i-size:i]

            current_window_price = prices[i]
            
            # Enhanced features
            features = [
                i,  # Time index
                np.mean(window[-5:]) / current_window_price,   
                np.mean(window[-10:]) / current_window_price, 
                np.mean(window[-20:]) / current_window_price, 

                (window[-1] - window[-5]) / window[-5] if len(window) >= 5 else 0,  # 5-day momentum
                (window[-1] - window[-10]) / window[-10] if len(window) >= 10 else 0, # 10-day momentum

                np.std(window[-10:]) / np.mean(window[-10:]) if np.mean(window[-10:]) > 0 else 0, # volatility

                window[-1],             # current price
                (window[-1] - window[0]) / window[0],  

                np.max(window) - np.min(window)/ np.mean(window) if np.mean(window) > 0 else 0,  
            ]
            X.append(features)
            
        
        if len(X) < 15:
            # not enough training data
            avg_return = np.mean(daily_returns[-30:]) if len(daily_returns) >= 30 else 0
            predicted_change = avg_return * days_ahead * 0.5  # Very conservative
            predicted_price = current_price * (1 + predicted_change)
            return {
                'predicted_price': predicted_price,
                'confidence': 40,
                'method': 'insufficient_data'
            }
        
        # training model
        model = RandomForestRegressor(n_estimators=100, 
                                      random_state=42,
                                      max_depth=8,
                                      min_samples_split=5,
                                      min_samples_leaf=2)
        model.fit(X, y)
        
        # prediction
        current_window = prices[-size:]
        current_features = [
            np.mean(current_window[-5:]) / current_price,
            np.mean(current_window[-10:]) / current_price,
            np.mean(current_window[-20:]) / current_price,
            (current_window[-1] - current_window[-5]) / current_window[-5] if len(current_window) >= 5 else 0,
            (current_window[-1] - current_window[-10]) / current_window[-10] if len(current_window) >= 10 else 0,
            np.std(current_window[-10:]) / np.mean(current_window[-10:]) if np.mean(current_window[-10:]) > 0 else 0,
            (current_window[-1] - current_window[0]) / current_window[0],
            (np.max(current_window) - np.min(current_window)) / np.mean(current_window) if np.mean(current_window) > 0 else 0
        ]
        
        predicted_relative_change = model.predict([current_features])[0]

        max_change = stock_smart_constraint(historical_volatility, days_ahead)
        
        predicted_relative_change = np.clip(predicted_relative_change, -max_change, max_change)

        #relativity to tevert to long term trends over months
        if days_ahead > 30:
            long_term_return = np.mean(daily_returns) * days_ahead
            predicted_relative_change = predicted_relative_change * 0.7 + long_term_return * 0.3

        # confidence
        score = model.score(X, y)
        confidence = max(45, min(70, int(score * 85)))

        if days_ahead > 30: #reduce confidence for long predicts
            confidence_penalty = min(15, (days_ahead - 30) * 0.3)
            base_confidence -= confidence_penalty
        
        final_confidence = max(40, int(base_confidence))
        return {
            'predicted_price': predicted_price,
            'confidence': confidence,
            'method': 'RandomForest',
            'predicted_change_percent': predicted_relative_change * 100,
            'max_allowed_change': max_change * 100
        }
        
    except Exception as e:
        print(f"Random Forest error: {e}")
        # Trend fallback
        if len(prices) > 10: #conservative
            recent_prices = prices[-min(30, len(prices)):]
            trend = (recent_prices[-1] - recent_prices[0]) / len(recent_prices)
            predicted_price = current_price + (trend * days_ahead * 0.2) 
        else:
            predicted_price = current_price

        max_fallback_change = 0.15  # 15% max even for fallback
        min_price = current_price * (1 - max_fallback_change)
        max_price = current_price * (1 + max_fallback_change)
        predicted_price = max(min_price, min(max_price, predicted_price))
        
        return {
            'predicted_price': predicted_price,
            'confidence': 35,
            'method': 'trend_fallback'
        }

def get_model_info(days_ahead: int):
   #courtesy of frontend
    if days_ahead <= 7:
        return {
            'model_name': 'Short-term Pattern Analysis',
            'model_code': 'ARIMA-S',
            'algorithm': 'ARIMA Time Series Analysis',
            'description': 'Analyzes recent price movements and patterns',
            'timeframe': '1-7 days',
            'approach': 'Time series forecasting with autocorrelation analysis',
            'best_for': 'Short-term predictions based on recent trends',
            'confidence_range': '60-75%'
        }
    else:
        return {
            'model_name': 'Long-term Pattern Recognition',
            'model_code': 'RF-L', 
            'algorithm': 'Random Forest Machine Learning',
            'description': 'Machine learning analysis of historical patterns',
            'timeframe': '8+ days',
            'approach': 'Ensemble learning with technical indicators',
            'best_for': 'Longer predictions using historical data patterns',
            'confidence_range': '55-70%'
        }



# predict endpoint
@app.get("/predict")

def predict(stock: str = "AAPL", days_ahead: int = 1):
    try:

        stock = stock.upper() #so that even aapl becomes AAPL
        if days_ahead < 1 or days_ahead > 90:
            return {"error": "Days ahead must be between 1 and 90"}

        trading_info = get_trading_info(days_ahead)

        history_period = determine_period(days_ahead)
        model_data, historical_data = fetch_historical_prices(stock,
            period = history_period, days_ahead = days_ahead)
        current_price_data = stock_current_price(stock)

        if model_data is None or current_price_data is None:
            return {"error": "Invalid stock symbol or unable ot fetch data."}
        
        x, y = model_data
        prices = y.ravel().tolist()
        current_price = current_price_data["current_price"]

        if len(prices) < 10: #min data
            return {"error": "Insufficient historical data for prediction"}
        
        if days_ahead <= 7:
            # SHORT-TERM: ARIMA
            prediction_result = simple_arima_prediction(prices, days_ahead, current_price)
            model_info = get_model_info(days_ahead)
        else:
            # LONG-TERM: Random Forest
            prediction_result =random_forest_prediction(prices, days_ahead, current_price)
            model_info = get_model_info(days_ahead)

        predicted_price = prediction_result['predicted_price']
        confidence = prediction_result['confidence']    
        sentiment = get_sentiment(stock)
        vol = obtain_volatility(prices)
        
        result = Prediction(
            stock = stock.upper(),
            predicted_price = float(predicted_price),
            confidence = confidence,
            volatility = vol,
            trend = "Uptrend" if predicted_price > current_price_data["current_price"] else "Downtrend",
            sentiment = sentiment,
            timestamp = datetime.now().isoformat(),
            current_price = current_price_data["current_price"],
            price_change = current_price_data["price_change"],
            price_change_percent = current_price_data["price_change_percent"]
        )
        #timeline
        pred_timeline = generate_pred_timeline(
            current_price_data["current_price"], 
            float(predicted_price), 
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
            "trading info": trading_info,
            "model_info": {
                **model_info,
                "method_used": prediction_result['method'],
                "model_params": prediction_result.get('model_params', 'N/A')
            }
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
