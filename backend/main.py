from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# in-memory history store, will be updating this with calls
history = []

# response model for history (this the import from pydantic)
class Prediction(BaseModel):
    stock: str
    predicted_price: float
    confidence: int
    volatility: str
    trend: str
    timestamp: str

# predict endpoint
@app.get("/predict")
def predict(stock: str = "AAPL"):
    result = {
        "stock": stock,
        "predicted_price": 153.20,
        "confidence": 87,
        "volatility": "Moderate",
        "trend": "Strong Uptrend",
        "timestamp": datetime.datetime.now().isoformat()
    }
    history.append(result)
    return result

# history endpoint
@app.get("/history", response_model=List[Prediction])
def get_history():
    return history
