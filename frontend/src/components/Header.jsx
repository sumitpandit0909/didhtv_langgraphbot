import React from 'react';
import { Tv, RefreshCw, Settings, Activity } from 'lucide-react';

export default function Header({ 
  backendStatus, 
  onNewChat, 
  onOpenSettings, 
  userId, 
  conversationId 
}) {
  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-logo-badge">
          <Tv size={22} strokeWidth={2.2} />
        </div>
        <div className="brand-meta">
          <h1>
            DishBot
            <span className="brand-pill">Agentic Support</span>
          </h1>
          <p>DishTV Intelligent Conversational Assistant</p>
        </div>
      </div>

      <div className="header-actions">
        {/* Backend health status badge */}
        <div 
          className="status-badge" 
          title={`Backend Server: ${backendStatus}`}
        >
          <span className={`status-dot ${backendStatus}`}></span>
          <span>
            {backendStatus === 'online' ? 'Connected' : backendStatus === 'offline' ? 'Offline' : 'Connecting...'}
          </span>
        </div>

        {/* New chat / restart session button */}
        <button 
          className="icon-btn" 
          onClick={onNewChat} 
          title="Start Fresh Conversation"
        >
          <RefreshCw size={17} />
        </button>

        {/* Settings button */}
        <button 
          className="icon-btn" 
          onClick={onOpenSettings} 
          title="Session & User Settings"
        >
          <Settings size={17} />
        </button>
      </div>
    </header>
  );
}
