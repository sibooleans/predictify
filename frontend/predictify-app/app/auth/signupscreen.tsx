import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet, Alert } from 'react-native';
import { createUserWithEmailAndPassword } from 'firebase/auth';
import auth from '../../config/authentication';

const signupscreen = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    const handleCreateAccount = async () => {
        if (!email || !password || !confirmPassword) {
            Alert.alert('Missing Fields', 'Please fill in all fields.');
            return
        }

        if (password.length < 6) {
            Alert.alert('Weak password', 'Password must be at least 6 characters long.');
            return;
        }

        if (password != confirmPassword) {
            Alert.alert('Error', 'Passwords do not match.');
            return;
        }

        try {
            await createUserWithEmailAndPassword(auth, email, password);
            Alert.alert('Account Created', 'You can now log in with your new account.');
// can navigate to login screen here    
        } catch (err: any) {
            console.log('Signup error:', err.message);
            Alert.alert('Error', err.message);
        }
    };

    return (
    <View style={styles.container}>
        <Text style={styles.title}>Sign Up</Text>

        <TextInput
            placeholder = "Email"
            autoCapitalize = "none"
            keyboardType = "email-address"
            onChangeText = {setEmail}
            style = {styles.input}
        />

        <TextInput
            placeholder = "Password"
            secureTextEntry
            onChangeText = {setPassword}
            style = {styles.input}
        />

        <TextInput
            placeholder = "Confirm Password"
            secureTextEntry
            onChangeText = {setConfirmPassword}
            style = {styles.input}
        />

        <Button title="Create Account" onPress={handleCreateAccount} />
    </View>
    );
};

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
});

export default signupscreen;
   