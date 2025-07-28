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
import Slider from '@react-native-community/slider';
import { format, addDays } from 'date-fns';
import { LineChart, ProgressChart } from 'react-native-chart-kit'
import { LogBox } from 'react-native';
import { api } from '../../utils/apiClient'

// Suppress known warnings from chart library
LogBox.ignoreLogs([
  '"shadow*" style props are deprecated',
  'VirtualizedLists should never be nested',
]);

const { width } = Dimensions.get('window');
const chartWidth = width - 40;

type Prediction = {
    stock: string;
    predicted_price: number;
    confidence: number;
    volatility: string;
    trend: string;
    sentiment: string;
    timestamp: string;
    current_price: number;
    price_change: number;
    price_change_percent: number;
}

type HistoricalData = {
  date: string;
  price: number;
}

type PredictionTimelinePoint = {
  day: number;
  price: number;
  label: string;
}

type ChartInfo = {
  title: string;
  timeframe_days: number;
  data_period: string;
}

type TradingInfo = {
  trading_days_ahead: number;
  calendar_days_ahead: number;
  target_date: string;
  target_date_formatted: string;
  weekends_skipped: number;
  is_trading_day_today: boolean;
}

type ModelInfo = {
  model_name: string;
  model_code: string;
  algorithm: string;
  description: string;
  timeframe: string;
  approach: string;
  best_for: string;
  confidence_range: string;
  method_used?: string;
  model_params?: string;
}

type BackendResponse = {
  prediction: Prediction;
  historical_data: HistoricalData[];
  prediction_timeline: PredictionTimelinePoint[];
  chart_info: ChartInfo;
  trading_info: TradingInfo;
  model_info: ModelInfo;
}

export default function PredictScreen() {
  const [stock, setStock] = useState('');
  const [daysAhead, setDaysAhead] = useState(1);
  const [result, setResult] = useState<BackendResponse | null>(null);
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
      const data = await api.getPrediction(stock, daysAhead);

      //got to switch this out to ngrok. figure out the debugging. reconsidering the switch as ngrok buggy.
      //any other way to solve the prob where connection has to be same btw laptop and phone?
      //ngrok tunnel breaks aft 2 hrs??

      //check if render got error, if have manual deploy commit
      if (data.error) {
        Alert.alert("Prediction Error", data.error);
        return;
      }

      //making sure not imcomplete
      if (!data.prediction || !data.prediction.stock || data.prediction.predicted_price === undefined) {
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

  const getApproximateTargetDate = (daysAhead: number) => {
    const weekends = Math.floor(daysAhead / 5) * 2;
    const approximateDays = daysAhead + weekends;
    return format(addDays(new Date(), approximateDays), 'PPP');
  };

  const predictedDate = result?.trading_info?.target_date_formatted || getApproximateTargetDate(daysAhead);

  const connectedTimelineData = () => {
    if (!result || !result?.historical_data || !result?.prediction_timeline) return null;

    const recentHistoryCount = Math.min(40, result.historical_data.length);
    const recentHistory = result.historical_data.slice(-recentHistoryCount);
    
    // Prediction data
    const futurePoints = result.prediction_timeline.slice(1);
    
    const historicalPrices = recentHistory.map((item: HistoricalData) => item.price);
    const futurePrices = futurePoints.map((item: PredictionTimelinePoint) => item.price);
    //const allPrices = [...historicalPrices, ...futurePrices];

    const currentPrice = result.prediction.current_price;
    
    //labels
    const totalPoints = historicalPrices.length + futurePrices.length;
    const labelInterval = Math.max(1, Math.floor(totalPoints / 6)); //cap it at 6
    const historicalLabels = recentHistory.map((item: HistoricalData, index: number) => {
    if (index % labelInterval === 0 || index === recentHistory.length - 1) {
      return format(new Date(item.date), 'MM/dd');
    }
    return '';
  });
    
    const futureLabels = futurePoints.map((item: PredictionTimelinePoint, index: number) => {
      if (index % Math.max(1, Math.floor(futurePoints.length / 3)) === 0 || index === futurePoints.length - 1) {
      return item.label || `+${item.day}d`;
      }
      return '';
    });
    
    //combine everyt
    const allPrices = [...historicalPrices, currentPrice, ...futurePrices];
    const allLabels = [...historicalLabels, 'Now', ...futureLabels];
    
    //different styling for historical vs prediction
     const datasets = [
      {
        data: allPrices,
        color: (opacity = 1) => `rgba(0, 204, 255, ${opacity})`,
        strokeWidth: 3
      },

    {
        
      data: [
        ...Array(historicalPrices.length - 1).fill(NaN), 
        currentPrice,
        ...Array(futurePrices.length).fill(NaN)
      ],
      color: (opacity = 1) => `rgba(255, 215, 0, ${opacity})`, // Gold color
      strokeWidth: 0, //dot
      withDots: true,
    },
    // prediction points green
    {
      data: [
        ...Array(historicalPrices.length).fill(NaN), // Fill with NaN to start from current price
        currentPrice, // Start prediction from current price
        ...futurePrices
      ],
      color: (opacity = 1) => `rgba(76, 175, 80, ${opacity})`, // Green
      strokeWidth: 3,
      strokeDashArray: [5, 5], // dashed line for predictions
    }
  ];

  return { 
    labels: allLabels, 
    datasets,
    transitionIndex: historicalPrices.length // hist endpoint
  };
};
      


  // Chart configuration
  const improved_chartConfig = {
    backgroundColor: '#111',
    backgroundGradientFrom: '#111',
    backgroundGradientTo: '#222',
    decimalPlaces: 2,
    color: (opacity = 1) => `rgba(0, 204, 255, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
    style: {
      borderRadius: 16
    },
    propsForDots: {
      r: "4",
      strokeWidth: "2",
      stroke: "#00ccff"
    },
    propsForBackgroundLines: {
      strokeDasharray: "",
      stroke: "#333",
      strokeWidth: 1
    },
    propsForLabels: {
      fontSize: 10, //smaller font
    },
    formatXLabel: (value: string) => {
    // Only show non-empty labels and truncate if needed
      return value.length > 5 ? value.substring(0, 5) : value;
    },
  segments: 4,
  };

  const predictionChartConfig = {
    backgroundColor: '#111',
    backgroundGradientFrom: '#001a2e',
    backgroundGradientTo: '#111',
    decimalPlaces: 2,
    color: (opacity = 1) => `rgba(76, 175, 80, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
    style: {
      borderRadius: 16
    },
    propsForDots: {
      r: "4",
      strokeWidth: "2",
      stroke: "#4CAF50"
    }
  };

  const getModelDisplayInfo = (daysAhead: number, modelInfo?: ModelInfo) => {
  if (daysAhead <= 7) {
    return {
      icon: '📈',
      category: 'Short-term Analysis',
      timeDescription: `${daysAhead} day${daysAhead > 1 ? 's' : ''} ahead`,
      approach: 'Recent pattern analysis',
      color: '#00ccff'
    };
  } else {
    return {
      icon: '🤖',
      category: 'Long-term Forecasting', 
      timeDescription: `${daysAhead} days ahead`,
      approach: 'Historical pattern recognition',
      color: '#4CAF50'
    };
  }
};


  return (
  <ScrollView contentContainerStyle={styles.container}>
    {/*Header - Replace w predictify logo*/}
    <View style={styles.header}>
      <Text style={styles.title}>🧠 Stock Predictor</Text>
      <Text style={styles.subtitle}>Machine learning powered forecasts</Text>
    </View>

    {/*Part to Input*/}
    <View style={styles.inputSection}>
      {/*Stock Input(AAPL)*/}
      <View style={styles.inputGroup}>
        <Text style={styles.label}>Stock Symbol</Text>
        <TextInput
          style={styles.input}
          placeholder="Enter symbol (e.g., AAPL)"
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
          Prediction Timeline: {daysAhead} {daysAhead === 1 ? 'trading day' : 'trading days'}
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
            <Text style={styles.sliderLabel}>1 trading day</Text>
            <Text style={styles.sliderLabel}>90 trading days</Text>
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

    {/*Results - charts added*/}
    {result && !loading && (
      <Animated.View style={[styles.resultsContainer, { opacity: fadeAnim }]}>

        {/*Current vs Predicted*/}
        <View style={styles.priceComparisonCard}>
            <Text style={styles.cardTitle}>Price Comparison</Text>
            
            <View style={styles.priceRow}>
              <View style={styles.priceColumn}>
                <Text style={styles.priceLabel}>Current Price</Text>
                <Text style={styles.currentPrice}>
                  ${result.prediction.current_price.toFixed(2)}
                </Text>
                <Text style={[
                  styles.priceChange,
                  { color: result.prediction.price_change >= 0 ? '#4CAF50' : '#F44336' }
                ]}>
                  {result.prediction.price_change >= 0 ? '+' : ''}${result.prediction.price_change.toFixed(2)} 
                  ({result.prediction.price_change_percent >= 0 ? '+' : ''}
                  {result.prediction.price_change_percent.toFixed(1)}%)
                </Text>
              </View>

              <View style={styles.priceColumn}>
                <Text style={styles.priceLabel}>Predicted Price</Text>
                <Text style={styles.predictedPrice}>
                  ${result.prediction.predicted_price.toFixed(2)}
                </Text>
                <Text style={styles.targetDate}>by {predictedDate}</Text>
              </View>
            </View>

            {/*Change Indicator*/}
            <View style={styles.changeIndicator}>
              <Text style={[
                styles.changeText,
                { color: result.prediction.predicted_price > result.prediction.current_price ? '#4CAF50' : '#F44336' }
              ]}>
                {result.prediction.predicted_price > result.prediction.current_price ? '📈' : '📉'} 
                {result.prediction.predicted_price > result.prediction.current_price ? '+' : ''}
                ${(result.prediction.predicted_price - result.prediction.current_price).toFixed(2)} 
                ({((result.prediction.predicted_price - result.prediction.current_price) / 
                result.prediction.current_price * 100).toFixed(1)}%)
              </Text>
            </View>
          </View>

          {/*Connected Timeline Chart - Historical + Prediction*/}
          {connectedTimelineData() && (
            <View style={styles.chartCard}>
              <Text style={styles.chartTitle}>
                {getModelDisplayInfo(daysAhead).icon} {result.chart_info.title} → {result.model_info?.model_name || 'AI Prediction'}
              </Text>
              <View style={styles.chartContainer}>
                <LineChart
                  data={connectedTimelineData()!}
                  width={chartWidth}
                  height={220}
                  chartConfig={improved_chartConfig}
                  bezier={false}
                  style={styles.chart}
                  withHorizontalLabels={true}
                  withVerticalLabels={true}
                  withDots={true}
                  withShadow={false}
                  withInnerLines={true}
                  withOuterLines={true}
                  yLabelsOffset={10}
                  xLabelsOffset={-5}
                  fromZero={false}
/>
              </View>
              <View style={styles.chartLegend}>
                <View style={styles.legendItem}>
                  <View style={[styles.legendDot, { backgroundColor: '#00ccff' }]} />
                  <Text style={styles.legendText}>Historical ({result.chart_info.timeframe_days} days)</Text>
                </View>
                <View style={styles.legendItem}>
                  <View style={[styles.legendDot, { backgroundColor: '#FFD700' }]} />
                  <Text style={styles.legendText}>Current Price</Text>
                </View>
                <View style={styles.legendItem}>
                  <View style={[styles.legendDot, { backgroundColor: '#4CAF50' }]} />
                  <Text style={styles.legendText}>AI Prediction ({daysAhead} days)</Text>
                </View>
              </View>
              <Text style={styles.chartSubtitle}>
                Seamless timeline from real historical data to AI prediction
              </Text>
            </View>
          )}

          {/*Confidence Meter*/}
          <View style={styles.confidenceSection}>
            <View style={styles.confidenceHeader}>
              <Text style={styles.confidenceLabel}>🎯 Prediction Confidence</Text>
              <Text
                style={[
                  styles.confidenceLevel,
                  { color: confidenceColour(result.prediction.confidence) }
                ]}
              >
                {confidenceLevel(result.prediction.confidence)}
              </Text>
            </View>
            
            <View style={styles.confidenceMeter}>
              <View style={styles.confidenceTrack}>
                <View style={[
                  styles.confidenceFill,
                  {
                    width: `${result.prediction.confidence}%`,
                    backgroundColor: confidenceColour(result.prediction.confidence)
                  }
                ]}
                />
              </View>
              <Text style={[
                styles.confidencePercent,
                { color: confidenceColour(result.prediction.confidence) }
              ]}>
                {result.prediction.confidence}%
              </Text>
            </View>
          </View>

        {/*Metrics Grid*/}
        <View style={styles.metricsGrid}>
          <View style={styles.metricCard}>
            <Text style={styles.metricIcon}>{trendIcon(result.prediction.trend)}</Text>
            <Text
              style={[
                styles.metricValue,
                { color: trendColor(result.prediction.trend) }
              ]}
            >
              {result.prediction.trend}
            </Text>
            <Text style={styles.metricLabel}>Market Trend</Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricIcon}>📊</Text>
            <Text
              style={[
                styles.metricValue,
                { color: volatilityColor(result.prediction.volatility) }
              ]}
            >
              {result.prediction.volatility}
            </Text>
            <Text style={styles.metricLabel}>Volatility</Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricIcon}>
              {sentimentEmoji(result.prediction.sentiment)}
            </Text>
            <Text style={styles.metricValue}>
              {result.prediction.sentiment}
            </Text>
            <Text style={styles.metricLabel}>Market Sentiment</Text>
          </View>
        </View>

         {/*Confidence Chart*/}
          <View style={styles.chartCard}>
            <Text style={styles.chartTitle}>🎯 Model Confidence Analysis</Text>
            <View style={styles.chartContainer}>
              <ProgressChart
                data={{
                  labels: ["Confidence", "Accuracy", "Reliability"],
                  data: [
                    result.prediction.confidence / 100,
                    Math.min(result.prediction.confidence / 100 + 0.1, 1),
                    result.prediction.confidence > 
                    80 ? 0.9 : result.prediction.confidence > 60 ? 0.7 : 0.5
                  ]
                }}
                width={chartWidth}
                height={200}
                strokeWidth={16}
                radius={32}
                chartConfig={{
                  backgroundColor: '#111',
                  backgroundGradientFrom: '#111',
                  backgroundGradientTo: '#222',
                  color: (opacity = 1, index = 0) => {
                    const colors = ['#00ccff', '#4CAF50', '#FF9800'];
                    return colors[index] || `rgba(255, 255, 255, ${opacity})`;
                  },
                  labelColor: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
                }}
                hideLegend={false}
                style={styles.chart}
              />
            </View>
          </View>

        {/*Model Information*/}
        <View style={styles.modelInfo}>
          <Text style={styles.modelTitle}>📋 Model Details</Text>
          {result.model_info && (
    <View style={styles.modelDetails}>
      <View style={styles.modelHeader}>
        <Text style={[styles.modelBadge, { backgroundColor: getModelDisplayInfo(daysAhead).color }]}>
          {getModelDisplayInfo(daysAhead).icon} {getModelDisplayInfo(daysAhead).category}
        </Text>
      </View>
      
      <Text style={styles.modelText}>
        • Algorithm: {result.model_info.algorithm}
      </Text>
      <Text style={styles.modelText}>
        • Approach: {result.model_info.approach}
      </Text>
      <Text style={styles.modelText}>
        • Timeframe: {result.model_info.timeframe}
      </Text>
      <Text style={styles.modelText}>
        • Best for: {result.model_info.best_for}
      </Text>
      <Text style={styles.modelText}>
        • Expected confidence: {result.model_info.confidence_range}
      </Text>
      {result.model_info.method_used && (
        <Text style={styles.modelText}>
          • Method used: {result.model_info.method_used}
        </Text>
      )}
    </View>
  )}
  
  <View style={styles.modelExplanation}>
    <Text style={styles.explanationTitle}>Why this model?</Text>
    <Text style={styles.explanationText}>
      {daysAhead <= 7 
        ? "For short-term predictions, we analyze recent price movements and patterns using time series analysis. This captures momentum and mean reversion effects that are most relevant for the next few days."
        : "For longer-term predictions, we use machine learning to analyze months of historical data, identifying complex patterns and relationships that emerge over weeks and months."
      }
    </Text>
  </View>
</View>

        {/*Disclaimer*/}
        <View style={styles.disclaimer}>
          <Text style={styles.disclaimerTitle}>⚠️ Important Notice</Text>
          <Text style={styles.disclaimerText}>
            This prediction is generated using machine learning models based on historical data from yfinance. 
            Charts show actual price movements and AI-generated forecasts. Stock markets are inherently 
            unpredictable and past performance does not guarantee future results. This is not financial advice. 
            Always conduct your own research and consider consulting with qualified financial advisors before making 
            investment decisions.
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
  priceComparisonCard: {
    backgroundColor: '#111',
    borderRadius: 16,
    padding: 24,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#333',
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#00ccff',
    textAlign: 'center',
    marginBottom: 20,
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  priceColumn: {
    alignItems: 'center',
    flex: 1,
  },
  priceLabel: {
    color: '#666',
    fontSize: 14,
    marginBottom: 8,
  },
  currentPrice: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  predictedPrice: {
    color: '#00ccff',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  priceChange: {
    fontSize: 14,
    fontWeight: '600',
  },
  targetDate: {
    color: '#ccc',
    fontSize: 14,
  },
  changeIndicator: {
    alignItems: 'center',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#333',
  },
  changeText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  chartCard: {
    backgroundColor: '#111',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#333',
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#00ccff',
    marginBottom: 16,
    textAlign: 'center',
  },
  chartContainer: {
    alignItems: 'center',
    marginVertical: 10,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  chartSubtitle: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    marginTop: 8,
    fontStyle: 'italic',
  },

  chartLegend: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 12,
    paddingHorizontal: 10,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 4,
  },
  legendText: {
    fontSize: 10,
    color: '#999',
  },
  confidenceSection: {
    backgroundColor: '#111',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#333',
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
    borderWidth: 1,
    borderColor: '#333',
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
    borderWidth: 1,
    borderColor: '#333',
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

  modelHeader: {
    marginBottom: 12,
    alignItems: 'center',
  },

  modelBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    color: '#000',
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
  },

  modelExplanation: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#1a1a1a',
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#00ccff',
  },

  explanationTitle: {
    color: '#00ccff',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 6,
  },

  explanationText: {
    color: '#ccc',
    fontSize: 13,
    lineHeight: 18,
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