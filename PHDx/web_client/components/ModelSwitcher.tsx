'use client';

interface ModelSwitcherProps {
  selected: string;
  onChange: (model: string) => void;
}

export function ModelSwitcher({ selected, onChange }: ModelSwitcherProps) {
  const models = ['claude', 'gpt', 'gemini'];
  
  return (
    <div className="inline-flex items-center gap-1 p-1 bg-black/40 backdrop-blur-md border border-white/5 rounded-full">
      {models.map((model) => (
        <button
          key={model}
          onClick={() => onChange(model)}
          className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
            selected === model
              ? 'bg-gradient-to-r from-[#007AFF] to-[#BF5AF2] text-white shadow-lg'
              : 'text-[#8A8F98] hover:text-white'
          }`}
        >
          {model.charAt(0).toUpperCase() + model.slice(1)}
        </button>
      ))}
    </div>
  );
}
