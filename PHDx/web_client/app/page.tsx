'use client';

import { useState, useEffect } from 'react';
import { Wifi, WifiOff, FileText, Send, Loader2 } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://phdx-production.up.railway.app';

interface Document {
  id: string;
  name: string;
  source: string;
}

export default function Home() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState('claude');
  const [apiStatus, setApiStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    // Check API status
    fetch(`${API_URL}/health`)
      .then(res => res.json())
      .then((data) => {
        if (data.status === 'healthy') {
          setApiStatus('online');
        } else {
          setApiStatus('offline');
        }
      })
      .catch(() => setApiStatus('offline'));

    // Load recent files
    fetch(`${API_URL}/files/recent`)
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setDocuments(data);
          if (data.length > 0) setSelectedDoc(data[0].id);
        }
      })
      .catch(console.error);
  }, []);

  const handleGenerate = async () => {
    if (!prompt.trim() || !selectedDoc) return;

    setIsGenerating(true);
    try {
      const res = await fetch(`${API_URL}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          doc_id: selectedDoc,
          prompt: prompt,
          model: selectedModel
        })
      });
      const data = await res.json();
      if (data.success) {
        setResponse(data.text);
      } else {
        setResponse(`Error: ${data.error || 'Generation failed'}`);
      }
    } catch (error) {
      setResponse('Error connecting to API');
    }
    setIsGenerating(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              PHDx
            </h1>
            <span className="text-slate-500 text-sm">PhD Thesis Command Center</span>
          </div>

          <div className="flex items-center gap-4">
            {/* Model Selector */}
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200"
            >
              <option value="claude">Claude</option>
              <option value="gpt-4">GPT-4</option>
            </select>

            {/* Status Indicator */}
            <div className={`flex items-center gap-2 text-sm px-3 py-1.5 rounded-full ${
              apiStatus === 'online'
                ? 'bg-green-900/30 text-green-400'
                : apiStatus === 'checking'
                ? 'bg-yellow-900/30 text-yellow-400'
                : 'bg-red-900/30 text-red-400'
            }`}>
              {apiStatus === 'online' ? <Wifi className="w-4 h-4" /> :
               apiStatus === 'checking' ? <Loader2 className="w-4 h-4 animate-spin" /> :
               <WifiOff className="w-4 h-4" />}
              {apiStatus === 'online' ? 'Connected' : apiStatus === 'checking' ? 'Checking...' : 'Offline'}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8 flex gap-6">
        {/* Sidebar - Documents */}
        <aside className="w-64 flex-shrink-0">
          <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-4">
            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
              Recent Documents
            </h2>
            {documents.length > 0 ? (
              <ul className="space-y-2">
                {documents.map((doc) => (
                  <li key={doc.id}>
                    <button
                      onClick={() => setSelectedDoc(doc.id)}
                      className={`w-full text-left px-3 py-2 rounded-lg flex items-center gap-2 text-sm transition-colors ${
                        selectedDoc === doc.id
                          ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                          : 'text-slate-300 hover:bg-slate-700/50'
                      }`}
                    >
                      <FileText className="w-4 h-4" />
                      <span className="truncate">{doc.name}</span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-slate-500 text-sm">
                {apiStatus === 'offline'
                  ? 'Connect API to load documents'
                  : 'No documents found'}
              </p>
            )}
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 space-y-6">
          {/* Prompt Input */}
          <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-6">
            <h2 className="text-lg font-semibold text-slate-200 mb-4">AI Writing Assistant</h2>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your prompt... (e.g., 'Help me improve the introduction section')"
              className="w-full h-32 bg-slate-900/50 border border-slate-600 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
            <div className="mt-4 flex justify-between items-center">
              <p className="text-slate-500 text-sm">
                {selectedDoc ? `Working with: ${documents.find(d => d.id === selectedDoc)?.name || selectedDoc}` : 'Select a document'}
              </p>
              <button
                onClick={handleGenerate}
                disabled={isGenerating || !prompt.trim() || apiStatus !== 'online'}
                className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Generate
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Response Output */}
          <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-6">
            <h2 className="text-lg font-semibold text-slate-200 mb-4">Response</h2>
            <div className="min-h-[200px] bg-slate-900/50 border border-slate-600 rounded-lg p-4">
              {response ? (
                <p className="text-slate-300 whitespace-pre-wrap">{response}</p>
              ) : (
                <p className="text-slate-500 italic">AI response will appear here...</p>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-4 hover:border-blue-500/50 transition-colors cursor-pointer">
              <h3 className="font-semibold text-blue-400">Thesis Writing</h3>
              <p className="text-sm text-slate-400 mt-1">AI-assisted writing and editing</p>
            </div>
            <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-4 hover:border-purple-500/50 transition-colors cursor-pointer">
              <h3 className="font-semibold text-purple-400">Literature Review</h3>
              <p className="text-sm text-slate-400 mt-1">Organize research papers</p>
            </div>
            <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-4 hover:border-green-500/50 transition-colors cursor-pointer">
              <h3 className="font-semibold text-green-400">Knowledge Base</h3>
              <p className="text-sm text-slate-400 mt-1">Search your research materials</p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
