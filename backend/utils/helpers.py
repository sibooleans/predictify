import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

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
