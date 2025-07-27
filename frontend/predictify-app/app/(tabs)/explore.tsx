import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity,
  ActivityIndicator, RefreshControl, ScrollView} from 'react-native';

type Stock = {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume?: number;
};

type SectorData = {
  avg_change: number;
  stock_count: number;
  top_stocks: Stock[];
};

export default function ExploreScreen() {
  const [stockData, setStockData] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [currentTab, setCurrentTab] = useState('trending');


  const loadMarketData = async () => {
    try {
      setLoading(true);
      const response = await fetch('https://predictify-zcef.onrender.com/explore-stocks');
      const data = await response.json();

      if (data.error) {
        console.log('API error:', data.error);
        return;
      }
      
      setStockData(data);
    } catch (error) {
      console.log('Network error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadMarketData();
    setRefreshing(false);
  };

  useEffect(() => {
    loadMarketData();
  }, []);

  const tabOptions = [
    { id: 'trending', title: 'Trending', icon: '🔥' },
    { id: 'gainers', title: 'Gainers', icon: '📈' },
    { id: 'losers', title: 'Losers', icon: '📉' },
    { id: 'sectors', title: 'Sectors', icon: '📂' },
    { id: 'popular', title: 'Popular', icon: '⚡' }
  ];

  //formatting each stock - go red and green for %
  const renderStockItem = ({ item }: { item: Stock }) => (
    <TouchableOpacity style={styles.stockCard}>
      <View style={styles.stockMainInfo}>
        <Text style={styles.stockSymbol}>{item.symbol}</Text>
        <Text style={styles.companyName}>{item.name}</Text>
      </View>
      
      <View style={styles.stockPriceInfo}>
        <Text style={styles.stockPrice}>${item.price.toFixed(2)}</Text>
        <Text style={[
          styles.stockChange,
          { color: item.changePercent >= 0 ? '#4CAF50' : '#F44336' }
        ]}>
          {item.changePercent >= 0 ? '+' : ''}{item.changePercent.toFixed(2)}%
        </Text>
      </View>
    </TouchableOpacity>
  );

  //format the sector part - stick w red n green again
  const renderSectorItem = ({ item }: { item: [string, SectorData] }) => {
    const [sectorName, sectorInfo] = item;
    
    return (
      <View style={styles.sectorCard}>
        <View style={styles.sectorHeader}>
          <Text style={styles.sectorTitle}>{sectorName}</Text>
          <View style={styles.sectorPerformance}>
            <Text style={styles.sectorStockCount}>
              {sectorInfo.stock_count} stocks
            </Text>
            <Text style={[
              styles.sectorAvgChange,
              { color: sectorInfo.avg_change >= 0 ? '#4CAF50' : '#F44336' }
            ]}>
              {sectorInfo.avg_change >= 0 ? '+' : ''}{sectorInfo.avg_change.toFixed(1)}%
            </Text>
          </View>
        </View>
        
        <Text style={styles.sectorSubheading}>Top performers:</Text>
        {sectorInfo.top_stocks.slice(0, 3).map((stock, idx) => (
          <View key={stock.symbol} style={styles.sectorStockRow}>
            <Text style={styles.sectorStockSymbol}>{stock.symbol}</Text>
            <Text style={[
              styles.sectorStockPerf,
              { color: stock.changePercent >= 0 ? '#4CAF50' : '#F44336' }
            ]}>
              {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(1)}%
            </Text>
          </View>
        ))}
      </View>
    );
  };

  if (loading) { //same as other loading screens.
    return (
      <View style={styles.loadingScreen}>
        <ActivityIndicator size="large" color="#00ccff" />
        <Text style={styles.loadingMessage}>Loading market data...</Text>
      </View>
    );
  }

  //naviagate to tabs
  const getCurrentTabData = () => {
    if (currentTab === 'sectors') {
      return Object.entries(stockData.sectors || {});
    }
    return stockData[currentTab] || [];
  };

  return (
    <View style={styles.container}>
      <Text style={styles.pageTitle}>Explore Markets</Text>
      
      {/* tab selection */}
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false} 
        style={styles.tabScrollView}
        contentContainerStyle={styles.tabContent}
      >
        {tabOptions.map((tab) => (
          <TouchableOpacity
            key={tab.id}
            style={[
              styles.tabButton,
              currentTab === tab.id && styles.activeTabButton
            ]}
            onPress={() => setCurrentTab(tab.id)}
          >
            <Text style={styles.tabEmoji}>{tab.icon}</Text>
            <Text style={[
              styles.tabLabel,
              currentTab === tab.id && styles.activeTabLabel
            ]}>
              {tab.title}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

    {/* main content list */}
    {currentTab === 'sectors' ? (
      <FlatList
          data={Object.entries(stockData.sectors || {}) as [string, SectorData][]}
          renderItem={renderSectorItem}
          keyExtractor={(item) => item[0]}
          refreshControl={
            <RefreshControl 
              refreshing={refreshing} 
              onRefresh={handleRefresh} 
              tintColor="#00ccff" 
            />
          }
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.listContent}
        />
      ) : (
        <FlatList
          data={stockData[currentTab] as Stock[] || []}
          renderItem={renderStockItem}
          keyExtractor={(item) => item.symbol}
          refreshControl={
            <RefreshControl 
              refreshing={refreshing} 
              onRefresh={handleRefresh} 
              tintColor="#00ccff" 
            />
          }
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.listContent}
        />
      )}
    </View>
  );
} 

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
    paddingTop: 60,
  },
  loadingScreen: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
  },
  loadingMessage: {
    color: '#00ccff',
    marginTop: 15,
    fontSize: 16,
  },
  pageTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#00ccff',
    textAlign: 'center',
    marginBottom: 25,
    paddingHorizontal: 20,
  },
  tabScrollView: {
    marginBottom: 20,
    paddingLeft: 20,
    maxHeight: 60,
  },
  tabContent: {
    paddingRight: 20,
    alignItems: 'center',
  },
  tabButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 8,
    marginRight: 10,
    borderRadius: 18,
    backgroundColor: '#111',
    borderWidth: 1,
    borderColor: '#333',
    minWidth: 80,
  },
  activeTabButton: {
    backgroundColor: '#00ccff',
    borderColor: '#00ccff',
  },
  tabEmoji: {
    fontSize: 16,
    marginRight: 8,
  },
  tabLabel: {
    color: '#ccc',
    fontSize: 14,
    fontWeight: '600',
  },
  activeTabLabel: {
    color: '#000',
  },
  listContent: {
    paddingBottom: 25,
  },
  stockCard: {
    backgroundColor: '#111',
    marginHorizontal: 20,
    marginBottom: 14,
    borderRadius: 12,
    padding: 18,
    borderWidth: 1,
    borderColor: '#333',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  stockMainInfo: {
    flex: 1,
  },
  stockSymbol: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  companyName: {
    fontSize: 14,
    color: '#aaa',
  },
  stockPriceInfo: {
    alignItems: 'flex-end',
  },
  stockPrice: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  stockChange: {
    fontSize: 14,
    fontWeight: '600',
  },
  sectorCard: {
    backgroundColor: '#111',
    marginHorizontal: 20,
    marginBottom: 16,
    borderRadius: 12,
    padding: 18,
    borderWidth: 1,
    borderColor: '#333',
  },
  sectorHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 15,
  },
  sectorTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    flex: 1,
  },
  sectorPerformance: {
    alignItems: 'flex-end',
  },
  sectorStockCount: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  sectorAvgChange: {
    fontSize: 16,
    fontWeight: '600',
  },
  sectorSubheading: {
    fontSize: 14,
    color: '#aaa',
    marginBottom: 10,
  },
  sectorStockRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  sectorStockSymbol: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  sectorStockPerf: {
    fontSize: 14,
    fontWeight: '500',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 50,
  },
  emptyMessage: {
    color: '#666',
    fontSize: 16,
  },
});
