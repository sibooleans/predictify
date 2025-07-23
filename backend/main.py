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

#helpers

analyzer = SentimentIntensityAnalyzer()

def fetch_historical_prices(symbol: str):
    #link = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
    data = yf.download(symbol, period = "1mo")
    if data.empty:
        return None
    prices = data["Close"].tolist()
    if len(prices) < 2:
        return None
 
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
        "predicted_price": 0.0,
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
        
        print(f"\n[DEBUG] Stock symbol: {stock}")
        print(f"[DEBUG] x (days): {x.flatten()}")
        print(f"[DEBUG] y (prices): {y.flatten()}")

        model = LinearRegression()
        model.fit(x,y)
        predicted = model.predict([[len(x)]])[0][0] 
        r_squared = model.score(x, y)

        print(f"[DEBUG] Predicted price: {predicted}")
        print(f"[DEBUG] Last actual price: {y[-1][0]}")
        print(f"[DEBUG] R^2 Score: {r_squared}")

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
    print("[DEBUG] Hello from updated root!")
    return {"message": "Backend is running."}

@app.head("/")

def head_root():
    return {}
