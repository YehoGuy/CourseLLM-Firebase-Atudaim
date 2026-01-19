// components/FileUploader.tsx
'use client';

import { ChangeEvent, FormEvent } from 'react';

interface Props {
  file: File | null;
  loading: boolean;
  onFileChange: (file: File) => void;
  onUpload: (e: FormEvent) => void;
}

export default function FileUploader({ file, loading, onFileChange, onUpload }: Props) {
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      onFileChange(e.target.files[0]);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8">
      <h2 className="text-lg font-semibold mb-4">Upload Document</h2>
      <form onSubmit={onUpload} className="flex gap-4 items-center">
        <input 
          type="file" 
          accept=".pdf,.docx,.pptx" 
          onChange={handleChange}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
        <button 
          type="submit" 
          disabled={!file || loading}
          className={`px-8 py-2 rounded-full text-white font-medium transition-colors ${
            loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {loading ? 'Processing...' : 'Convert'}
        </button>
      </form>
    </div>
  );
}