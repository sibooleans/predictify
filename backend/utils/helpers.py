import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

#try same logic as explore endpoint to get reddit api calls
'''def create_reddit_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.reddit.com/'
    })
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# Use session in sentiment function
reddit_session = create_reddit_session()


analyzer = SentimentIntensityAnalyzer()

def get_sentiment(symbol: str):

    #reddit sentiment with basic rzning
    try:
        print(f"[DEBUG] Starting sentiment analysis for {symbol}")
        url = f"https://www.reddit.com/r/stocks/search.json?q={symbol}&sort=new&limit=10"
        headers = {'User-Agent': 'StockApp/1.0'}

        print(f"[DEBUG] Making request to: {url}")
        response = reddit_session.get(url, timeout=10)
        print(f"[DEBUG] Response status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"[DEBUG] Reddit API error: {response.status_code}")
           
            data = response.json()

        else:

        sentiments = []
        posts_count = 0
        sample_titles = []

        #for loop to find posts on reddit
        for post in data['data']['children']:
            title = post['data']['title']
            score = analyzer.polarity_scores(title)['compound']
            sentiments.append(score)
            post_count += 1
            print(f"[DEBUG] Post: '{title[:50]}...' Score: {score}")

            if len(sample_titles) < 2:
                sample_titles.append(title[:50] + "..." if len(title) > 50 else title)
            
        if not sentiments:
            print("[DEBUG] No posts found")
            return {
                "sentiment": "Neutral",
                "reason": "No recent Reddit discussions found"
            }
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        print(f"[DEBUG] Average sentiment: {avg_sentiment}")

        #basic post count for reason on frontend.

        if avg_sentiment > 0.2:
            sentiment_word = "Positive"
            reason = f"Bullish across {post_count} Reddit posts"
        elif avg_sentiment > 0.05:
            sentiment_word = "Positive" 
            reason = f"Mildly positive in {post_count} Reddit posts"
        elif avg_sentiment < -0.2:
            sentiment_word = "Negative"
            reason = f"Bearish across {post_count} Reddit posts"
        elif avg_sentiment < -0.05:
            sentiment_word = "Negative"
            reason = f"Mildly negative in {post_count} Reddit posts"
        else:
            sentiment_word = "Neutral"
            reason = f"Mixed opinions in {post_count} Reddit posts"
        
        return {
            "sentiment": sentiment_word,
            "reason": reason
        }
            
    except Exception as e:
        print(f"[DEBUG] Exception occurred: {str(e)}")
        return {
            "sentiment": "Neutral",
            "reason": "Sentiment analysis unavailable"
        }'''

reddit_session = requests.Session()
reddit_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.reddit.com/'
})

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
reddit_session.mount("http://", adapter)
reddit_session.mount("https://", adapter)

analyzer = SentimentIntensityAnalyzer()

def get_sentiment(symbol: str):
    """Simple Reddit sentiment with session bypass and basic reasoning"""
    
    # Try multiple subreddits for better success rate
    subreddits = ['stocks', 'investing', 'SecurityAnalysis']
    
    for subreddit in subreddits:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/search.json?q={symbol}&sort=new&limit=10"
            
            print(f"[DEBUG] Trying r/{subreddit} for {symbol}")
            
            # Use session instead of requests.get (bypass method)
            response = reddit_session.get(url, timeout=10)
            
            print(f"[DEBUG] Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"[DEBUG] r/{subreddit} failed with {response.status_code}, trying next...")
                continue
                
            data = response.json()
            
            sentiments = []
            post_count = 0
            sample_titles = []
            
            for post in data['data']['children']:
                title = post['data']['title']
                score = analyzer.polarity_scores(title)['compound']
                sentiments.append(score)
                post_count += 1
                
                # Keep first 2 titles as examples
                if len(sample_titles) < 2:
                    sample_titles.append(title[:50] + "..." if len(title) > 50 else title)
            
            if not sentiments:
                print(f"[DEBUG] No posts found in r/{subreddit}, trying next...")
                continue
            
            # Found posts! Analyze sentiment
            avg_sentiment = sum(sentiments) / len(sentiments)
            print(f"[DEBUG] Found {post_count} posts in r/{subreddit}, avg sentiment: {avg_sentiment}")
            
            # Create reason with post count and sentiment strength (your original logic)
            if avg_sentiment > 0.2:
                sentiment_word = "Positive"
                reason = f"Bullish across {post_count} Reddit posts"
            elif avg_sentiment > 0.05:
                sentiment_word = "Positive" 
                reason = f"Mildly positive in {post_count} Reddit posts"
            elif avg_sentiment < -0.2:
                sentiment_word = "Negative"
                reason = f"Bearish across {post_count} Reddit posts"
            elif avg_sentiment < -0.05:
                sentiment_word = "Negative"
                reason = f"Mildly negative in {post_count} Reddit posts"
            else:
                sentiment_word = "Neutral"
                reason = f"Mixed opinions in {post_count} Reddit posts"
            
            return {
                "sentiment": sentiment_word,
                "reason": reason
            }
            
        except Exception as e:
            print(f"[DEBUG] Error with r/{subreddit}: {e}")
            continue
    
    # If all subreddits fail
    print("[DEBUG] All Reddit sources failed")
    return {
        "sentiment": "Neutral",
        "reason": "No recent Reddit discussions found"
    }


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

"""def stock_smart_constraint(historical_volatility: float, days_ahead: int):
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

    return final_max"""
def stock_smart_constraint(historical_volatility: float, days_ahead: int):
    daily_vol = historical_volatility
    time_scaled_vol = daily_vol * np.sqrt(days_ahead)
    
    if days_ahead <= 3:
        multiplier = 0.8   
        absolute_max = 0.025  
    elif days_ahead <= 7:
        multiplier = 1.0   
        absolute_max = 0.04   
    elif days_ahead <= 30:
        multiplier = 1.2   
        absolute_max = 0.12   
    else:
        multiplier = 1.5
        absolute_max = 0.25   
    
    calculated_max = time_scaled_vol * multiplier
    final_max = min(calculated_max, absolute_max)
    
    # NO minimum - let stable stocks be stable!
    return final_max


