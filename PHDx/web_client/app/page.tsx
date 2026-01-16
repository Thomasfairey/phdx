'use client';

import { useState, useEffect } from 'react';
import { Sidebar, ModelSwitcher, DraftingEditor } from '@/components';
import { Wifi, WifiOff } from 'lucide-react';

interface Document {
  id: string;
  name: string;
  source: string;
}

export default function Home() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState('claude');
  const [apiStatus, setApiStatus] = useState<'online' | 'offline'>('offline');

  useEffect(() => {
    fetch('http://127.0.0.1:8000/status')
      .then(res => res.json())
      .then(() => setApiStatus('online'))
      .catch(() => setApiStatus('offline'));

    fetch('http://127.0.0.1:8000/files/recent')
      .then(res => res.json())
      .then(data => {
        setDocuments(data);
        if (data.length > 0) setSelectedDoc(data[0].id);
      })
      .catch(console.error);
  }, []);

  return (
    <div className="min-h-screen bg-[#050505]">
      <Sidebar documents={documents} selectedDoc={selectedDoc} onSelectDoc={setSelectedDoc} />
      
      <main className="ml-[260px] min-h-screen p-6">
        <header className="glass-panel px-6 py-4 mb-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <ModelSwitcher selected={selectedModel} onChange={setSelectedModel} />
            <div className={`flex items-center gap-2 text-sm ${apiStatus === 'online' ? 'text-[#30D158]' : 'text-[#FF453A]'}`}>
              {apiStatus === 'online' ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
              {apiStatus === 'online' ? 'Connected' : 'Offline'}
            </div>
          </div>
        </header>

        <div className="h-[calc(100vh-140px)]">
          <DraftingEditor docId={selectedDoc} selectedModel={selectedModel} />
        </div>
      </main>
    </div>
  );
}
