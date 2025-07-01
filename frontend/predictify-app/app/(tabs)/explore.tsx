import React, { useState } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, Image } from 'react-native';

type Stock = {
  symbol: string;
  name: string;
  price: number;
  change: number;
};

const mockStocks: Stock[] = [
  { symbol: 'AAPL', name: 'Apple Inc.', price: 195.32, change: +1.23 },
  { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 178.27, change: -3.84 },
  { symbol: 'TSLA', name: 'Tesla Inc.', price: 323.79, change: +4.10 },
  { symbol: 'AMZN', name: 'Amazon.com Inc.', price: 223.30, change: -6.18 },
];
//gotta replace this mockstocks with actual data. link to yahoo finance api

export default function ExploreScreen() {
  const [stocks, setStocks] = useState<Stock[]>(mockStocks);

  const renderItem = ({ item }: { item: Stock }) => (
    <TouchableOpacity style={styles.card}>
      <View style={styles.stockHeader}>
        <Text style={styles.symbol}>{item.symbol}</Text>
        <Text style={[styles.priceChange, { color: item.change >= 0 ? '#4caf50' : '#f44336' }]}>
          {item.change >= 0 ? '+' : ''}
          {item.change.toFixed(2)}
        </Text>
      </View>
      <Text style={styles.name}>{item.name}</Text>
      <Text style={styles.price}>${item.price.toFixed(2)}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Explore Popular Stocks</Text>
      <FlatList
        data={stocks}
        renderItem={renderItem}
        keyExtractor={(item) => item.symbol}
        contentContainerStyle={{ paddingBottom: 20 }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#000',
    flex: 1,
    paddingTop: 60,
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#00ccff',
    marginBottom: 20,
    textAlign: 'center',
  },
  card: {
    backgroundColor: '#1e1e1e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  stockHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  symbol: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  name: {
    fontSize: 14,
    color: '#aaa',
    marginTop: 4,
  },
  price: {
    fontSize: 20,
    fontWeight: '600',
    color: '#fff',
    marginTop: 8,
  },
  priceChange: {
    fontSize: 16,
    fontWeight: '500',
  },
});
