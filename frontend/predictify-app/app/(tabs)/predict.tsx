import { useState } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  Button, 
  StyleSheet, 
  TouchableOpacity, 
  ActivityIndicator, 
  ScrollView,
  Animated, 
  Alert, 
  Dimensions
} from 'react-native';
import Slider from '@react-native-community/Slider';
import { format, addDays } from 'date-fns';

const { width } = Dimensions.get('window');

type Prediction = {
    stock: string;
    predicted_price: number;
    confidence: number;
    volatility: string;
    trend: string;
    sentiment: string;
    timestamp: string;
}

export default function PredictScreen() {
  const [stock, setStock] = useState('');
  const [daysAhead, setDaysAhead] = useState(1);
  const [result, setResult] = useState<Prediction | null>(null);
  const [loading, setLoading] = useState(false);
  const [fadeAnim] = useState(new Animated.Value(0));

  //result animation

  const animateResults = () => {
    fadeAnim.setValue(0);
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 800,
      useNativeDriver: true,
    }).start();
  }


  const getPrediction = async () => {
    if (!stock.trim()) {
      alert("Please enter a stock symbol!");
      return;
    }
    setLoading(true);
    setResult(null); //this one i add for cleating results
    try {
      const response = await fetch(
        `https://predictify-zcef.onrender.com/predict?stock=${stock}&days_ahead=${daysAhead}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      //got to switch this out to ngrok. figure out the debugging. reconsidering the switch as ngrok buggy.
      //any other way to solve the prob where connection has to be same btw laptop and phone?
      //ngrok tunnel breaks aft 2 hrs??
      const data = await response.json();

      //check if render got error, if have manual deploy commit
      if (data.error) {
        Alert.alert("Prediction Error", data.error);
        return;
      }

      //making sure not imcomplete
      if (!data.stock || data.predicted_price === undefined) {
        Alert.alert("Data Error", "Invalid response from prediction service");
        return;
      }

      setResult(data);
      setTimeout(() => animateResults(), 100);

    } catch (error) {
      //when unable to connect to backend, this error takes AGES to show up.
      //gotta look into reducing the timing of error to show up too.
      console.error('Error fetching prediction:', error);
      
      //if else statements for specific errors. handle edge cases.
      if (error instanceof Error) {
        if (error.message.includes('fetch')) {
          Alert.alert("Network error", 
            "Unable to connect to prediction service. Please make sure you are connected to the Internet.");
        } else if (error.message.includes('Server error: 404')) {
          Alert.alert("Service Error", "Prediction service is temporarily unavailable.");
        } else {
          Alert.alert(
            "Prediction Failed",
            "Something went wrong. Please try again."
          );
        }
      } else {
        Alert.alert("Prediction Failed", "Unexpected error. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const confidenceColour = (confidence: number) => {
    if (confidence >= 80) return '#4CAF50'; //green
    if (confidence >= 60) return '#FF9800'; //prange
    return '#F44336' //red
  };

  const confidenceLevel = (confidence: number) => {
    if (confidence >= 80) return 'High';
    if (confidence >= 60) return 'Moderate';
    return 'Low';
  };

  const trendIcon = (trend: string) => {
    return trend === 'Uptrend' ? '📈' : '📉';
  }

  const trendColor = (trend: string) => {
    return trend === 'Uptrend' ? '#4CAF50' : '#F44336';
  }

  const sentimentEmoji = (sentiment: string) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive': return '😊';
      case 'negative': return '😟';
      case 'neutral': return '😐';
      default: return '🤔';
    }
  };

  const volatilityColor = (volatility: string) => {
    switch (volatility?.toLowerCase()) {
      case 'high': return '#F44336';
      case 'moderate': return '#FF9800';
      case 'low': return '#4CAF50';
      default: return '#666';
    }
  };

  const predictedDate = format(addDays(new Date(), daysAhead), 'PPP');

  return (
  <ScrollView contentContainerStyle={styles.container}>
    {/*Header - Replace w predictify logo*/}
    <View style={styles.header}>
      <Text style={styles.title}>🧠 AI Stock Predictor</Text>
      <Text style={styles.subtitle}>Machine learning powered forecasts</Text>
    </View>

    {/*Part to Input*/}
    <View style={styles.inputSection}>
      {/*Stock Input(AAPL)*/}
      <View style={styles.inputGroup}>
        <Text style={styles.label}>Stock Symbol</Text>
        <TextInput
          style={styles.input}
          placeholder="Enter symbol (e.g., AAPL, TSLA)"
          placeholderTextColor="#666"
          value={stock}
          onChangeText={(text) => setStock(text.toUpperCase())}
          autoCapitalize="characters"
          autoCorrect={false}
          maxLength={10}
        />
      </View>

      {/*Days Ahead Slider - Decide 30 or 90*/}
      <View style={styles.inputGroup}>
        <Text style={styles.label}>
          Prediction Timeline: {daysAhead} {daysAhead === 1 ? 'day' : 'days'}
        </Text>
        <View style={styles.sliderContainer}>
          <Slider
            style={styles.slider}
            minimumValue={1}
            maximumValue={90}
            value={daysAhead}
            onValueChange={(value: number) => setDaysAhead(Math.round(value))}
            minimumTrackTintColor="#00ccff"
            maximumTrackTintColor="#333"
            thumbTintColor = "#00ccff"
            step={1}
          />
          <View style={styles.sliderLabels}>
            <Text style={styles.sliderLabel}>1 day</Text>
            <Text style={styles.sliderLabel}>90 days</Text>
          </View>
        </View>
        <Text style={styles.predictionDate}>Target Date: {predictedDate}</Text>
      </View>

      {/*Predict Button*/}
      <TouchableOpacity
        style={[styles.predictButton, loading && styles.buttonDisabled]}
        onPress={getPrediction}
        disabled={loading}
        activeOpacity={0.8}
      >
        {loading ? (
          <View style={styles.loadingButton}>
            <ActivityIndicator size="small" color="#000" />
            <Text style={styles.loadingButtonText}>Analyzing...</Text>
          </View>
        ) : (
          <Text style={styles.buttonText}>⚡ Generate Prediction</Text>
        )}
      </TouchableOpacity>
    </View>

    {/*Loading State*/}
    {loading && (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#00ccff" />
        <Text style={styles.loadingText}>Processing {stock} data...</Text>
        <Text style={styles.loadingSubtext}>This may take a few seconds</Text>
      </View>
    )}

    {/*Results*/}
    {result && !loading && (
      <Animated.View style={[styles.resultsContainer, { opacity: fadeAnim }]}>
        {/*Result Card*/}
        <View style={styles.mainResultCard}>
          <Text style={styles.resultTitle}>
            {result.stock.toUpperCase()} Forecast
          </Text>
          
          <View style={styles.priceContainer}>
            <Text style={styles.priceLabel}>Predicted Price</Text>
            <Text style={styles.predictedPrice}>
              ${result.predicted_price.toFixed(2)}
            </Text>
            <Text style={styles.targetDate}>by {predictedDate}</Text>
          </View>

          {/*Confidence Meter*/}
          <View style={styles.confidenceSection}>
            <View style={styles.confidenceHeader}>
              <Text style={styles.confidenceLabel}>🎯 Prediction Confidence</Text>
              <Text
                style={[
                  styles.confidenceLevel,
                  { color: confidenceColour(result.confidence) }
                ]}
              >
                {confidenceLevel(result.confidence)}
              </Text>
            </View>
            
            <View style={styles.confidenceMeter}>
              <View style={styles.confidenceTrack}>
                <View
                  style={[
                    styles.confidenceFill,
                    {
                      width: `${result.confidence}%`,
                      backgroundColor: confidenceColour(result.confidence)
                    }
                  ]}
                />
              </View>
              <Text style={[
                styles.confidencePercent,
                { color: confidenceColour(result.confidence) }
              ]}>
                {result.confidence}%
              </Text>
            </View>
          </View>
        </View>

        {/*Metrics Grid*/}
        <View style={styles.metricsGrid}>
          <View style={styles.metricCard}>
            <Text style={styles.metricIcon}>{trendIcon(result.trend)}</Text>
            <Text
              style={[
                styles.metricValue,
                { color: trendColor(result.trend) }
              ]}
            >
              {result.trend}
            </Text>
            <Text style={styles.metricLabel}>Market Trend</Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricIcon}>📊</Text>
            <Text
              style={[
                styles.metricValue,
                { color: volatilityColor(result.volatility) }
              ]}
            >
              {result.volatility}
            </Text>
            <Text style={styles.metricLabel}>Volatility</Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricIcon}>
              {sentimentEmoji(result.sentiment)}
            </Text>
            <Text style={styles.metricValue}>
              {result.sentiment}
            </Text>
            <Text style={styles.metricLabel}>Market Sentiment</Text>
          </View>
        </View>

        {/*Model Information*/}
        <View style={styles.modelInfo}>
          <Text style={styles.modelTitle}>📋 Model Details</Text>
          <View style={styles.modelDetails}>
            <Text style={styles.modelText}>
              • Algorithm: Random Forest Regression
            </Text>
            <Text style={styles.modelText}>
              • Data Source: Historical price patterns
            </Text>
            <Text style={styles.modelText}>
              • Analysis Period: {daysAhead <= 3 ? '1 month' : daysAhead <= 10 ? '3 months' : daysAhead <= 30 ? '6 months' : '1 year'}
            </Text>
            <Text style={styles.modelText}>
              • Generated: {new Date(result.timestamp).toLocaleString()}
            </Text>
          </View>
        </View>

        {/*Disclaimer*/}
        <View style={styles.disclaimer}>
          <Text style={styles.disclaimerTitle}>⚠️ Important Notice</Text>
          <Text style={styles.disclaimerText}>
            This prediction is generated using machine learning models based on historical data. 
            Stock markets are inherently unpredictable and past performance does not guarantee 
            future results. This is not financial advice. Always conduct your own research and 
            consider consulting with qualified financial advisors before making investment decisions.
          </Text>
        </View>
      </Animated.View>
    )}
  </ScrollView>
  );
}


const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: '#000',
    padding: 20,
    paddingTop: 60,
  },
  header: {
    alignItems: 'center',
    marginBottom: 30,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#00ccff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
  },
  inputSection: {
    marginBottom: 30,
  },
  inputGroup: {
    marginBottom: 24,
  },
  label: {
    color: '#ccc',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#111',
    borderColor: '#333',
    borderWidth: 1,
    borderRadius: 12,
    padding: 16,
    color: '#fff',
    fontSize: 16,
  },
  sliderContainer: {
    marginTop: 8,
  },
  slider: {
    width: '100%',
    height: 40,
  },
  sliderThumb: {
    backgroundColor: '#00ccff',
    width: 20,
    height: 20,
  },
  sliderLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  sliderLabel: {
    color: '#666',
    fontSize: 12,
  },
  predictionDate: {
    color: '#00ccff',
    fontSize: 14,
    marginTop: 8,
    textAlign: 'center',
  },
  predictButton: {
    backgroundColor: '#00ccff',
    borderRadius: 12,
    padding: 18,
    alignItems: 'center',
  },
  buttonDisabled: {
    backgroundColor: '#333',
  },
  buttonText: {
    color: '#000',
    fontSize: 18,
    fontWeight: 'bold',
  },
  loadingButton: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  loadingButtonText: {
    color: '#000',
    fontSize: 16,
    marginLeft: 8,
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    color: '#00ccff',
    fontSize: 16,
    marginTop: 12,
  },
  loadingSubtext: {
    color: '#666',
    fontSize: 14,
    marginTop: 4,
  },
  resultsContainer: {
    marginTop: 20,
  },
  mainResultCard: {
    backgroundColor: '#111',
    borderRadius: 16,
    padding: 24,
    marginBottom: 20,
  },
  resultTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#00ccff',
    textAlign: 'center',
    marginBottom: 20,
  },
  priceContainer: {
    alignItems: 'center',
    marginBottom: 24,
  },
  priceLabel: {
    color: '#666',
    fontSize: 14,
    marginBottom: 4,
  },
  predictedPrice: {
    color: '#00ccff',
    fontSize: 36,
    fontWeight: 'bold',
  },
  targetDate: {
    color: '#ccc',
    fontSize: 14,
    marginTop: 4,
  },
  confidenceSection: {
    marginBottom: 8,
  },
  confidenceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  confidenceLabel: {
    color: '#ccc',
    fontSize: 16,
  },
  confidenceLevel: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  confidenceMeter: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  confidenceTrack: {
    flex: 1,
    height: 8,
    backgroundColor: '#333',
    borderRadius: 4,
    marginRight: 12,
  },
  confidenceFill: {
    height: '100%',
    borderRadius: 4,
  },
  confidencePercent: {
    fontSize: 16,
    fontWeight: 'bold',
    minWidth: 45,
  },
  metricsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  metricCard: {
    backgroundColor: '#111',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    flex: 1,
    marginHorizontal: 4,
  },
  metricIcon: {
    fontSize: 24,
    marginBottom: 8,
  },
  metricValue: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
    textAlign: 'center',
  },
  metricLabel: {
    color: '#666',
    fontSize: 12,
    textAlign: 'center',
  },
  modelInfo: {
    backgroundColor: '#111',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
  },
  modelTitle: {
    color: '#00ccff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  modelDetails: {
    gap: 6,
  },
  modelText: {
    color: '#ccc',
    fontSize: 14,
  },
  disclaimer: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#ff9800',
  },
  disclaimerTitle: {
    color: '#ff9800',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  disclaimerText: {
    color: '#ccc',
    fontSize: 14,
    lineHeight: 20,
  },
});