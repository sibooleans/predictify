import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Button, ScrollView,
  TouchableOpacity, Dimensions, Animated } from 'react-native';
import { Link } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

const { width } = Dimensions.get('window');
//typescript declarations for action button fn
interface ActionButtonProps {
  icon: any;
  title: string;
  subtitle: string;
  route: any;
  gradient?: boolean;
}

//implement 3 action buttons, 1 to each feature.
const ActionButton = ({ icon, title, subtitle, route, gradient = false }: ActionButtonProps) => (
  <Link href={route} asChild>
    <TouchableOpacity 
      style={[
        styles.actionButton, 
        gradient && styles.primaryActionButton
      ]}
      activeOpacity={0.8}
    >
      <View style={styles.actionContent}>
        <Ionicons 
          name={icon} 
          size={24} 
          color={gradient ? '#000' : '#00ccff'} 
        />
        <View style={styles.actionText}>
          <Text style={[
            styles.actionTitle,
            gradient && styles.primaryActionTitle
          ]}>
            {title}
          </Text>
          <Text style={[
            styles.actionSubtitle,
            gradient && styles.primaryActionSubtitle
          ]}>
            {subtitle}
          </Text>
        </View>
      </View>
      <Ionicons 
        name="arrow-forward" 
        size={20} 
        color={gradient ? '#000' : '#666'} 
      />
    </TouchableOpacity>
  </Link>
);

export default function HomeScreen() {
  //remember to replace the placeholder emoji with our actual logo
  const [fadeAnim] = useState(new Animated.Value(0));
  const [scaleAnim] = useState(new Animated.Value(0.9));

  //tried a pop in effect.
  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 900,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      })
    ]).start();
  }, []);
  

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <Animated.View 
        style={[
          styles.content,
          {
            opacity: fadeAnim,
            transform: [{ scale: scaleAnim }]
          }
        ]}
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.logoArea}>
            <View style={styles.logo}>
              <Text style={styles.logoText}>📈</Text>
            </View>
            <Text style={styles.appName}>Predictify</Text>
            <Text style={styles.tagline}>Stock Predictions</Text>
          </View>
        </View>

        {/* Three Buttons */} 
        <View style={styles.buttons}>
          <ActionButton
            icon="analytics"
            title="Start Predicting"
            subtitle="Forecasts for any stock"
            route="/(tabs)/predict"
            gradient={false}
          />
          
          <ActionButton
            icon="compass"
            title="Explore Markets"
            subtitle="Trending stocks & market insights"
            route="/(tabs)/explore"
          />
          
          <ActionButton
            icon="time"
            title="My Predictions"
            subtitle="View your prediction history"
            route="/(tabs)/history"
          />
        </View>

        {/* Stock coverage info */}
        <View style={styles.coverageCard}>
          <View style={styles.coverageHeader}>
            <View style={styles.yahooLogo}>
              <Text style={styles.yahooText}>Y!</Text>
            </View>
            <View style={styles.coverageInfo}>
              <Text style={styles.coverageTitle}>Powered by Yahoo Finance</Text>
              <Text style={styles.coverageSubtitle}>
                Predict any stock from major exchanges
              </Text>
            </View>
          </View>
          
          <View style={styles.exchangeList}>
            <View style={styles.exchangeItem}>
              <Text style={styles.exchangeCode}>NYSE</Text>
              <Text style={styles.exchangeName}>New York Stock Exchange</Text>
            </View>
            <View style={styles.exchangeItem}>
              <Text style={styles.exchangeCode}>NASDAQ</Text>
              <Text style={styles.exchangeName}>NASDAQ Global Market</Text>
            </View>
            <View style={styles.exchangeItem}>
              <Text style={styles.exchangeCode}>LSE</Text>
              <Text style={styles.exchangeName}>London Stock Exchange</Text>
            </View>
          </View>
          
          <Text style={styles.footnote}>
            Search by symbol (AAPL, TSLA, GOOGL...) or explore trending stocks
          </Text>
        </View>

        {/* Models Preview */}
        <View style={styles.modelsCard}>
          <Text style={styles.modelsTitle}>🧠 Multi Model Strategy</Text>
          <View style={styles.modelsList}>
            <View style={styles.modelItem}>
              <View style={styles.modelIcon}>
                <Text style={styles.modelEmoji}>⚡</Text>
              </View>
              <View style={styles.modelDetails}>
                <Text style={styles.modelName}>ARIMA</Text>
                <Text style={styles.modelDesc}>Short-term patterns (1-7 days)</Text>
              </View>
            </View>
            
            <View style={styles.modelItem}>
              <View style={styles.modelIcon}>
                <Text style={styles.modelEmoji}>🎯</Text>
              </View>
              <View style={styles.modelDetails}>
                <Text style={styles.modelName}>Random Forest Regression</Text>
                <Text style={styles.modelDesc}>Long-term forecasts (8-90 days)</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            💡 Tip: Start with popular stocks like AAPL or TSLA to get real-time forecasts!
          </Text>
        </View>
      </Animated.View>
    </ScrollView>
  );
}



//shud add more shortcuts to impt features. currently thinking mayb explore feature deserves one roo.

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  content: {
    paddingTop: 70,
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logoArea: {
    alignItems: 'center',
  },
  logo: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#111',
    borderWidth: 2,
    borderColor: '#00ccff',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  logoText: {
    fontSize: 32,
  },
  appName: {
    fontSize: 30,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 6,
  },
  tagline: {
    fontSize: 16,
    color: '#aaa',
    textAlign: 'center',
  },
  buttons: {
    marginBottom: 32,
  },
  // Base button style - MUST come before primaryActionButton
  actionButton: {
    backgroundColor: '#111',
    borderRadius: 16,
    padding: 20,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#333',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  // Primary button override - MUST come after actionButton
  primaryActionButton: {
    backgroundColor: '#00ccff', // This will override the #111 background
    borderColor: '#00ccff',
    shadowColor: '#00ccff',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  actionContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  actionText: {
    marginLeft: 16,
    flex: 1,
  },
  actionTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4,
  },
  primaryActionTitle: {
    color: '#000',
  },
  actionSubtitle: {
    fontSize: 14,
    color: '#aaa',
  },
  primaryActionSubtitle: {
    color: '#333',
  },
  coverageCard: {
    backgroundColor: '#111',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#333',
  },
  coverageHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  yahooLogo: {
    width: 40,
    height: 40,
    borderRadius: 8,
    backgroundColor: '#7B68EE',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  yahooText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  coverageInfo: {
    flex: 1,
  },
  coverageTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 2,
  },
  coverageSubtitle: {
    fontSize: 14,
    color: '#aaa',
  },
  exchangeList: {
    marginBottom: 16,
  },
  exchangeItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
  },
  exchangeCode: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#00ccff',
    minWidth: 70,
  },
  exchangeName: {
    fontSize: 14,
    color: '#ccc',
    flex: 1,
  },
  footnote: {
    fontSize: 13,
    color: '#666',
    fontStyle: 'italic',
    textAlign: 'center',
  },
  modelsCard: {
    backgroundColor: '#111',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#333',
  },
  modelsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 16,
    textAlign: 'center',
  },
  modelsList: {
    gap: 16,
  },
  modelItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  modelIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: '#1a1a1a',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  modelEmoji: {
    fontSize: 20,
  },
  modelDetails: {
    flex: 1,
  },
  modelName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4,
  },
  modelDesc: {
    fontSize: 14,
    color: '#aaa',
  },
  footer: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 3,
    borderLeftColor: '#00ccff',
  },
  footerText: {
    fontSize: 14,
    color: '#ccc',
    textAlign: 'center',
    lineHeight: 20,
  },
});