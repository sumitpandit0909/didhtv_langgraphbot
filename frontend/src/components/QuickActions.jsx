import React from 'react';
import { Package, CreditCard, Zap, History, Wrench, Building2, Headset } from 'lucide-react';

const PROMPTS = [
  { label: 'Dish SMRT Hub Info', text: 'Tell me about Dish SMRT Hub', icon: Package },
  { label: 'Browse Packages', text: 'What recharge packages are available?', icon: CreditCard },
  { label: 'Recharge Super Family', text: 'I want to recharge Super Family', icon: Zap },
  { label: 'My Past Recharges', text: 'Show my last transactions', icon: History },
  { label: 'Fix Error 101', text: 'My TV shows Error 101, how to fix?', icon: Wrench },
  { label: 'TechChefz Info (RAG)', text: 'What services does TechChefz provide?', icon: Building2 },
  { label: 'Live Agent Support', text: 'I want to talk to an agent', icon: Headset },
];

export default function QuickActions({ onSelectPrompt, disabled }) {
  return (
    <div className="quick-tray">
      {PROMPTS.map((item, idx) => {
        const IconComponent = item.icon;
        return (
          <button
            key={idx}
            className="quick-chip"
            onClick={() => onSelectPrompt(item.text)}
            disabled={disabled}
            type="button"
          >
            <IconComponent size={14} />
            <span>{item.label}</span>
          </button>
        );
      })}
    </div>
  );
}
