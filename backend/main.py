from fastapi import FastAPI

app = FastAPI()

@app.get("/predict")
def predict(stock: str = "AAPL"):
    return {
        "stock": stock,
        "predicted_price": 153.20,
        "confidence": 87,
        "volatility": "Moderate",
        "trend": "Strong Uptrend"
    }