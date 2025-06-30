import { View, Text, StyleSheet, Button, ScrollView } from 'react-native';
import { Link } from 'expo-router';

export default function HomeScreen() {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>📈 Welcome to Predictify</Text>
      <Text style={styles.subtitle}>
        Your AI-powered assistant for smarter investing.
      </Text>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}> What can you do here?</Text>
        <Text style={styles.text}>• Predict stock prices using AI</Text>
        <Text style={styles.text}>• View confidence levels & trends</Text>
        <Text style={styles.text}>• Track volatility & get insights</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}> Ready to go?</Text>
        <Link href="/predict" asChild>
          <Button title="Start Predicting" />
        </Link>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}> Manage your account</Text>
        <Link href="/profile" asChild>
          <Button title="View Profile" />
        </Link>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 24,
    backgroundColor: '#000',
    justifyContent: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#00ccff',
    textAlign: 'center',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    color: '#aaa',
    textAlign: 'center',
    marginBottom: 20,
  },
  section: {
    marginBottom: 28,
    paddingHorizontal: 10,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 8,
  },
  text: {
    color: '#ccc',
    marginLeft: 10,
    marginBottom: 4,
  },
});