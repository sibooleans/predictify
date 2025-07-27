import numpy as np
from sklearn.ensemble import RandomForestRegressor
from statsmodels.tsa.arima.model import ARIMA
import warnings
warnings.filterwarnings('ignore')
from services.stock_service import fetch_historical_prices, stock_current_price
from utils.helpers import (get_trading_info, obtain_volatility, get_sentiment, 
                          stock_smart_constraint, chart_title, chart_timeframe,
                          determine_period, generate_pred_timeline)
from models.response_models import Prediction
from datetime import datetime

#ARIMA Model

def simple_arima_prediction(prices: list, days_ahead: int, current_price: float):
    try:
        # Convert to returns (more stable than raw prices)
        returns = []
        for i in range(1, len(prices)):
            daily_return = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(daily_return)
        
        # Use last 30 days of returns
        recent_returns = returns[-25:] if len(returns) > 25 else returns
        
        if len(recent_returns) < 10:
            if len(recent_returns) >= 5:
                try:
                    model = ARIMA(recent_returns, order=(1,1,1))
                    fitted = model.fit()
                    forecast = fitted.forecast(steps=days_ahead)
                    
                    predicted_price = current_price
                    for return_pred in forecast:
                        predicted_price *= (1 + return_pred)
                    
                    # Apply constraints
                    max_change = 0.10 if days_ahead <= 3 else 0.15
                    min_price = current_price * (1 - max_change)
                    max_price = current_price * (1 + max_change)
                    predicted_price = max(min_price, min(max_price, predicted_price))
                    
                    return {
                        'predicted_price': predicted_price,
                        'confidence': 55,
                        'method': 'ARIMA_minimal_data',
                        'model_params': (1,1,1)
                    }
                except:
                    pass

                #fallback when impossible.

            avg_return = np.mean(recent_returns) if recent_returns else 0
            predicted_price = current_price * (1 + avg_return * days_ahead * 0.1)
            return {
                'predicted_price': predicted_price,
                'confidence': 40,
                'method': 'insufficient_data_fallback',
                'model_params': 'fallback'
            }
        
        # ARIMA strats in order of likely sucess
        
        arima_strategies = [
            (1,1,1), # Most common, fastest method
            (0,1,1), # Simple MA model
            (1,1,0), # Simple AR model
            (2,1,1), # More complex
            (1,1,2), # More complex
            (1,1,1), # Retry with better method
            (0,1,1), # Retry with better method
            (2,1,2), # Most complex, more time
            ]   
    
        best_model = None
        best_aic = float('inf')
        best_params = None
        total_time = 0
        max_time = 4.5
        
        #attempt to fix issue that arima takes LOADS of time
        import time
        
        for params in arima_strategies:
            if total_time >= max_time:
                print(f"ARIMA time budget exhausted: {total_time:.1f}s")
                break
            
            start_time = time.time()
            
            try:
                model = ARIMA(recent_returns, order=params)
            
                # methof fitting and time limit
                fitted = model.fit()
                
                
                fit_time = time.time() - start_time
                total_time += fit_time
                
                # Check if this is the best model so far
                if fitted.aic < best_aic:
                    best_aic = fitted.aic
                    best_model = fitted
                    best_params = params
                    print(f"ARIMA{params} succeeded in {fit_time:.2f}s, AIC: {fitted.aic:.2f}")
                
                # decent model and are running out of time, stop
                if best_aic < 0 and total_time > 3.0:
                    print(f"Good ARIMA model found, stopping early at {total_time:.1f}s")
                    break
                    
            except Exception as e:
                fit_time = time.time() - start_time
                total_time += fit_time
                print(f"ARIMA{params} failed in {fit_time:.2f}s: {str(e)[:50]}")
                continue
        
        # If we found a working ARIMA model, use it
        if best_model is not None:
            try:
                print(f"Using ARIMA{best_params} with AIC {best_aic:.2f}")
    
                forecast = best_model.forecast(steps=days_ahead)
                
                # Convert returns back to price
                predicted_price = current_price
                for return_pred in forecast:
                    predicted_price *= (1 + return_pred)
                
                # Calculate confidence based on model quality
                confidence = 60 
                if best_aic < -50:
                    confidence += 15  # great model
                elif best_aic < -20:
                    confidence += 10  # good model
                elif best_aic < 0:
                    confidence += 5   # decent model
                
                if len(recent_returns) > 20:
                    confidence += 5  # more data pts bonus
                
                # constraints
                max_change = 0.12 if days_ahead <= 3 else 0.18
                min_price = current_price * (1 - max_change)
                max_price = current_price * (1 + max_change)
                predicted_price = max(min_price, min(max_price, predicted_price))
                
                return {
                    'predicted_price': predicted_price,
                    'confidence': min(75, confidence),
                    'method': 'ARIMA_success',
                    'model_params': best_params,
                    'aic': best_aic,
                    'total_time': round(total_time, 2)
                }
                
            except Exception as e:
                print(f"ARIMA forecast failed: {e}")
                # model fitted but forecast failed - use model's fitted values
                try:
                    # use model's trend for prediction
                    fitted_values = best_model.fittedvalues
                    if len(fitted_values) > 0:
                        recent_trend = np.mean(fitted_values[-3:])
                        predicted_price = current_price * (1 + recent_trend * days_ahead)
                        
                        max_change = 0.10
                        min_price = current_price * (1 - max_change)
                        max_price = current_price * (1 + max_change)
                        predicted_price = max(min_price, min(max_price, predicted_price))
                        
                        return {
                            'predicted_price': predicted_price,
                            'confidence': 55,
                            'method': 'ARIMA_fitted_trend',
                            'model_params': best_params
                        }
                except:
                    pass
        # enhanced fallback in case of no model
        if len(recent_returns) >= 5:
            # Use multiple statistical approaches
            approaches = []
            
            # 1. exponential smoothing
            alpha = 0.3
            smoothed = recent_returns[0]
            for ret in recent_returns[1:]:
                smoothed = alpha * ret + (1 - alpha) * smoothed
            approaches.append(smoothed)
            
            # 2. weighted recent average
            weights = np.linspace(1, 3, len(recent_returns[-5:]))  
            weights = weights / weights.sum()
            weighted_avg = np.average(recent_returns[-5:], weights=weights)
            approaches.append(weighted_avg)
            
            # 3. mean reversion consideration
            last_return = recent_returns[-1]
            vol = np.std(recent_returns)
            if abs(last_return) > vol:  
                mean_rev = -last_return * 0.2 
            else:
                mean_rev = np.mean(recent_returns[-3:])
            approaches.append(mean_rev)
            
            # average the approaches
            combined_signal = np.mean(approaches)
            predicted_price = current_price * (1 + combined_signal * days_ahead * 0.4)
        else:
            # simple fallback
            avg_return = np.mean(recent_returns)
            predicted_price = current_price * (1 + avg_return * days_ahead * 0.2)
        
        # constraints
        max_change = 0.08 if days_ahead <= 3 else 0.12
        min_price = current_price * (1 - max_change)
        max_price = current_price * (1 + max_change)
        predicted_price = max(min_price, min(max_price, predicted_price))
        
        return {
            'predicted_price': predicted_price,
            'confidence': 45,
            'method': 'statistical_fallback_after_arima_failed',
            'model_params': 'stat_fallback',
            'arima_attempts': len(arima_strategies),
            'total_time': round(total_time, 2)
        }
        
    except Exception as e:
        print(f"Complete ARIMA failure: {e}")
        # emergency fallback
        predicted_price = current_price * (1 + np.random.normal(0, 0.005))
        return {
            'predicted_price': predicted_price,
            'confidence': 35,
            'method': 'emergency_fallback',
            'model_params': 'emergency'
        }
        
       
        

def fallback_prediction(prices: list, days_ahead: int, current_price: float):
    #if random forest fails. fall back to a simple trend extrapolation.
    try:
        if len(prices) > 10:
            #trend from recent prices
            recent_count = min(20, len(prices))  # Use last 20 days or all available
            recent_prices = prices[-recent_count:]
            
            #linear trend
            if len(recent_prices) >= 3:
                # Simple slope calculation
                x_vals = list(range(len(recent_prices)))
                y_vals = recent_prices
                
                #trend (change per day)
                n = len(recent_prices)
                sum_x = sum(x_vals)
                sum_y = sum(y_vals)
                sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
                sum_x2 = sum(x * x for x in x_vals)
                
                # linear regression slope
                if n * sum_x2 - sum_x * sum_x != 0:
                    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                else:
                    slope = 0
                
                # conservative trend
                trend_prediction = current_price + (slope * days_ahead * 0.3)  # 30% of full trend
            else:
                # in case of not enough data.
                avg_change = (recent_prices[-1] - recent_prices[0]) / len(recent_prices)
                trend_prediction = current_price + (avg_change * days_ahead * 0.1)
            
            # conservative constraints to keep control (fallback should be safe)
            if days_ahead <= 30:
                max_change_percent = 0.08  # 8% max for monthly fallback
            elif days_ahead <= 60:
                max_change_percent = 0.12  # 12% max for 2-month fallback
            else:
                max_change_percent = 0.15  # 15% max for longer fallback
            
            min_price = current_price * (1 - max_change_percent)
            max_price = current_price * (1 + max_change_percent)
            safe_prediction = max(min_price, min(max_price, trend_prediction))
            
            # confidence based off quality of datas
            if len(prices) > 30:
                confidence = 40
            elif len(prices) > 20:
                confidence = 35
            else:
                confidence = 30
            
            return {
                'predicted_price': safe_prediction,
                'confidence': confidence,
                'method': 'trend_fallback',
                'data_points': len(recent_prices)
            }
            
        elif len(prices) >= 3:
            # minimal change
            recent_change = (prices[-1] - prices[-3]) / 2  # Average of last 2 days
            minimal_prediction = current_price + (recent_change * days_ahead * 0.05)  # Very conservative
            
            # constraints
            max_change = current_price * 0.05  # 5% max when very little data
            min_price = current_price - max_change
            max_price = current_price + max_change
            safe_prediction = max(min_price, min(max_price, minimal_prediction))
            
            return {
                'predicted_price': safe_prediction,
                'confidence': 25,
                'method': 'minimal_data_fallback',
                'data_points': len(prices)
            }
        
        else:
            #really really suay suay no data - return current price
            return {
                'predicted_price': current_price,
                'confidence': 20,
                'method': 'no_change_fallback',
                'data_points': len(prices)
            }
        
    except Exception as e:
        print(f"Even fallback prediction failed: {e}")
        # for emergency also just return current price
        return {
            'predicted_price': current_price,
            'confidence': 15,
            'method': 'emergency_fallback',
            'error': str(e)
        }
def random_forest_prediction(prices: list, days_ahead: int, current_price: float):
    try:
        if len(prices) < 50:
            print(f"Not enough price data: {len(prices)} points, need at least 50")
            return fallback_prediction(prices, days_ahead, current_price)
        
        daily_returns = []
        for i in range(1, min(len(prices), 252)):  # Last year of data max
            if prices[-i-1] > 0:  # Avoid division by zero
                daily_return = (prices[-i] - prices[-i-1]) / prices[-i-1]
                if abs(daily_return) < 0.5:  # Filter out extreme outliers (50%+ moves)
                    daily_returns.append(daily_return)
        
        if len(daily_returns) < 20:
            print(f"Not enough valid daily returns: {len(daily_returns)}")
            return fallback_prediction(prices, days_ahead, current_price)
        
        # realistic constraints based on historical volatility
        historical_volatility = np.std(daily_returns)
        if historical_volatility == 0:
            print("Zero volatility detected")
            return fallback_prediction(prices, days_ahead, current_price)
        '''annual_volatility = historical_volatility * np.sqrt(252)  # Annualized volatility
        
        # annual volatility for realistic bounds
        time_factor = days_ahead / 252  # Fraction of a year
        expected_volatility = annual_volatility * np.sqrt(time_factor)'''
        #pretty much the same method as under the predict function, just now moving it out.
        
        X = []
        y = []
        
        size = 20

        min_data_needed = size + days_ahead + 10  # Extra buffer

        if len(prices) < min_data_needed:
            print(f"Insufficient data for windowing: need {min_data_needed}, have {len(prices)}")
            return fallback_prediction(prices, days_ahead, current_price)
        
        for i in range(size, len(prices) - days_ahead):
            try:
                window = prices[i-size:i]
                current_window_price = prices[i]
                future_price = prices[i + days_ahead]
            
                if (len(window) != size or 
                    current_window_price <= 0 or 
                    future_price <= 0 or
                    any(p <= 0 for p in window)):
                    continue
                
                # calculate features with error checking
                try:
                    features = [
                        np.mean(window[-5:]) / current_window_price,
                        np.mean(window[-10:]) / current_window_price,
                        np.mean(window[-20:]) / current_window_price,
                        (window[-1] - window[-5]) / window[-5] if len(window) >= 5 and window[-5] > 0 else 0,
                        (window[-1] - window[-10]) / window[-10] if len(window) >= 10 and window[-10] > 0 else 0,
                        np.std(window[-10:]) / np.mean(window[-10:]) if np.mean(window[-10:]) > 0 else 0,
                        (window[-1] - window[0]) / window[0] if window[0] > 0 else 0,
                        (np.max(window) - np.min(window)) / np.mean(window) if np.mean(window) > 0 else 0
                    ]
                    
                    # validate features (no NaN, no infinity)
                    if any(not np.isfinite(f) for f in features):
                        continue
                    
                    # calculate target (relative change)
                    relative_change = (future_price - current_window_price) / current_window_price
                    
                    # validate target
                    if not np.isfinite(relative_change) or abs(relative_change) > 1.0: 
                        continue
                    
                    X.append(features)
                    y.append(relative_change)
                    
                except (ZeroDivisionError, ValueError, IndexError):
                    continue
            
            except Exception as e:
                print(f"Error processing window {i}: {e}")
                continue
        
        # got enpugh training data?
        if len(X) < 20:  #min20 samples
            print(f"Not enough valid training samples: {len(X)}, need at least 20")
            return fallback_prediction(prices, days_ahead, current_price)
        
        print(f"Training Random Forest with {len(X)} samples")
        
        # convert to numpy arrays with validation
        try:
            X = np.array(X)
            y = np.array(y)
            
            # Check for empty arrays or wrong shapes
            if X.shape[0] == 0 or y.shape[0] == 0:
                print(f"Empty arrays after conversion: X shape {X.shape}, y shape {y.shape}")
                return fallback_prediction(prices, days_ahead, current_price)
            
            if X.shape[0] != y.shape[0]:
                print(f"Mismatched array sizes: X {X.shape[0]}, y {y.shape[0]}")
                return fallback_prediction(prices, days_ahead, current_price)
                
        except Exception as e:
            print(f"Error converting to numpy arrays: {e}")
            return fallback_prediction(prices, days_ahead, current_price)
        
        
        # training model
        try:
            model = RandomForestRegressor(n_estimators=50, 
                                        random_state=42,
                                        max_depth=8,
                                        min_samples_split=5,
                                        min_samples_leaf=2)
            model.fit(X, y)

        except Exception as e:
            print(f"Error training Random Forest: {e}")
            return fallback_prediction(prices, days_ahead, current_price)

        
        # prediction w validaion
        try:
            current_window = prices[-size:]
            if len(current_window) != size or any(p <= 0 for p in current_window):
                print("Invalid current window for prediction")
                return fallback_prediction(prices, days_ahead, current_price)
        
            current_features = [
                np.mean(current_window[-5:]) / current_price,
                np.mean(current_window[-10:]) / current_price,
                np.mean(current_window[-20:]) / current_price,
                (current_window[-1] - current_window[-5]) / current_window[-5] if len(current_window) >= 5 else 0,
                (current_window[-1] - current_window[-10]) / current_window[-10] if len(current_window) >= 10 else 0,
                np.std(current_window[-10:]) / np.mean(current_window[-10:]) if np.mean(current_window[-10:]) > 0 else 0,
                (current_window[-1] - current_window[0]) / current_window[0],
                (np.max(current_window) - np.min(current_window)) / np.mean(current_window) if np.mean(current_window) > 0 else 0
            ]
        
            if any(not np.isfinite(f) for f in current_features):
                print("Invalid features for prediction")
                return fallback_prediction(prices, days_ahead, current_price)

            predicted_relative_change = model.predict([current_features])[0]

            if not np.isfinite(predicted_relative_change):
                print("Model returned invalid prediction")
                return fallback_prediction(prices, days_ahead, current_price)
            
        except Exception as e:
            print(f"Error making prediction: {e}")
            return fallback_prediction(prices, days_ahead, current_price)
        

        max_change = stock_smart_constraint(historical_volatility, days_ahead)
        predicted_relative_change = np.clip(predicted_relative_change, -max_change, max_change)

        predicted_price = current_price * (1 + predicted_relative_change)

        #relativity to tevert to long term trends over months
        '''if days_ahead > 30:
        long_term_return = np.mean(daily_returns) * days_ahead
        predicted_relative_change = predicted_relative_change * 0.7 + long_term_return * 0.3'''

        # confidence
        score = model.score(X, y)
        confidence = max(45, min(70, int(score * 85)))

        if days_ahead > 30: #reduce confidence for long predicts
            confidence_penalty = min(15, (days_ahead - 30) * 0.3)
            confidence -= confidence_penalty
        
        final_confidence = max(40, int(confidence))
        return {
            'predicted_price': predicted_price,
            'confidence': final_confidence,
            'method': 'RandomForest',
            'training_samples': len(X)
        }
    
    except Exception as e:
        print(f"Random Forest error: {e}")
        return fallback_prediction(prices, days_ahead, current_price)
    
def get_model_info(days_ahead: int):
   #courtesy of frontend
    if days_ahead <= 7:
        return {
            'model_name': 'Short-term Pattern Analysis',
            'model_code': 'ARIMA-S',
            'algorithm': 'ARIMA Time Series Analysis',
            'description': 'Analyzes recent price movements and patterns',
            'timeframe': '1-7 days',
            'approach': 'Time series forecasting with autocorrelation analysis',
            'best_for': 'Short-term predictions based on recent trends',
            'confidence_range': '60-75%'
        }
    else:
        return {
            'model_name': 'Long-term Pattern Recognition',
            'model_code': 'RF-L', 
            'algorithm': 'Random Forest Machine Learning',
            'description': 'Machine learning analysis of historical patterns',
            'timeframe': '8+ days',
            'approach': 'Ensemble learning with technical indicators',
            'best_for': 'Longer predictions using historical data patterns',
            'confidence_range': '55-70%'
        }

def predict(stock: str = "AAPL", days_ahead: int = 1):
    try:

        stock = stock.upper() #so that even aapl becomes AAPL
        if days_ahead < 1 or days_ahead > 90:
            return {"error": "Days ahead must be between 1 and 90"}

        trading_info = get_trading_info(days_ahead)

        history_period = determine_period(days_ahead)
        model_data, historical_data = fetch_historical_prices(stock,
            period = history_period, days_ahead = days_ahead)
        current_price_data = stock_current_price(stock)

        if model_data is None or current_price_data is None:
            return {"error": "Invalid stock symbol or unable ot fetch data."}
        
        x, y = model_data
        prices = y.ravel().tolist()
        current_price = current_price_data["current_price"]

        if len(prices) < 10: #min data
            return {"error": "Insufficient historical data for prediction"}
        
        if days_ahead <= 7:
            # SHORT-TERM: ARIMA
            prediction_result = simple_arima_prediction(prices, days_ahead, current_price)
            model_info = get_model_info(days_ahead)
        else:
            # LONG-TERM: Random Forest
            prediction_result =random_forest_prediction(prices, days_ahead, current_price)
            model_info = get_model_info(days_ahead)

        predicted_price = prediction_result['predicted_price']
        confidence = prediction_result['confidence']    
        sentiment = get_sentiment(stock)
        vol = obtain_volatility(prices)
        
        result = Prediction(
            stock = stock.upper(),
            predicted_price = float(predicted_price),
            confidence = confidence,
            volatility = vol,
            trend = "Uptrend" if predicted_price > current_price_data["current_price"] else "Downtrend",
            sentiment = sentiment,
            timestamp = datetime.now().isoformat(),
            current_price = current_price_data["current_price"],
            price_change = current_price_data["price_change"],
            price_change_percent = current_price_data["price_change_percent"]
        )
        #timeline
        pred_timeline = generate_pred_timeline(
            current_price_data["current_price"], 
            float(predicted_price), 
            days_ahead,
            vol
        )

        api_response = {
            "prediction": result.model_dump(),
            "historical_data": historical_data,
            "prediction_timeline": pred_timeline,
            "chart_info": {
                "title": chart_title(days_ahead),
                "timeframe_days": chart_timeframe(days_ahead),
                "data_period": history_period
            },
            "trading info": trading_info,
            "model_info": {
                **model_info,
                "method_used": prediction_result['method'],
                "model_params": prediction_result.get('model_params', 'N/A')
            }
        }

        return api_response
        
    except Exception as e:
        print(f"Prediction error: {e}")
        return {"error": f"Prediction failed: {str(e)}"}

