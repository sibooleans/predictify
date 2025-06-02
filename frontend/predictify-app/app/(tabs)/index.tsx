import MiniChart from './MiniChart'; 

type Prediction = {
  stock: string;
  predicted_price: number;
  confidence: number;
  volatility: string;
  trend: string;
};

import { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet } from 'react-native';

export default function HomeScreen() {
  const [stock, setStock] = useState('');
  const [result, setResult] = useState<Prediction | null>(null);

const getPrediction = async () => {
  if (!stock.trim()) {
  alert("Please enter a stock symbol!");
  return;
  }
  console.log("Fetching for:", stock);
  try {
    const response = await fetch(`http://192.168.10.105:8000/predict?stock=${stock}`);
    const data = await response.json();
    console.log("Got prediction:", data);
    setResult(data);
  } catch (error) {
    console.error(' Error fetching prediction:', error);
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
  backgroundColor: '#000', // dark mode base
  },
  title: {
  fontSize: 28,
  fontWeight: 'bold',
  color: '#00ccff',
  marginBottom: 20,
  textAlign: 'center',
  },
  input: { borderColor: '#ccc', borderWidth: 1, padding: 10, marginBottom: 10,color: 'white' },
  result: { marginTop: 20 },

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
  }


});
