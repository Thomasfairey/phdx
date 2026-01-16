'use client';

import { useState } from 'react';
import { FileText, Sparkles } from 'lucide-react';

interface Document {
  id: string;
  name: string;
  source: string;
}

interface SidebarProps {
  documents: Document[];
  selectedDoc: string | null;
  onSelectDoc: (id: string) => void;
}

export function Sidebar({ documents, selectedDoc, onSelectDoc }: SidebarProps) {
  return (
    <aside className="fixed left-0 top-0 h-screen w-[260px] glass-panel rounded-none border-l-0 border-t-0 border-b-0 flex flex-col z-50">
      <div className="p-6 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#007AFF] to-[#BF5AF2] flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold neon-text">PHDx</h1>
            <p className="text-xs text-[#8A8F98]">Command Center</p>
          </div>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4">
        <p className="text-xs uppercase tracking-wider text-[#8A8F98] mb-3 px-2">Documents</p>
        <div className="space-y-1">
          {documents.map((doc) => (
            <button
              key={doc.id}
              onClick={() => onSelectDoc(doc.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-left ${
                selectedDoc === doc.id
                  ? 'bg-gradient-to-r from-[#007AFF]/20 to-[#BF5AF2]/20 border border-[#007AFF]/30'
                  : 'hover:bg-white/5'
              }`}
            >
              <FileText className={`w-4 h-4 ${selectedDoc === doc.id ? 'text-[#007AFF]' : 'text-[#8A8F98]'}`} />
              <span className={`text-sm truncate ${selectedDoc === doc.id ? 'text-white' : 'text-[#8A8F98]'}`}>
                {doc.name}
              </span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
