from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from models.response_models import Prediction
from services.prediction_service import prediction as get_prediction
from services.stock_service import get_historical_data

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

@app.get("/")
def root():
    print("[DEBUG] Hello from updated root!")
    return {"message": "Backend is running."}

@app.head("/")
def head_root():
    return {}

# predict endpoint
@app.get("/predict")
def predict(stock: str = "AAPL", days_ahead: int = 1):
    try:
        result = get_prediction(stock, days_ahead)
        
        if "prediction" in result:
            history.append(result["prediction"])
        
        return result
    except Exception as e:
        print(f"Prediction error: {e}")
        return {"error": f"Prediction failed: {str(e)}"}

@app.head("/predict")
def head_predict(stock: str = "AAPL"):
    return {}

# history endpoint
@app.get("/history")
def get_history():
    return history

@app.head("/history")
def head_history():
    return {}

#endpoint for js historical data
@app.get("/historical/{symbol}")
def historical_data(symbol: str, period: str = "1mo"):
    return get_historical_data(symbol, period)