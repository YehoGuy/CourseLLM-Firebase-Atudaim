"use client";
import React, { useState } from 'react';
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth';
import { useRouter } from 'next/navigation';
import { app } from '../../firebaseConfig';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const auth = getAuth(app);
    setError('');

    try {
      await signInWithEmailAndPassword(auth, email, password);
      console.log("Login Success! Redirecting...");
      router.push('/material'); 
    } catch (err: any) {
      console.error("LOGIN ERROR:", err.code, err.message);

      if (err.code === 'auth/user-not-found' || err.code === 'auth/invalid-credential' || err.code === 'auth/invalid-login-credentials') {
        try {
          console.log("User not found. Attempting to auto-register...");
          await createUserWithEmailAndPassword(auth, email, password);
          console.log("Registration Success! Redirecting...");
          router.push('/material');
        } catch (signUpErr: any) {
          console.error("REGISTRATION FAILED:", signUpErr.code, signUpErr.message);
          setError('Failed to create account: ' + signUpErr.message);
        }
      } else {
        setError('Login failed: ' + err.message);
      }
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', marginTop: '50px' }}>
      <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '300px' }}>
        <h1 className="text-2xl font-bold">Login / Register</h1>
        <p className="text-sm text-gray-500">Entering a new email will auto-create an account.</p>
        
        {error && <p style={{ color: 'red' }}>{error}</p>}
        
        <input 
          type="email" 
          placeholder="Email" 
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={{ padding: '8px', border: '1px solid #ccc' }}
        />
        
        <input 
          type="password" 
          placeholder="Password" 
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={{ padding: '8px', border: '1px solid #ccc' }}
        />
        
        <button type="submit" style={{ padding: '10px', background: 'blue', color: 'white', border: 'none' }}>
          Sign In
        </button>
      </form>
    </div>
  );
}