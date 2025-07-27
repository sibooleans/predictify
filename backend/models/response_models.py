from pydantic import BaseModel
from typing import List, Dict, Any

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