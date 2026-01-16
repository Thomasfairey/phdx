'use client';

import { useState } from 'react';
import { Send, Cloud, Loader2 } from 'lucide-react';

interface DraftingEditorProps {
  docId: string | null;
  selectedModel: string;
}

export function DraftingEditor({ docId, selectedModel }: DraftingEditorProps) {
  const [prompt, setPrompt] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (!docId || !prompt) return;
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doc_id: docId, prompt, model: selectedModel }),
      });
      const data = await res.json();
      if (data.success) setOutput(data.text);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full gap-4">
      <div className="glass-panel p-4">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Enter your prompt..."
          className="w-full h-24 p-3 bg-transparent"
        />
        <div className="flex justify-between items-center mt-3">
          <div className="flex gap-2">
            <button onClick={() => setPrompt('Summarize this section')} className="px-3 py-1 text-xs bg-white/5 rounded-full hover:bg-white/10">Summarize</button>
            <button onClick={() => setPrompt('Expand on this argument')} className="px-3 py-1 text-xs bg-white/5 rounded-full hover:bg-white/10">Expand</button>
          </div>
          <button onClick={handleGenerate} disabled={loading || !docId} className="btn-primary flex items-center gap-2">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            Generate
          </button>
        </div>
      </div>
      
      <div className="flex-1 glass-panel p-6 overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-medium text-[#8A8F98]">Output</h3>
          <button className="flex items-center gap-2 text-xs text-[#007AFF] hover:text-[#64D2FF]">
            <Cloud className="w-3 h-3" /> Sync to Cloud
          </button>
        </div>
        <div className="prose prose-invert max-w-none" style={{ fontFamily: 'Merriweather, serif' }}>
          {output || <span className="text-[#8A8F98] italic">Generated content will appear here...</span>}
        </div>
      </div>
    </div>
  );
}
