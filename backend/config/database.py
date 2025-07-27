import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import Optional, Dict, Any, List

class DatabaseManager:
    def __init__(self):
        self.connection_string = os.getenv('DATABASE_URL')
        if not self.connection_string:
            raise ValueError("DATABASE_URL environment variable not set!")

    def get_connection(self):
        try:
            db_conn = psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor,
                sslmode='require'
            )
            return db_conn
        except Exception as e:
            print(f"Database connection error: {e}")
            raise
    
    def create_tables(self):
        #create tables for sql
        db_conn = self.get_connection()
        cursor = db_conn.cursor()
        
        try:
            # user list - add usenrmae
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    firebase_uid VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # list of predictions for history pg
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    stock_symbol VARCHAR(10) NOT NULL,
                    predicted_price DECIMAL(10,2) NOT NULL,
                    current_price DECIMAL(10,2) NOT NULL,
                    price_change DECIMAL(10,2) NOT NULL,
                    price_change_percent DECIMAL(5,2) NOT NULL,
                    days_ahead INTEGER NOT NULL,
                    confidence INTEGER NOT NULL,
                    volatility VARCHAR(20),
                    trend VARCHAR(20),
                    sentiment VARCHAR(20),
                    model_used VARCHAR(50),
                    prediction_date DATE NOT NULL,
                    target_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    actual_price DECIMAL(10,2) NULL,
                    accuracy_checked BOOLEAN DEFAULT FALSE,
                    accuracy_percentage DECIMAL(5,2) NULL
                );
            """)
            
            #indexing for db
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON predictions(user_id);
                CREATE INDEX IF NOT EXISTS idx_predictions_stock_symbol ON predictions(stock_symbol);
                CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at);
                CREATE INDEX IF NOT EXISTS idx_users_firebase_uid ON users(firebase_uid);
            """)

            db_conn.commit()
            print("Database tables created successfully")

        except Exception as e:
            db_conn.rollback()
            print(f"Error creating tables: {e}")
            raise
        finally:
            cursor.close()
            db_conn.close()
        
    def createorget_user(self, firebase_uid: str, email: str) -> int:
    #get user id of existing user or make new
        db_conn = self.get_connection()
        cursor = db_conn.cursor()

        try:
            # find use ralr there
            cursor.execute(
                "SELECT id FROM users WHERE firebase_uid = %s",
                (firebase_uid,)
            )
            user = cursor.fetchone()
            
            if user:
                return user['id']
            
            # creaying new user
            cursor.execute(
                """INSERT INTO users (firebase_uid, email) 
                   VALUES (%s, %s) RETURNING id""",
                (firebase_uid, email)
            )
            user_id = cursor.fetchone()['id']
            db_conn.commit()
            print(f"Created new user: {email}")
            return user_id
            
        except Exception as e:
            db_conn.rollback()
            print(f"Error managing user: {e}")
            raise
        finally:
            cursor.close()
            db_conn.close()

    def save_prediction(self, user_firebase_uid: str, prediction_data: Dict[str, Any]) -> bool:
        #saving to db
        db_conn = self.get_connection()
        cursor = db_conn.cursor()
        
        try:
            # find user id
            user_id = self.createorget_user(
                user_firebase_uid, 
                prediction_data.get('email', 'unknown@email.com')
            )
            
            pred = prediction_data.get('prediction', {})
    
            cursor.execute("""
                INSERT INTO predictions (
                    user_id, stock_symbol, predicted_price, current_price,
                    price_change, price_change_percent, days_ahead, confidence,
                    volatility, trend, sentiment, model_used, prediction_date, target_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                pred.get('stock'),
                pred.get('predicted_price'),
                pred.get('current_price'),
                pred.get('price_change'),
                pred.get('price_change_percent'),
                prediction_data.get('days_ahead', 1),
                pred.get('confidence'),
                pred.get('volatility'),
                pred.get('trend'),
                pred.get('sentiment'),
                prediction_data.get('model_info', {}).get('method_used', 'Unknown'),
                prediction_data.get('trading_info', {}).get('target_date', 'today'),
                prediction_data.get('trading_info', {}).get('target_date')
            ))
            
            db_conn.commit()
            print(f"Saved prediction for {pred.get('stock')}")
            return True
            
        except Exception as e:
            db_conn.rollback()
            print(f"Error saving prediction: {e}")
            return False
        finally:
            cursor.close()
            db_conn.close()
    
    def get_user_predictions(self, user_firebase_uid: str, limit: int = 50) -> List[Dict[str, Any]]:
        #predictions for specific userid
        db_conn = self.get_connection()
        cursor = db_conn.cursor()
        
        try:
            cursor.execute("""
                SELECT p.*, u.email 
                FROM predictions p
                JOIN users u ON p.user_id = u.id
                WHERE u.firebase_uid = %s
                ORDER BY p.created_at DESC
                LIMIT %s
            """, (user_firebase_uid, limit))
            
            predictions = cursor.fetchall()
            
            formatted_predictions = []
            for prediction in predictions:
                formatted_predictions.append({
                    'id': prediction['id'],
                    'stock': prediction['stock_symbol'],
                    'predicted_price': float(prediction['predicted_price']),
                    'current_price': float(prediction['current_price']),
                    'price_change': float(prediction['price_change']),
                    'price_change_percent': float(prediction['price_change_percent']),
                    'confidence': prediction['confidence'],
                    'volatility': prediction['volatility'],
                    'trend': prediction['trend'],
                    'sentiment': prediction['sentiment'],
                    'timestamp': prediction['created_at'].isoformat(),
                    'days_ahead': prediction['days_ahead'],
                    'model_used': prediction['model_used'],
                    'target_date': prediction['target_date'].isoformat() if prediction['target_date'] else None
                })
            
            return formatted_predictions
            
        except Exception as e:
            print(f"Error fetching predictions: {e}")
            return []
        finally:
            cursor.close()
            db_conn.close()
        
db_manager = DatabaseManager()
        



