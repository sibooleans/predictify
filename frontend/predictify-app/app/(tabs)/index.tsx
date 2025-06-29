import { View, Text, Button, StyleSheet, useColorScheme} from 'react-native';
import { Link } from 'expo-router';

export default function HomeScreen() {
  const colorScheme = useColorScheme();
  const darkMode = colorScheme === "dark";

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      padding: 24,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: darkMode ? '#000' : '#fff',
    },
    title: {
      fontSize: 28,
      fontWeight: 'bold',
      marginBottom: 12,
      textAlign: 'center',
      color: darkMode ? '#fff' : '#000',
    },
    subtitle: {
      fontSize: 16,
      marginBottom: 20,
      textAlign: 'center',
      color: darkMode ? '#aaa' : '#666',
    },
  });

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Welcome to Predictify</Text>
      <Text style={styles.subtitle}>
        Your personal AI assistant for stock market insights.
      </Text>

      <Link href="/predict" asChild>
        <Button title="Start Predicting" />
      </Link>
    </View>
  );
}




