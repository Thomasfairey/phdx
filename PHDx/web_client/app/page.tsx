'use client';

import { useState } from 'react';
import { Sidebar, ModuleType } from '@/components/Sidebar';
import { AirlockModule } from '@/components/AirlockModule';
import { DNAModule } from '@/components/DNAModule';
import { RedThreadModule } from '@/components/RedThreadModule';
import { AuditorModule } from '@/components/AuditorModule';
import { ThesisGraph } from '@/components/ThesisGraph';

export default function Home() {
  const [activeModule, setActiveModule] = useState<ModuleType>('graph');
  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(null);

  const handleChapterSelect = (chapterId: string) => {
    setSelectedChapterId(chapterId);
    // Could switch to red-thread module to analyze the selected chapter
  };

  const renderModule = () => {
    switch (activeModule) {
      case 'graph':
        return (
          <ThesisGraph
            userId="default"
            onNodeSelect={handleChapterSelect}
          />
        );
      case 'airlock':
        return <AirlockModule />;
      case 'dna':
        return <DNAModule />;
      case 'red-thread':
        return <RedThreadModule />;
      case 'auditor':
        return <AuditorModule />;
      default:
        return (
          <ThesisGraph
            userId="default"
            onNodeSelect={handleChapterSelect}
          />
        );
    }
  };

  return (
    <div className="min-h-screen bg-[#050505]">
      {/* Sidebar Navigation */}
      <Sidebar activeModule={activeModule} onModuleChange={setActiveModule} />

      {/* Main Content Area */}
      <main className="ml-[280px] min-h-screen">
        <div className="p-8">
          {renderModule()}
        </div>
      </main>
    </div>
  );
}
