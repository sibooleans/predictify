import { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet } from 'react-native';

type Prediction = {
  stock: string;
  predicted_price: number;
  confidence: number;
  volatility: string;
  trend: string;
};

export default function PredictScreen() {
  const [stock, setStock] = useState('');
  const [result, setResult] = useState<Prediction | null>(null);

  const getPrediction = async () => {
    if (!stock.trim()) {
      alert("Please enter a stock symbol!");
      return;
    }

    try {
      const response = await fetch(`http://192.168.88.7:8000/predict?stock=${stock}`);
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error fetching prediction:', error);
      alert("Something went wrong while fetching prediction.");
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Predictify</Text>

      <TextInput
        style={styles.input}
        placeholder="Enter stock symbol (e.g. AAPL)"
        placeholderTextColor="#aaa"
        value={stock}
        onChangeText={setStock}
      />

      <Button title="Predict" onPress={getPrediction} />


      {result && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>{result.stock} Forecast</Text>
          <Text style={styles.cardLine}>💵 Predicted Price: ${result.predicted_price}</Text>
          <Text style={styles.cardLine}>📊 Confidence: {result.confidence}%</Text>
          <Text style={styles.cardLine}>⚠️ Volatility: {result.volatility}</Text>
          <Text style={styles.cardLine}>📈 Trend: {result.trend}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    paddingTop: 60,
    flex: 1,
    backgroundColor: '#000',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#00ccff',
    marginBottom: 20,
    textAlign: 'center',
  },
  input: {
    borderColor: '#ccc',
    borderWidth: 1,
    padding: 10,
    marginBottom: 10,
    color: 'white',
  },
  link: {
    color: '#00ccff',
    marginTop: 20,
    textAlign: 'center',
  },
  card: {
    backgroundColor: '#1e1e1e',
    borderRadius: 12,
    padding: 20,
    marginTop: 25,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 5,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#00ccff',
    marginBottom: 10,
  },
  cardLine: {
    fontSize: 16,
    color: 'white',
    marginBottom: 6,
  },
});

/*import { useState } from 'react';
import { View, Text, TextInput, Button, ActivityIndicator,
  ScrollView, StyleSheet, } from 'react-native';

type Prediction = {
  stock: string;
  predicted_price: number;
  confidence: number;
  volatility: string;
  trend: string;
};

export default function PredictScreen() {
  const [stock, setStock] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<Prediction | null>(null);
  const [history, setHistory] = useState<Prediction[]>([]);

  const getPrediction = async () => {
    const trimmed = stock.trim().toUpperCase();
    if (!trimmed) {
      setError('Please enter a valid stock symbol.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await fetch(`http://192.168.88.7:8000/predict?stock=${trimmed}`);
      if (!response.ok) throw new Error('Server returned error');

      const data: Prediction = await response.json();
      setResult(data);
      setHistory(prev => [data, ...prev.slice(0, 4)]); // Show last 5
    } catch (err) {
      console.error(err);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      <Text style={styles.title}>Stock Prediction</Text>

      <TextInput
        style={styles.input}
        placeholder="e.g., AAPL"
        placeholderTextColor="#aaa"
        value={stock}
        onChangeText={setStock}
      />

      <Button title="Predict" onPress={getPrediction} />

      {loading && <ActivityIndicator size="large" style={{ marginTop: 20 }} />}

      {error ? <Text style={styles.error}>{error}</Text> : null}

      {result && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>{result.stock} Forecast</Text>
          <Text style={styles.cardLine}>💵 Predicted Price: ${result.predicted_price}</Text>
          <Text style={[styles.cardLine, getConfidenceStyle(result.confidence)]}>
            📊 Confidence: {result.confidence}%
          </Text>
          <Text style={styles.cardLine}>⚠️ Volatility: {result.volatility}</Text>
          <Text style={styles.cardLine}>📈 Trend: {result.trend}</Text>
        </View>
      )}

      {history.length > 1 && (
        <View style={styles.history}>
          <Text style={styles.historyTitle}>Recent Predictions</Text>
          {history.slice(1).map((item, idx) => (
            <Text key={idx} style={styles.historyItem}>
              {item.stock}: ${item.predicted_price} ({item.confidence}%)
            </Text>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

function getConfidenceStyle(confidence: number) {
  return {
    color: confidence >= 80 ? 'lightgreen' : confidence >= 60 ? 'orange' : 'red',
  };
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
    paddingHorizontal: 16,
  },
  scrollContent: {
    paddingTop: 60,
    paddingBottom: 40,
    alignItems: 'center',
  },
  title: {
    fontSize: 26,
    fontWeight: 'bold',
    color: '#00ccff',
    marginBottom: 16,
    textAlign: 'center',
  },
  input: {
    borderColor: '#555',
    borderWidth: 1,
    borderRadius: 8,
    color: 'white',
    padding: 10,
    width: '100%',
    marginBottom: 10,
  },
  error: {
    color: 'red',
    marginTop: 12,
    fontSize: 14,
  },
  card: {
    backgroundColor: '#1e1e1e',
    borderRadius: 12,
    padding: 20,
    marginTop: 20,
    width: '100%',
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#00ccff',
    marginBottom: 10,
  },
  cardLine: {
    fontSize: 16,
    color: '#fff',
    marginBottom: 6,
  },
  history: {
    marginTop: 30,
    width: '100%',
  },
  historyTitle: {
    fontSize: 18,
    color: '#aaa',
    marginBottom: 6,
  },
  historyItem: {
    fontSize: 14,
    color: '#ccc',
    marginBottom: 4,
  },
});

import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet, ScrollView } from 'react-native';

type Prediction = {
  stock: string;
  predicted_price: number;
  confidence: number;
  volatility: string;
  trend: string;
};

export default function PredictScreen() {
  const [stock, setStock] = useState('');
  const [result, setResult] = useState<Prediction | null>(null);
  const [history, setHistory] = useState<Prediction[]>([]);

  const getPrediction = async () => {
    if (!stock.trim()) {
      alert('Please enter a stock symbol!');
      return;
    }

    try {
      const response = await fetch(`http://192.168.88.7:8000/predict?stock=${stock}`);
      const data = await response.json();
      setResult(data);
      setHistory([data, ...history]); // Add new result to top of history
    } catch (error) {
      console.error('Error fetching prediction:', error);
      alert('Failed to fetch prediction.');
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Predictify</Text>

      <TextInput
        style={styles.input}
        placeholder="Enter stock symbol (e.g., AAPL)"
        placeholderTextColor="#aaa"
        value={stock}
        onChangeText={setStock}
      />

      <Button title="PREDICT" onPress={getPrediction} />

      {result && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>{result.stock} Forecast</Text>
          <Text>💵 Predicted Price: ${result.predicted_price}</Text>
          <Text>📊 Confidence: {result.confidence}%</Text>
          <Text>⚠️ Volatility: {result.volatility}</Text>
          <Text>📈 Trend: {result.trend}</Text>
        </View>
      )}

      {history.length > 0 && (
        <View style={styles.historyContainer}>
          <Text style={styles.historyTitle}>Prediction History</Text>
          {history.map((item, index) => (
            <View key={index} style={styles.historyCard}>
              <Text style={styles.historyStock}>{item.stock}</Text>
              <Text>💵 ${item.predicted_price}</Text>
              <Text>📊 {item.confidence}%</Text>
              <Text>⚠️ {item.volatility}</Text>
              <Text>📈 {item.trend}</Text>
            </View>
          ))}
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
    marginBottom: 20,
    textAlign: 'center',
  },
  input: {
    borderColor: '#ccc',
    borderWidth: 1,
    padding: 10,
    marginBottom: 10,
    color: 'white',
  },
  card: {
    backgroundColor: '#1e1e1e',
    borderRadius: 12,
    padding: 20,
    marginTop: 25,
    marginBottom: 15,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#00ccff',
    marginBottom: 10,
  },
  historyContainer: {
    marginTop: 30,
  },
  historyTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ccc',
    marginBottom: 10,
  },
  historyCard: {
    backgroundColor: '#121212',
    padding: 12,
    marginBottom: 12,
    borderRadius: 8,
  },
  historyStock: {
    fontWeight: 'bold',
    fontSize: 16,
    color: '#fff',
    marginBottom: 4,
  },
});*/





