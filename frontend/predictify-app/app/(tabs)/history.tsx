import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity,
    ActivityIndicator, TextInput, RefreshControl, Alert} from 'react-native';
import { format, parseISO, differenceInDays } from 'date-fns';
import { api } from '../../utils/apiClient';

type Prediction = {
    id?: number;
    stock: string;
    predicted_price: number;
    current_price: number;
    confidence: number;
    volatility: string;
    trend: string;
    sentiment: string;
    timestamp: string;
    days_ahead: number;
    target_date?: string;
    model_used?: string;
    price_change?: number;
    price_change_percent?: number;
};

export default function HistoryScreen() {
    const [history, setHistory] = useState<Prediction[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [filter, setFilter] = useState<'all' | 'accurate' | 'recent'>('all');

    const fetchHistory = async () => {
        try {
            setLoading(true);
            const data = await api.getHistory();
            setHistory(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('History fetch error:', error);
            Alert.alert('Error', 'Failed to load prediction history');
        } finally {
            setLoading(false);
        }
    };

    const onRefresh = async () => {
        setRefreshing(true);
        await fetchHistory();
        setRefreshing(false);
    };

    useEffect(() => {
        fetchHistory();
    }, []);

    //filter n search
    const filteredHistory = history
        .filter(item => {
            const matchSearch = item
            .stock
            .toLowerCase()
            .includes(searchTerm.toLowerCase());
            
            switch (filter) {
                case 'accurate':
                    return matchSearch && item.confidence >= 70;
                case 'recent':
                    const daysSince = differenceInDays(new Date(), parseISO(item.timestamp));
                    return matchSearch && daysSince <= 7;
                default:
                    return matchSearch;
            }
        })
        .sort((a, b) => new Date(b.timestamp).getTime() - 
        new Date(a.timestamp).getTime());

        

        const confidenceColor = (confidence: number) => {
        if (confidence >= 80) return '#4CAF50';
        if (confidence >= 60) return '#FF9800';
        return '#F44336';
        };

        const trendIcon = (trend: string) => trend === 'Uptrend' ? '📈' : '📉';
        const trendColor = (trend: string) => trend === 'Uptrend' ? '#4CAF50' : '#F44336';

        const getSentimentEmoji = (sentiment: string) => {
            switch (sentiment?.toLowerCase()) {
                case 'positive': return '😊';
                case 'negative': return '😟';
                case 'neutral': return '😐';
                default: return '🤔';
            }
        };

        const getVolatilityColor = (volatility: string) => {
            switch (volatility?.toLowerCase()) {
                case 'high': return '#F44336';
                case 'moderate': return '#FF9800';
                case 'low': return '#4CAF50';
                default: return '#666';
            }
        };

        //same helper functions as predict.tsx, just copy over

        const formatTimestamp = (timestamp: string) => {
            try {
                return format(parseISO(timestamp), 'MMM dd, yyyy • h:mm a');
            } catch {
                return 'Invalid date';
            }
        };

        if (loading) {
            return (
                <View style={styles.loadingContainer}>
                    <ActivityIndicator size="large" color="#00ccff" />
                    <Text style={styles.loadingText}>Loading prediction history...</Text>
                </View>
            );
        }

        return (
            <View style={styles.container}>
                {/* Header */}
                <View style={styles.header}>
                    <Text style={styles.title}>📊 Prediction History</Text>
                    <Text style={styles.subtitle}>
                        {history.length} prediction{history.length !== 1 ? 's' : ''} made
                </Text>
            </View>

            {/* Search n filter logic */}
            <View style={styles.controlsSection}>
                <TextInput
                    style={styles.searchInput}
                    placeholder="Search by stock symbol..."
                    placeholderTextColor="#666"
                    value={searchTerm}
                    onChangeText={setSearchTerm}
                />
                
                <View style={styles.filterButtons}>
                    {['all', 'accurate', 'recent'].map((filterType) => (
                        <TouchableOpacity
                            key={filterType}
                            style={[
                                styles.filterButton,
                                filter === filterType && styles.filterButtonActive
                            ]}
                            onPress={() => setFilter(filterType as any)}
                        >
                            <Text style={[
                                styles.filterButtonText,
                                filter === filterType && styles.filterButtonTextActive
                            ]}>
                                {filterType === 'all' ? 'All' : 
                                 filterType === 'accurate' ? 'High Confidence' : 'Recent'}
                            </Text>
                        </TouchableOpacity>
                    ))}
                </View>
            </View>

            {/* Stats Summary */}
            {history.length > 0 && (
                <View style={styles.statsContainer}>
                    <View style={styles.statCard}>
                        <Text style={styles.statNumber}>
                            {Math.round(history.reduce((sum, p) => sum + p.confidence, 0) / history.length)}%
                        </Text>
                        <Text style={styles.statLabel}>Avg Confidence</Text>
                    </View>
                    <View style={styles.statCard}>
                        <Text style={styles.statNumber}>
                            {history.filter(p => p.trend === 'Uptrend').length}
                        </Text>
                        <Text style={styles.statLabel}>Bullish Calls</Text>
                    </View>
                    <View style={styles.statCard}>
                        <Text style={styles.statNumber}>
                            {new Set(history.map(p => p.stock)).size}
                        </Text>
                        <Text style={styles.statLabel}>Stocks Analyzed</Text>
                    </View>
                </View>
            )}

            {/* History List */}
            <ScrollView 
                style={styles.historyList}
                refreshControl={
                    <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#00ccff" />
                }
                showsVerticalScrollIndicator={false}
            >
                {filteredHistory.length === 0 ? (
                    <View style={styles.emptyContainer}>
                        <Text style={styles.emptyIcon}>📈</Text>
                        <Text style={styles.emptyTitle}>
                            {searchTerm ? 'No matching predictions' : 'No predictions yet'}
                        </Text>
                        <Text style={styles.emptySubtitle}>
                            {searchTerm 
                                ? `Try searching for a different stock symbol`
                                : 'Start making predictions to see your history here'
                            }
                        </Text>
                    </View>
                ) : (
                    filteredHistory.map((item, index) => (
                        <TouchableOpacity key={index} style={styles.predictionCard}>
                            {/* Card Header */}
                            <View style={styles.cardHeader}>
                                <View style={styles.stockInfo}>
                                    <Text style={styles.stockSymbol}>{item.stock}</Text>
                                    <Text style={styles.timestamp}>
                                        {formatTimestamp(item.timestamp)}
                                    </Text>
                                </View>
                                <View style={styles.confidenceBadge}>
                                    <Text style={[
                                        styles.confidenceText,
                                        { color: confidenceColor(item.confidence) }
                                    ]}>
                                        {item.confidence}% confident
                                    </Text>
                                </View>
                            </View>

                            {/* Price Comparison */}
                            <View style={styles.priceSection}>
                                <View style={styles.priceColumn}>
                                    <Text style={styles.priceLabel}>Predicted</Text>
                                    <Text style={styles.predictedPrice}>
                                        ${item.predicted_price.toFixed(2)}
                                    </Text>
                                </View>
                                <View style={styles.priceArrow}>
                                    <Text style={styles.arrowIcon}>→</Text>
                                </View>
                                <View style={styles.priceColumn}>
                                    <Text style={styles.priceLabel}>Current</Text>
                                    <Text style={styles.currentPrice}>
                                        ${item.current_price.toFixed(2)}
                                    </Text>
                                </View>
                            </View>

                            {/* Change Indicator */}
                            <View style={styles.changeSection}>
                                <Text style={[
                                    styles.changeText,
                                    { color: trendColor(item.trend) }
                                ]}>
                                    {trendIcon(item.trend)} {item.trend} prediction
                                </Text>
                                <Text style={styles.changeAmount}>
                                    {item.predicted_price > item.current_price ? '+' : ''}
                                    ${(item.predicted_price - item.current_price).toFixed(2)} 
                                    ({((item.predicted_price - item.current_price) / item.current_price * 100).toFixed(1)}%)
                                </Text>
                            </View>

                            {/* Metrics Row */}
                            <View style={styles.metricsRow}>
                                <View style={styles.metricItem}>
                                    <Text style={styles.metricIcon}>📊</Text>
                                    <Text style={[
                                        styles.metricText,
                                        { color: getVolatilityColor(item.volatility) }
                                    ]}>
                                        {item.volatility}
                                    </Text>
                                </View>
                                <View style={styles.metricItem}>
                                    <Text style={styles.metricIcon}>
                                        {getSentimentEmoji(item.sentiment)}
                                    </Text>
                                    <Text style={styles.metricText}>{item.sentiment}</Text>
                                </View>
                                <View style={styles.metricItem}>
                                    <Text style={styles.metricIcon}>⏱️</Text>
                                    <Text style={styles.metricText}>
                                        {item.days_ahead}d ahead
                                    </Text>
                                </View>
                            </View>

                            {/* Model Info */}
                            {item.model_used && (
                                <View style={styles.modelBadge}>
                                    <Text style={styles.modelBadgeText}>
                                        🤖 {item.model_used}
                                    </Text>
                                </View>
                            )}
                        </TouchableOpacity>
                    ))
                )}
            </ScrollView>
        </View>
    );
}
        
const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#000',
        paddingTop: 60,
    },
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#000',
    },
    loadingText: {
        color: '#00ccff',
        marginTop: 12,
        fontSize: 16,
    },
    header: {
        paddingHorizontal: 20,
        marginBottom: 20,
    },
    title: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#00ccff',
        textAlign: 'center',
        marginBottom: 8,
    },
    subtitle: {
        fontSize: 16,
        color: '#666',
        textAlign: 'center',
    },
    controlsSection: {
        paddingHorizontal: 20,
        marginBottom: 20,
    },
    searchInput: {
        backgroundColor: '#111',
        borderColor: '#333',
        borderWidth: 1,
        borderRadius: 12,
        padding: 16,
        color: '#fff',
        fontSize: 16,
        marginBottom: 16,
    },
    filterButtons: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        gap: 8,
    },
    filterButton: {
        flex: 1,
        paddingVertical: 12,
        paddingHorizontal: 16,
        borderRadius: 8,
        backgroundColor: '#111',
        borderWidth: 1,
        borderColor: '#333',
        alignItems: 'center',
    },
    filterButtonActive: {
        backgroundColor: '#00ccff',
        borderColor: '#00ccff',
    },
    filterButtonText: {
        color: '#ccc',
        fontSize: 14,
        fontWeight: '600',
    },
    filterButtonTextActive: {
        color: '#000',
    },
    statsContainer: {
        flexDirection: 'row',
        paddingHorizontal: 20,
        marginBottom: 20,
        gap: 12,
    },
    statCard: {
        flex: 1,
        backgroundColor: '#111',
        borderRadius: 12,
        padding: 16,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#333',
    },
    statNumber: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#00ccff',
        marginBottom: 4,
    },
    statLabel: {
        fontSize: 12,
        color: '#666',
        textAlign: 'center',
    },
    historyList: {
        flex: 1,
        paddingHorizontal: 20,
    },
    emptyContainer: {
        alignItems: 'center',
        paddingVertical: 60,
    },
    emptyIcon: {
        fontSize: 48,
        marginBottom: 16,
    },
    emptyTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#fff',
        marginBottom: 8,
        textAlign: 'center',
    },
    emptySubtitle: {
        fontSize: 16,
        color: '#666',
        textAlign: 'center',
        paddingHorizontal: 20,
    },
    predictionCard: {
        backgroundColor: '#111',
        borderRadius: 16,
        padding: 20,
        marginBottom: 16,
        borderWidth: 1,
        borderColor: '#333',
    },
    cardHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 16,
    },
    stockInfo: {
        flex: 1,
    },
    stockSymbol: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#fff',
        marginBottom: 4,
    },
    timestamp: {
        fontSize: 14,
        color: '#666',
    },
    confidenceBadge: {
        backgroundColor: '#1a1a1a',
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 16,
    },
    confidenceText: {
        fontSize: 12,
        fontWeight: '600',
    },
    priceSection: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 16,
    },
    priceColumn: {
        flex: 1,
        alignItems: 'center',
    },
    priceArrow: {
        paddingHorizontal: 16,
    },
    arrowIcon: {
        fontSize: 24,
        color: '#666',
    },
    priceLabel: {
        fontSize: 14,
        color: '#666',
        marginBottom: 4,
    },
    predictedPrice: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#00ccff',
    },
    currentPrice: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#fff',
    },
    changeSection: {
        alignItems: 'center',
        paddingVertical: 12,
        borderTopWidth: 1,
        borderTopColor: '#333',
        marginBottom: 16,
    },
    changeText: {
        fontSize: 16,
        fontWeight: '600',
        marginBottom: 4,
    },
    changeAmount: {
        fontSize: 14,
        color: '#ccc',
    },
    metricsRow: {
        flexDirection: 'row',
        justifyContent: 'space-around',
        marginBottom: 12,
    },
    metricItem: {
        alignItems: 'center',
        flex: 1,
    },
    metricIcon: {
        fontSize: 16,
        marginBottom: 4,
    },
    metricText: {
        fontSize: 12,
        color: '#ccc',
        textAlign: 'center',
    },
    modelBadge: {
        backgroundColor: '#1a1a1a',
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 8,
        alignSelf: 'flex-start',
    },
    modelBadgeText: {
        fontSize: 12,
        color: '#00ccff',
        fontWeight: '600',
    },
});