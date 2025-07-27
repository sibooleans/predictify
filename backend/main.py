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

    return final_max

#ARIMA Model

def simple_arima_prediction(prices: list, days_ahead: int, current_price: float):
    try:
        # Convert to returns (more stable than raw prices)
        returns = []
        for i in range(1, len(prices)):
            daily_return = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(daily_return)
        
        # Use last 30 days of returns
        recent_returns = returns[-25:] if len(returns) > 25 else returns
        
        if len(recent_returns) < 10:
            if len(recent_returns) >= 5:
                try:
                    model = ARIMA(recent_returns, order=(1,1,1))
                    fitted = model.fit()
                    forecast = fitted.forecast(steps=days_ahead)
                    
                    predicted_price = current_price
                    for return_pred in forecast:
                        predicted_price *= (1 + return_pred)
                    
                    # Apply constraints
                    max_change = 0.10 if days_ahead <= 3 else 0.15
                    min_price = current_price * (1 - max_change)
                    max_price = current_price * (1 + max_change)
                    predicted_price = max(min_price, min(max_price, predicted_price))
                    
                    return {
                        'predicted_price': predicted_price,
                        'confidence': 55,
                        'method': 'ARIMA_minimal_data',
                        'model_params': (1,1,1)
                    }
                except:
                    pass

                #fallback when impossible.

                avg_return = np.mean(recent_returns) if recent_returns else 0
                predicted_price = current_price * (1 + avg_return * days_ahead * 0.1)
                return {
                    'predicted_price': predicted_price,
                    'confidence': 40,
                    'method': 'insufficient_data_fallback',
                    'model_params': 'fallback'
                }
        
        # ARIMA strats in order of likely sucess
        
        arima_strategies = [
            (1,1,1), # Most common, fastest method
            (0,1,1), # Simple MA model
            (1,1,0), # Simple AR model
            (2,1,1), # More complex
            (1,1,2), # More complex
            (1,1,1), # Retry with better method
            (0,1,1), # Retry with better method
            (2,1,2), # Most complex, more time
            ]   
    
        best_model = None
        best_aic = float('inf')
        best_params = None
        total_time = 0
        max_time = 4.5
        
        #attempt to fix issue that arima takes LOADS of time
        import time
        
        for params, time_limit, method in arima_strategies:
            if total_time >= max_time:
                print(f"ARIMA time budget exhausted: {total_time:.1f}s")
                break
            
            start_time = time.time()
            
            try:
                model = ARIMA(recent_returns, order=params)
            
                # methof fitting and time limit
                fitted = model.fit(disp=False)
                
                
                fit_time = time.time() - start_time
                total_time += fit_time
                
                # Check if this is the best model so far
                if fitted.aic < best_aic:
                    best_aic = fitted.aic
                    best_model = fitted
                    best_params = params
                    print(f"ARIMA{params} succeeded in {fit_time:.2f}s, AIC: {fitted.aic:.2f}")
                
                # decent model and are running out of time, stop
                if best_aic < 0 and total_time > 3.0:
                    print(f"Good ARIMA model found, stopping early at {total_time:.1f}s")
                    break
                    
            except Exception as e:
                fit_time = time.time() - start_time
                total_time += fit_time
                print(f"ARIMA{params} failed in {fit_time:.2f}s: {str(e)[:50]}")
                continue
        
        # If we found a working ARIMA model, use it
        if best_model is not None:
            try:
                print(f"Using ARIMA{best_params} with AIC {best_aic:.2f}")
    
                forecast = best_model.forecast(steps=days_ahead)
                
                # Convert returns back to price
                predicted_price = current_price
                for return_pred in forecast:
                    predicted_price *= (1 + return_pred)
                
                # Calculate confidence based on model quality
                confidence = 60 
                if best_aic < -50:
                    confidence += 15  # great model
                elif best_aic < -20:
                    confidence += 10  # good model
                elif best_aic < 0:
                    confidence += 5   # decent model
                
                if len(recent_returns) > 20:
                    confidence += 5  # more data pts bonus
                
                # constraints
                max_change = 0.12 if days_ahead <= 3 else 0.18
                min_price = current_price * (1 - max_change)
                max_price = current_price * (1 + max_change)
                predicted_price = max(min_price, min(max_price, predicted_price))
                
                return {
                    'predicted_price': predicted_price,
                    'confidence': min(75, confidence),
                    'method': 'ARIMA_success',
                    'model_params': best_params,
                    'aic': best_aic,
                    'total_time': round(total_time, 2)
                }
                
            except Exception as e:
                print(f"ARIMA forecast failed: {e}")
                # model fitted but forecast failed - use model's fitted values
                try:
                    # use model's trend for prediction
                    fitted_values = best_model.fittedvalues
                    if len(fitted_values) > 0:
                        recent_trend = np.mean(fitted_values[-3:])
                        predicted_price = current_price * (1 + recent_trend * days_ahead)
                        
                        max_change = 0.10
                        min_price = current_price * (1 - max_change)
                        max_price = current_price * (1 + max_change)
                        predicted_price = max(min_price, min(max_price, predicted_price))
                        
                        return {
                            'predicted_price': predicted_price,
                            'confidence': 55,
                            'method': 'ARIMA_fitted_trend',
                            'model_params': best_params
                        }
                except:
                    pass
        # enhanced fallback in case of no model
        if len(recent_returns) >= 5:
            # Use multiple statistical approaches
            approaches = []
            
            # 1. exponential smoothing
            alpha = 0.3
            smoothed = recent_returns[0]
            for ret in recent_returns[1:]:
                smoothed = alpha * ret + (1 - alpha) * smoothed
            approaches.append(smoothed)
            
            # 2. weighted recent average
            weights = np.linspace(1, 3, len(recent_returns[-5:]))  
            weights = weights / weights.sum()
            weighted_avg = np.average(recent_returns[-5:], weights=weights)
            approaches.append(weighted_avg)
            
            # 3. mean reversion consideration
            last_return = recent_returns[-1]
            vol = np.std(recent_returns)
            if abs(last_return) > vol:  
                mean_rev = -last_return * 0.2 
            else:
                mean_rev = np.mean(recent_returns[-3:])
            approaches.append(mean_rev)
            
            # average the approaches
            combined_signal = np.mean(approaches)
            predicted_price = current_price * (1 + combined_signal * days_ahead * 0.4)
        else:
            # simple fallback
            avg_return = np.mean(recent_returns)
            predicted_price = current_price * (1 + avg_return * days_ahead * 0.2)
        
        # constraints
        max_change = 0.08 if days_ahead <= 3 else 0.12
        min_price = current_price * (1 - max_change)
        max_price = current_price * (1 + max_change)
        predicted_price = max(min_price, min(max_price, predicted_price))
        
        return {
            'predicted_price': predicted_price,
            'confidence': 45,
            'method': 'statistical_fallback_after_arima_failed',
            'model_params': 'stat_fallback',
            'arima_attempts': len(arima_strategies),
            'total_time': round(total_time, 2)
        }
        
    except Exception as e:
        print(f"Complete ARIMA failure: {e}")
        # emergency fallback
        predicted_price = current_price * (1 + np.random.normal(0, 0.005))
        return {
            'predicted_price': predicted_price,
            'confidence': 35,
            'method': 'emergency_fallback',
            'model_params': 'emergency'
        }
        
       
        

def fallback_prediction(prices: list, days_ahead: int, current_price: float):
    #if random forest fails. fall back to a simple trend extrapolation.
    try:
        if len(prices) > 10:
            #trend from recent prices
            recent_count = min(20, len(prices))  # Use last 20 days or all available
            recent_prices = prices[-recent_count:]
            
            #linear trend
            if len(recent_prices) >= 3:
                # Simple slope calculation
                x_vals = list(range(len(recent_prices)))
                y_vals = recent_prices
                
                #trend (change per day)
                n = len(recent_prices)
                sum_x = sum(x_vals)
                sum_y = sum(y_vals)
                sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
                sum_x2 = sum(x * x for x in x_vals)
                
                # linear regression slope
                if n * sum_x2 - sum_x * sum_x != 0:
                    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                else:
                    slope = 0
                
                # conservative trend
                trend_prediction = current_price + (slope * days_ahead * 0.3)  # 30% of full trend
            else:
                # in case of not enough data.
                avg_change = (recent_prices[-1] - recent_prices[0]) / len(recent_prices)
                trend_prediction = current_price + (avg_change * days_ahead * 0.1)
            
            # conservative constraints to keep control (fallback should be safe)
            if days_ahead <= 30:
                max_change_percent = 0.08  # 8% max for monthly fallback
            elif days_ahead <= 60:
                max_change_percent = 0.12  # 12% max for 2-month fallback
            else:
                max_change_percent = 0.15  # 15% max for longer fallback
            
            min_price = current_price * (1 - max_change_percent)
            max_price = current_price * (1 + max_change_percent)
            safe_prediction = max(min_price, min(max_price, trend_prediction))
            
            # confidence based off quality of datas
            if len(prices) > 30:
                confidence = 40
            elif len(prices) > 20:
                confidence = 35
            else:
                confidence = 30
            
            return {
                'predicted_price': safe_prediction,
                'confidence': confidence,
                'method': 'trend_fallback',
                'data_points': len(recent_prices)
            }
            
        elif len(prices) >= 3:
            # minimal change
            recent_change = (prices[-1] - prices[-3]) / 2  # Average of last 2 days
            minimal_prediction = current_price + (recent_change * days_ahead * 0.05)  # Very conservative
            
            # constraints
            max_change = current_price * 0.05  # 5% max when very little data
            min_price = current_price - max_change
            max_price = current_price + max_change
            safe_prediction = max(min_price, min(max_price, minimal_prediction))
            
            return {
                'predicted_price': safe_prediction,
                'confidence': 25,
                'method': 'minimal_data_fallback',
                'data_points': len(prices)
            }
        
        else:
            #really really suay suay no data - return current price
            return {
                'predicted_price': current_price,
                'confidence': 20,
                'method': 'no_change_fallback',
                'data_points': len(prices)
            }
        
    except Exception as e:
        print(f"Even fallback prediction failed: {e}")
        # for emergency also just return current price
        return {
            'predicted_price': current_price,
            'confidence': 15,
            'method': 'emergency_fallback',
            'error': str(e)
        }
def random_forest_prediction(prices: list, days_ahead: int, current_price: float):
    try:
        if len(prices) < 50:
            print(f"Not enough price data: {len(prices)} points, need at least 50")
            return fallback_prediction(prices, days_ahead, current_price)
        
        daily_returns = []
        for i in range(1, min(len(prices), 252)):  # Last year of data max
            if prices[-i-1] > 0:  # Avoid division by zero
                daily_return = (prices[-i] - prices[-i-1]) / prices[-i-1]
                if abs(daily_return) < 0.5:  # Filter out extreme outliers (50%+ moves)
                    daily_returns.append(daily_return)
        
        if len(daily_returns) < 20:
            print(f"Not enough valid daily returns: {len(daily_returns)}")
            return fallback_prediction(prices, days_ahead, current_price)
        
        # realistic constraints based on historical volatility
        historical_volatility = np.std(daily_returns)
        if historical_volatility == 0:
            print("Zero volatility detected")
            return fallback_prediction(prices, days_ahead, current_price)
        '''annual_volatility = historical_volatility * np.sqrt(252)  # Annualized volatility
        
        # annual volatility for realistic bounds
        time_factor = days_ahead / 252  # Fraction of a year
        expected_volatility = annual_volatility * np.sqrt(time_factor)'''
        #pretty much the same method as under the predict function, just now moving it out.
        
        X = []
        y = []
        
        size = 20

        min_data_needed = size + days_ahead + 10  # Extra buffer

        if len(prices) < min_data_needed:
            print(f"Insufficient data for windowing: need {min_data_needed}, have {len(prices)}")
            return fallback_prediction(prices, days_ahead, current_price)
        
        for i in range(size, len(prices) - days_ahead):
            try:
                window = prices[i-size:i]
                current_window_price = prices[i]
                future_price = prices[i + days_ahead]
            
                if (len(window) != size or 
                    current_window_price <= 0 or 
                    future_price <= 0 or
                    any(p <= 0 for p in window)):
                    continue
                
                # calculate features with error checking
                try:
                    features = [
                        np.mean(window[-5:]) / current_window_price,
                        np.mean(window[-10:]) / current_window_price,
                        np.mean(window[-20:]) / current_window_price,
                        (window[-1] - window[-5]) / window[-5] if len(window) >= 5 and window[-5] > 0 else 0,
                        (window[-1] - window[-10]) / window[-10] if len(window) >= 10 and window[-10] > 0 else 0,
                        np.std(window[-10:]) / np.mean(window[-10:]) if np.mean(window[-10:]) > 0 else 0,
                        (window[-1] - window[0]) / window[0] if window[0] > 0 else 0,
                        (np.max(window) - np.min(window)) / np.mean(window) if np.mean(window) > 0 else 0
                    ]
                    
                    # validate features (no NaN, no infinity)
                    if any(not np.isfinite(f) for f in features):
                        continue
                    
                    # calculate target (relative change)
                    relative_change = (future_price - current_window_price) / current_window_price
                    
                    # validate target
                    if not np.isfinite(relative_change) or abs(relative_change) > 1.0: 
                        continue
                    
                    X.append(features)
                    y.append(relative_change)
                    
                except (ZeroDivisionError, ValueError, IndexError):
                    continue
            
            except Exception as e:
                print(f"Error processing window {i}: {e}")
                continue
        
        # got enpugh training data?
        if len(X) < 20:  #min20 samples
            print(f"Not enough valid training samples: {len(X)}, need at least 20")
            return fallback_prediction(prices, days_ahead, current_price)
        
        print(f"Training Random Forest with {len(X)} samples")
        
        # convert to numpy arrays with validation
        try:
            X = np.array(X)
            y = np.array(y)
            
            # Check for empty arrays or wrong shapes
            if X.shape[0] == 0 or y.shape[0] == 0:
                print(f"Empty arrays after conversion: X shape {X.shape}, y shape {y.shape}")
                return fallback_prediction(prices, days_ahead, current_price)
            
            if X.shape[0] != y.shape[0]:
                print(f"Mismatched array sizes: X {X.shape[0]}, y {y.shape[0]}")
                return fallback_prediction(prices, days_ahead, current_price)
                
        except Exception as e:
            print(f"Error converting to numpy arrays: {e}")
            return fallback_prediction(prices, days_ahead, current_price)
        
        
        # training model
        try:
            model = RandomForestRegressor(n_estimators=50, 
                                        random_state=42,
                                        max_depth=8,
                                        min_samples_split=5,
                                        min_samples_leaf=2)
            model.fit(X, y)

        except Exception as e:
            print(f"Error training Random Forest: {e}")
            return fallback_prediction(prices, days_ahead, current_price)

        
        # prediction w validaion
        try:
            current_window = prices[-size:]
            if len(current_window) != size or any(p <= 0 for p in current_window):
                print("Invalid current window for prediction")
                return fallback_prediction(prices, days_ahead, current_price)
        
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
        
            if any(not np.isfinite(f) for f in current_features):
                print("Invalid features for prediction")
                return fallback_prediction(prices, days_ahead, current_price)

            predicted_relative_change = model.predict([current_features])[0]

            if not np.isfinite(predicted_relative_change):
                print("Model returned invalid prediction")
                return fallback_prediction(prices, days_ahead, current_price)
            
        except Exception as e:
            print(f"Error making prediction: {e}")
            return fallback_prediction(prices, days_ahead, current_price)
        

        max_change = stock_smart_constraint(historical_volatility, days_ahead)
        predicted_relative_change = np.clip(predicted_relative_change, -max_change, max_change)

        predicted_price = current_price * (1 + predicted_relative_change)

        #relativity to tevert to long term trends over months
        '''if days_ahead > 30:
        long_term_return = np.mean(daily_returns) * days_ahead
        predicted_relative_change = predicted_relative_change * 0.7 + long_term_return * 0.3'''

        # confidence
        score = model.score(X, y)
        confidence = max(45, min(70, int(score * 85)))

        if days_ahead > 30: #reduce confidence for long predicts
            confidence_penalty = min(15, (days_ahead - 30) * 0.3)
            confidence -= confidence_penalty
        
        final_confidence = max(40, int(confidence))
        return {
            'predicted_price': predicted_price,
            'confidence': final_confidence,
            'method': 'RandomForest',
            'training_samples': len(X)
        }
    
    except Exception as e:
        print(f"Random Forest error: {e}")
        return fallback_prediction(prices, days_ahead, current_price)


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
