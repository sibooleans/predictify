import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet, Alert } from 'react-native';
import { signInWithEmailAndPassword } from 'firebase/auth';
import auth from '../../config/authentication';
import { Link } from 'expo-router';
import { useRouter } from 'expo-router';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const router = useRouter(); 

    const handleLogin = async () => {
        if (!email || !password) {
            Alert.alert('Missing info', 'Please enter both email and password.');
            return;
        }

        try {
            await signInWithEmailAndPassword(auth, email, password);
            Alert.alert('Welcome back!', 'Login successful.');
            router.replace('/(tabs)');

            // still needa redirect to main screen
        } catch (error: any) {
            console.log('Login error:', error.message);
            Alert.alert('Login Failed', error.message);
        }
    };

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Login</Text>

            <TextInput
            placeholder="Email"
            autoCapitalize="none"
            keyboardType="email-address"
            onChangeText={setEmail}
            style={styles.input}
            />

            <TextInput
            placeholder="Password"
            secureTextEntry
            onChangeText={setPassword}
            style={styles.input}
            />

            <Button title="Log In" onPress={handleLogin} />

            <Link href="/authent/signup">
                <Text style={styles.link}>Don’t have an account? Sign up here</Text>
            </Link>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        padding: 24,
        flex: 1,
        justifyContent: 'center',
        backgroundColor: '#fff',
    },
    title: {
        fontSize: 22,
        marginBottom: 20,
        fontWeight: '600',
        textAlign: 'center',
    },
    input: {
        borderColor: '#bbb',
        borderWidth: 1,
        padding: 12,
        marginBottom: 12,
        borderRadius: 6,
    },
    link: {
        marginTop: 20,
        color: '#00ccff',
        textAlign: 'center',
    },
});
        