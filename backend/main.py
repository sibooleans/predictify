from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional
from models.response_models import Prediction
from services.prediction_service import predict as get_prediction
from services.stock_service import get_historical_data
from config.database import db_manager

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
    

 
    
