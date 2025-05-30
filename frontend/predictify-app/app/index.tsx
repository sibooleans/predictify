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
    try {
      const response = await fetch(`http://192.168.10.105:8000/predict?stock=${stock}`);
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error fetching prediction:', error);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Predictify</Text>
      <TextInput
        style={styles.input}
        placeholder="Enter stock symbol (e.g. AAPL)"
        value={stock}
        onChangeText={setStock}
      />
      <Button title="Predict" onPress={getPrediction} />
      {result && (
        <View style={styles.result}>
          <Text>Predicted Price: ${result.predicted_price}</Text>
          <Text>Confidence: {result.confidence}%</Text>
          <Text>Volatility: {result.volatility}</Text>
          <Text>Trend: {result.trend}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, marginTop: 60 },
  title: { fontSize: 24, marginBottom: 20, fontWeight: 'bold' },
  input: { borderColor: '#ccc', borderWidth: 1, padding: 10, marginBottom: 10 },
  result: { marginTop: 20 }
});
