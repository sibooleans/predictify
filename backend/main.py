from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional
from models.response_models import Prediction
from services.prediction_service import predict as get_prediction
from services.stock_service import get_historical_data
from config.database import db_manager
import yfinance as yf
import requests
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# in-memory history store removed. (py list)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        db_manager.create_tables()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")

@app.get("/setup-db")
def setup_database():
    try:
        db_manager.create_tables()
        return {"message": "Tables created successfully!"}
    except Exception as e:
        return {"error": f"Failed to create tables: {str(e)}"}

@app.get("/")
def root():
    print("[DEBUG] Hello from updated root!")
    return {"message": "Backend is running."}

@app.head("/")
def head_root():
    return {}

# predict endpoint
@app.get("/predict")
def predict(
    stock: str = "AAPL", 
    days_ahead: int = 1,
    user_firebase_uid: Optional[str] = Header(None, alias="X-User-UID"),
    user_email: Optional[str] = Header(None, alias="X-User-Email")
):
    try:
        result = get_prediction(stock, days_ahead)
        
        if user_firebase_uid and "prediction" in result:
            try:
                prediction_data = {
                    **result,
                    'days_ahead': days_ahead,
                    'email': user_email or 'unknown@email.com'
                }
                db_manager.save_prediction(user_firebase_uid, prediction_data)
            except Exception as e:
                print(f"Warning: Could not save to database: {e}")
        
        return result
        
    except Exception as e:
        print(f"Prediction error: {e}")
        return {"error": f"Prediction failed: {str(e)}"}
    
@app.head("/predict")
def head_predict(stock: str = "AAPL"):
    return {}

# history endpoint
@app.get("/history")
def get_history( user_firebase_uid: Optional[str] = Header(None, alias="X-User-UID"),
    limit: int = 50):
    try:
        if not user_firebase_uid:
            return {"error": "User authentication required"}
        
        predictions = db_manager.get_user_predictions(user_firebase_uid, limit)
        return predictions
        
    except Exception as e:
        print(f"History fetch error: {e}")
        return {"error": f"Failed to fetch history: {str(e)}"}
    
@app.head("/history")
def head_history():
    return {}

#endpoint for js historical data
@app.get("/historical/{symbol}")
def historical_data(symbol: str, period: str = "1mo"):
    return get_historical_data(symbol, period)

#db health check endpt
@app.get("/health/database")
def database_health():
    try:
        db_conn = db_manager.get_connection()
        cursor = db_conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        db_conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/user/stats")
def get_user_stats(user_firebase_uid: str = Header(..., alias="X-User-UID")):
    try:
        predictions = db_manager.get_user_predictions(user_firebase_uid, 1000)  # Get all
        
        if not predictions:
            return {
                "total_predictions": 0,
                "avg_confidence": 0,
                "bullish_calls": 0,
                "bearish_calls": 0,
                "stocks_analyzed": 0,
                "most_predicted_stock": None
            }
        
        # stats, bullish and bearish preds
        total = len(predictions)
        avg_confidence = sum(p['confidence'] for p in predictions) / total
        bullish = len([p for p in predictions if p['trend'] == 'Uptrend'])
        bearish = len([p for p in predictions if p['trend'] == 'Downtrend'])
        
        # most predicted for each user
        stock_counts = {}
        for p in predictions:
            stock_counts[p['stock']] = stock_counts.get(p['stock'], 0) + 1
        most_predicted = max(stock_counts.items(), key=lambda x: x[1])[0] if stock_counts else None
        
        return {
            "total_predictions": total,
            "avg_confidence": round(avg_confidence, 1),
            "bullish_calls": bullish,
            "bearish_calls": bearish,
            "stocks_analyzed": len(set(p['stock'] for p in predictions)),
            "most_predicted_stock": most_predicted
        }
        
    except Exception as e:
        print(f"Statistics error: {e}")
        return {"error": f"Failed to fetch statistics: {str(e)}"}

#explore page related backend data

@app.get("/explore-stocks")
def explore_data():
    try:
        # Add debugging for the Yahoo API call
        trending_url = "https://query1.finance.yahoo.com/v1/finance/trending/US"
        
        print(f"Making request to: {trending_url}")
        response = requests.get(trending_url)
        print(f"Response status: {response.status_code}")
        print(f"Response length: {len(response.text)}")
        print(f"First 200 chars: {response.text[:200]}")
        
        # Check for empty response
        if not response.text.strip():
            print("Empty response from Yahoo API")
            return {"error": "Empty response from trending API"}
        
        # Try to parse JSON
        try:
            trending_data = response.json()
        except Exception as json_error:
            print(f"JSON parsing failed: {json_error}")
            print(f"Raw response: {response.text[:500]}")
            return {"error": "Invalid JSON from trending API"}

        # Check if we got the expected structure
        if 'finance' not in trending_data:
            print(f"Unexpected response structure: {trending_data}")
            return {"error": "Unexpected API response structure"}

        #filter out stock symbols
        stock_symbols = []
        for quote in trending_data['finance']['result'][0]['quotes'][:30]:
            stock_symbols.append(quote['symbol'])
        
        all_stocks = []
        sectors_dict = {}

        for s in stock_symbols:
            try:
                ticker = yf.Ticker(s)
                hist = ticker.history(period="2d")
                info = ticker.info

                if len(hist) < 2:
                    continue

                curr_price = float(hist['Close'].iloc[-1])
                prev_price = float(hist['Close'].iloc[-2])
                price_change = curr_price - prev_price
                percent_change = (price_change / prev_price) * 100

                stock_data = {
                    'symbol': s,
                    'name': info.get('shortName', s)[:28],  
                    'price': curr_price,
                    'change': price_change,
                    'changePercent': percent_change,
                    'volume': int(hist['Volume'].iloc[-1]) if len(hist) > 0 else 0
                }

                all_stocks.append(stock_data)

                #secotr grping
                sector = info.get('sector', 'Other')
                if sector not in sectors_dict:
                    sectors_dict[sector] = []
                sectors_dict[sector].append(stock_data)
            
            except Exception as e: #for those stocks that cant load
                print(f"Failed to get data for {s}: {e}")
                continue    
        #sort into the 4 cats for explore page, gainers, loser etc.
        gainers_list = [stock for stock in all_stocks if stock['changePercent'] > 0]
        gainers_list.sort(key=lambda x: x['changePercent'], reverse=True)
        
        losers_list = [stock for stock in all_stocks if stock['changePercent'] < 0]
        losers_list.sort(key=lambda x: x['changePercent'])
        
        active_list = sorted(all_stocks, key=lambda x: x['volume'], reverse=True)
        
        sectors_data = {}
        for sector_name, stocks in sectors_dict.items():
            if len(stocks) >= 3:
                total_change = sum(stock['changePercent'] for stock in stocks)
                avg_change = total_change / len(stocks)
                
                top_performers = sorted(stocks, key=lambda x: x['changePercent'], reverse=True)
                
                sectors_data[sector_name] = {
                    'avg_change': avg_change,
                    'stock_count': len(stocks),
                    'top_stocks': top_performers[:4]
                }

        return {
            'trending': all_stocks[:15],
            'gainers': gainers_list[:12],
            'losers': losers_list[:12],
            'popular': active_list[:12],
            'sectors': sectors_data
        }   
        
    except Exception as e:
        print(f"Explore data error: {e}")
        return {"error": "Failed to fetch market data"}



 
    
