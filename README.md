# predictify
Smarter stock predictions for Beginner Investors.

PROJECT OVERVIEW

This is a mobile stock prediction app that is designed to help beginner investors understand short term stock trends and apply it. We provide simplified forecasts based on historical price data, offering a clean UI with insights such as predicted price, volatility, trend direction, and confidence percentage.

PROPOSED LEVEL

The proposed level for the project is Apollo 11. 
While our milestone 1 submission has focused mainly on coming up with a working end-to-end system with core functionality, we have active plans to add additional features such as sentiment analysis, chart visualizations, and a multi-stock dashboard. We are also now preparing to support user testing and will explore deployment for mobile access beyond local devices.

PROBLEM MOTIVATION

Loads of student are interested in investing but many are unaware of where to start. This is a problem that personally even I encountered. Existing stock apps are often cluttered with jargon and focused on advanced traders. Our app Predictify aims to bridge that gap with a clean educational tool that helps users build intuition about price movements, without diving into indicators that are too complicated. 

USER STORIES

As a student curious about the stock market, I want to enter a stock ticker and get a simple prediction so I can better understand short-term price movement.

As a beginner investor, I want to know how confident the prediction is so I can make more informed decisions.

As a casual user, I want to get insights without needing a brokerage account or making real trades.

MILESTONE 1 CORE FEATURES

Stock symbol input (e.g. “AAPL”)
Backend prediction API using FastAPI
Simple linear regression model (mocked for now)
Mobile UI built with React Native (Expo)
Forecast card showing:
- Predicted price
- Confidence level
- Volatility category
- Trend direction
View a mini price chart showing the last 5 days of historical movement

FUTURE FEATURES

Sentiment analysis using headlines/tweets (VADER)
Chart view of recent price history
Alerts when predicted price deviates significantly
Save/search history or watchlist
Compare multiple stocks side-by-side

TECH STACK 

Layer -	Tools Used
Frontend - React Native (Expo)
Backend - FastAPI (Python)
Model - Linear Regression (placeholder)
Hosting - Local testing via mobile preview
Version Control - Git + GitHub

HOW TO RUN THE APP 

Backend

cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload

Frontend

cd frontend
npx expo start

Make sure your phone and computer are on the same Wifi network so that Expo to connect to the backend.

API Endpoint

GET /predict?stock=AAPL
Returns a JSON object like:

{
  "stock": "AAPL",
  "predicted_price": 153.25,
  "confidence": 88.2,
  "volatility": "Moderate",
  "trend": "Upward"
}

SOFTWARE ENGINEERING PRACTICES

- Modular code structure with separation of frontend and backend
- Version control with GitHub and commit tracking
- Clear error handling and debugging in API fetches
- UI state managed via React Hooks (useState)
- Team collaboration via shared repository

KNOWN ISSUES 

- No database or user authentication yet
- Only supports 1-stock prediction at a time
- Prediction model is a placeholder (linear regression only)
- Frontend does not persist history

WHATS NEXT 

- Sentiment analysis (VADER) from headlines
- Multi-stock dashboard
- Chart visualization of stock history
- Save prediction history locally
- Optional deployment for external testers

AUTHORS

Sibi Nidharsan and Shreyas Khuntia 

