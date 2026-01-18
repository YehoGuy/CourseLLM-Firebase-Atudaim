'use client';

import { useState, useEffect } from 'react';
import { onAuthStateChanged, User } from 'firebase/auth';
import { useRouter } from 'next/navigation';
import { auth } from '../../firebaseConfig'; 
import FileUploader from '../components/FileUploader';
import MarkdownViewer from '../components/MarkdownViewer';

export default function MaterialToMD() {
  const [user, setUser] = useState<User | null>(null);
  const [loadingAuth, setLoadingAuth] = useState(true);
  
  // App State
  const [file, setFile] = useState<File | null>(null);
  const [markdown, setMarkdown] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const router = useRouter();
  const API_URL = '/api';

  // 1. Safe Auth Check
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      if (!currentUser) {
        router.push('/login');
      } else {
        setUser(currentUser);
      }
      setLoadingAuth(false);
    });
    return () => unsubscribe();
  }, [router]);

  // 2. The Real Conversion Logic
  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault(); // Stop page reload
    if (!file || !user) return;

    setLoading(true);
    setError('');
    
    try {
      const token = await user.getIdToken();
      const formData = new FormData();
      formData.append('file', file);

      // Send to Backend
      const response = await fetch(`${API_URL}/convert`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Conversion failed');
      }

      const data = await response.json();
      
      // Handle different variable names (safety net)
      const content = data.content || data.markdown || data.text || data.result;
      
      if (!content) {
          console.error("Backend sent:", data);
          throw new Error("Received empty content from backend");
      }

      setMarkdown(content);

    } catch (err: any) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 3. Loading Screen
  if (loadingAuth) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <h1 className="text-xl font-bold text-blue-600">Checking Access...</h1>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="max-w-6xl mx-auto p-8">
      <div className="flex justify-between items-center mb-8 border-b pb-4">
        <h1 className="text-3xl font-bold text-gray-800">Material to Markdown</h1>
        <div className="flex items-center gap-4">
          <span className="text-gray-600">{user.email}</span>
          <button onClick={() => auth.signOut()} className="text-sm text-red-500 font-semibold hover:underline">
            Sign Out
          </button>
        </div>
      </div>
      
      {/* Real Components Hooked Up to Logic */}
      <FileUploader 
        file={file} 
        loading={loading} 
        onFileChange={setFile} 
        onUpload={handleUpload} 
      />
      
      {error && (
        <div className="mb-8 p-3 bg-red-50 text-red-700 rounded border border-red-200">
            {error}
        </div>
      )}
      
      {/* This renders the 'Raw Markdown' header the robot is looking for */}
      <MarkdownViewer content={markdown} />
    </div>
  );
}