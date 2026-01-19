'use client';

import { Shield, Activity, Link2, ClipboardCheck, Sparkles } from 'lucide-react';

export type ModuleType = 'airlock' | 'dna' | 'red-thread' | 'auditor';

interface SidebarProps {
  activeModule: ModuleType;
  onModuleChange: (module: ModuleType) => void;
}

const modules = [
  {
    id: 'airlock' as ModuleType,
    name: 'Airlock',
    description: 'PII Sanitization',
    icon: Shield,
    gradient: 'from-cyan-500 to-blue-600',
    activeColor: 'text-cyan-400',
    activeBg: 'from-cyan-500/20 to-blue-600/20',
    activeBorder: 'border-cyan-500/30'
  },
  {
    id: 'dna' as ModuleType,
    name: 'DNA',
    description: 'Style Analysis',
    icon: Activity,
    gradient: 'from-purple-500 to-pink-600',
    activeColor: 'text-purple-400',
    activeBg: 'from-purple-500/20 to-pink-600/20',
    activeBorder: 'border-purple-500/30'
  },
  {
    id: 'red-thread' as ModuleType,
    name: 'Red Thread',
    description: 'Continuity Check',
    icon: Link2,
    gradient: 'from-red-500 to-orange-600',
    activeColor: 'text-red-400',
    activeBg: 'from-red-500/20 to-orange-600/20',
    activeBorder: 'border-red-500/30'
  },
  {
    id: 'auditor' as ModuleType,
    name: 'Auditor',
    description: 'Quality Score',
    icon: ClipboardCheck,
    gradient: 'from-green-500 to-emerald-600',
    activeColor: 'text-green-400',
    activeBg: 'from-green-500/20 to-emerald-600/20',
    activeBorder: 'border-green-500/30'
  }
];

export function Sidebar({ activeModule, onModuleChange }: SidebarProps) {
  return (
    <aside className="fixed left-0 top-0 h-screen w-[280px] glass-panel rounded-none border-l-0 border-t-0 border-b-0 flex flex-col z-50">
      {/* Logo */}
      <div className="p-6 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#007AFF] to-[#BF5AF2] flex items-center justify-center shadow-lg shadow-purple-500/20">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold neon-text">PHDx</h1>
            <p className="text-xs text-[#8A8F98]">Mission Control</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4">
        <p className="text-xs uppercase tracking-wider text-[#8A8F98] mb-4 px-2">
          Core Engines
        </p>
        <div className="space-y-2">
          {modules.map((module) => {
            const isActive = activeModule === module.id;
            const Icon = module.icon;

            return (
              <button
                key={module.id}
                onClick={() => onModuleChange(module.id)}
                className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all text-left ${
                  isActive
                    ? `bg-gradient-to-r ${module.activeBg} border ${module.activeBorder}`
                    : 'hover:bg-white/5 border border-transparent'
                }`}
              >
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                  isActive
                    ? `bg-gradient-to-br ${module.gradient}`
                    : 'bg-white/5'
                }`}>
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-[#8A8F98]'}`} />
                </div>
                <div>
                  <span className={`text-sm font-medium block ${
                    isActive ? module.activeColor : 'text-white'
                  }`}>
                    {module.name}
                  </span>
                  <span className="text-xs text-[#8A8F98]">
                    {module.description}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-white/5">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs text-[#8A8F98]">API Connected</span>
          <span className="text-xs text-[#8A8F98] ml-auto">localhost:8000</span>
        </div>
      </div>
    </aside>
  );
}
