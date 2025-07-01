import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Button } from 'react-native';

type Prediction = {
    stock: string;
    predicted_price: number;
    confidence: number;
    volatility: string;
    trend: string;
    timestamp: string;
};

export default function HistoryScreen() {
    const [history, setHistory] = useState<Prediction[]>([]);

    const fetchHistory = () => {
        fetch('http://192.168.88.7:8000/history')
        .then((res) => res.json())
        .then(setHistory)
        .catch((err) => console.error('History fetch error:', err));
    };
    //there seems to be a bit of delay from when i get prediction to it actually showing up on logs
    //add refresh button if possible

    useEffect(() => {
        fetchHistory();
    }, []);

    return (
        <ScrollView style={styles.container}>
            <Text style={styles.title}>Prediction History</Text>

        <View style={styles.refreshButton}>
            <Button title="Refresh" onPress={fetchHistory} />
        </View>

        {history.length === 0 ? (
            <Text style={styles.subtitle}>No predictions yet.</Text>
        ) : (
            history.slice()
            .reverse()
            .map((item, index) => (
            <View key={index} style={styles.card}>
                <Text style={styles.header}>
                    {item.stock} — {new Date(item.timestamp).toLocaleString()}
                </Text>
                <Text style={styles.text}>💵 ${item.predicted_price}</Text>
                <Text style={styles.text}>📊 {item.confidence}%</Text>
                <Text style={styles.text}>⚠️ {item.volatility}</Text> 
                <Text style={styles.text}>📈 {item.trend}</Text>
            </View>
            ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
    container: {
        padding: 16,
        paddingTop: 60,
        backgroundColor: '#000',
        flex: 1,
    },
    title: {
        fontSize: 24,
        color: '#00ccff',
        fontWeight: 'bold',
        marginBottom: 12,
        textAlign: 'center',
    },
    refreshButton: {
        marginBottom: 20,
        alignItems: 'center',
    },
    subtitle: {
        color: '#ccc',
        textAlign: 'center',
        marginTop: 20,
    },
    card: {
        backgroundColor: '#1a1a1a',
        padding: 16,
        borderRadius: 10,
        marginBottom: 10,
    },
    header: {
        fontSize: 16,
        color: '#00ccff',
        fontWeight: 'bold',
        marginBottom: 6,
    },
    text: {
        fontSize: 15,
        color: 'white',
        marginBottom: 4,
    },
});


