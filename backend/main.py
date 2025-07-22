from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.linear_model import LinearRegression
import requests
import numpy as np
import os

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

#helpers

analyzer = SentimentIntensityAnalyzer()
ALPHA_VANTAGE_KEY = os.getenv("VNEGMVK1557V30EK")

def fetch_historical_prices(symbol: str):
    link = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
    response = requests.get(link)
    data = response.json()
    if "Time Series (Daily)" not in data:
        return None
    
    time_series = data["Time Series (Daily)"]
    dates = sorted(time_series.key())[-30:] #data from lats month
    prices = [float(time_series[date]["4. close"]) for date in dates]

    return np.array(range(len(prices))).reshape(-1, 1), np.array(prices).reshape(-1,1)

def get_sentiment(symbol: str):
    #yet to use real tweets/reddit
    mock_headlines = [
        f"{symbol} shows strong growth potential!"
        f"Mixed opinions on {symbol} stock today."
        f"Investors worry about Q3 earnings for {symbol}"
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
    

    

# predict endpoint
@app.get("/predict", response_model=Prediction)

def predict(stock: str = "AAPL"):
    result = {
        "stock": stock,
        "predicted_price": None,
        "confidence": 0,
        "volatility": "Unknown",
        "trend": "Unknown",
        "sentiment": "Unknown",
        "timestamp": datetime.datetime.now().isoformat()
    }

    try:
        x, y = fetch_historical_prices(stock)
        if x is None or y is None:
            return {"error": "Invalid stock symbol or reached API limit."}

        model = LinearRegression()
        model.fit(x,y)
        predicted = model.predict([[len(x)]])[0][0] 
        r_squared = model.score(x, y)

        result.update({
            "predicted_price": float(predicted),
            "confidence": int(r_squared * 100),
            "volatility": "Moderate", #placeholder
            "trend": "Uptrend" if predicted > y[-1] else "Downtrend",
            "sentiment": get_sentiment(stock)
        })
    except Exception as e:
        result["error"] = str(e)

    history.append(result)
    return result

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

@app.get("/")

def root():
    return {"message": "Backend is running."}

@app.head("/")

def head_root():
    return {}
