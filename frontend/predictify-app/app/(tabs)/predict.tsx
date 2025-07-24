import { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet, 
  TouchableOpacity, ActivityIndicator, ScrollView} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { format, addDays } from 'date-fns';



export default function PredictScreen() {
  const [stock, setStock] = useState('');
  const [daysAhead, setDaysAhead] = useState(1);
  const [result, setResult] = useState<Prediction | null>(null);
  const [loading, setLoading] = useState(false);

  type Prediction = {
    stock: string;
    predicted_price: number;
    confidence: number;
    volatility: string;
    trend: string;
    sentiment: string;
  }

  const getPrediction = async () => {
    if (!stock.trim()) {
      alert("Please enter a stock symbol!");
      return;
    }
    setLoading(true);
    try {
      const response = await fetch(`https://predictify-zcef.onrender.com/predict?stock=${stock}&days_ahead=${daysAhead}`);
      //got to switch this out to ngrok. figure out the debugging.
      //ngrok tunnel breaks aft 2 hrs??
      const data = await response.json();
      setResult(data);
    } catch (error) {
      //when unable to connect to backend, this error takes AGES to show up.
      //gotta look into reducing the timing of error to show up too.
      console.error('Error fetching prediction:', error);
      alert("Something went wrong while fetching prediction.");
    } finally {
      setLoading(false);
    }
  };

  const predictedDate = format(addDays(new Date(), daysAhead), 'PPP');

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>📊 Predictify</Text>

      <View style={styles.inputGroup}>
        <Text style={styles.label}> Ticker</Text>
        <TextInput
          style={styles.input}
          placeholder="Enter stock symbol (e.g. AAPL)"
          placeholderTextColor="#aaa"
          value={stock}
          onChangeText={setStock}
        />
      </View>

      <View style={styles.inputGroup}>
        <Text style={styles.label}> Days Ahead</Text>
        <TextInput
          style={styles.input}
          placeholder="Timeline e.g. 3 days"
          placeholderTextColor="#aaa"
          keyboardType="numeric"
          value={daysAhead.toString()}
          onChangeText={(val) => setDaysAhead(parseInt(val) || 1)}
        />
      </View>

      <TouchableOpacity style={styles.button} onPress={getPrediction}>
        <Text style={styles.buttonText}> Predict</Text>
      </TouchableOpacity>

      {loading && (<ActivityIndicator size="large" 
      color="ooccff" 
      style={{marginTop: 20}} 
      />
    )}

      {result && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>{result.stock.toUpperCase()} Forecast</Text>

          <View style={styles.metricRow}>
            <Text style={styles.metricLabel}>💵 Predicted Price:</Text>
            <Text style={styles.metricValue}>${result.predicted_price.toFixed(2)}</Text>
          </View>
          <View style={styles.metricRow}>
            <Text style={styles.metricLabel}>🔐 Confidence:</Text>
            <Text style={styles.metricValue}>{result.confidence}%</Text>
          </View>
          <View style={styles.metricRow}>
            <Text style={styles.metricLabel}>📉 Volatility:</Text>
            <Text style={styles.metricValue}>{result.volatility}</Text>
          </View>
          <View style={styles.metricRow}>
            <Text style={styles.metricLabel}>⬆️ Trend:</Text>
            <Text style={styles.metricValue}>{result.trend}</Text>
          </View>
          <View style={styles.metricRow}>
            <Text style={styles.metricLabel}>😊 Sentiment:</Text>
            <Text style={styles.metricValue}>{result.sentiment}</Text>
          </View>
          <View style={styles.metricRow}>
            <Text style={styles.metricLabel}>🕒 Predicted Date:</Text>
            <Text style={styles.metricValue}>{predictedDate}</Text>
          </View>

          <View style={styles.assumptionBox}>
            <Text style={styles.assumptionTitle}>📌 Assumptions</Text>
            <Text style={styles.assumptionText}>
              Prediction based on historical data using a Random Forest model. Volatility is estimated and sentiment is derived from headlines.
            </Text>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    paddingTop: 60,
    backgroundColor: '#000',
    flexGrow: 1,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#00ccff',
    marginBottom: 25,
    textAlign: 'center',
  },
  inputGroup: {
    marginBottom: 15,
  },
  label: {
    color: '#ccc',
    marginBottom: 5,
    fontSize: 16,
  },
  input: {
    borderColor: '#555',
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    color: 'white',
    backgroundColor: '#111',
  },
  button: {
    backgroundColor: '#00ccff',
    borderRadius: 8,
    padding: 15,
    marginTop: 10,
  },
  buttonText: {
    textAlign: 'center',
    fontWeight: 'bold',
    color: '#000',
    fontSize: 16,
  },
  card: {
    backgroundColor: '#1e1e1e',
    borderRadius: 12,
    padding: 20,
    marginTop: 30,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 5,
  },
  cardTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#00ccff',
    marginBottom: 15,
    textAlign: 'center',
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  metricLabel: {
    color: '#ccc',
    fontSize: 16,
  },
  metricValue: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
  assumptionBox: {
    backgroundColor: '#111',
    padding: 12,
    borderRadius: 10,
    marginTop: 20,
  },
  assumptionTitle: {
    color: '#00ccff',
    fontWeight: 'bold',
    marginBottom: 8,
  },
  assumptionText: {
    color: '#ccc',
    fontSize: 14,
  },
});