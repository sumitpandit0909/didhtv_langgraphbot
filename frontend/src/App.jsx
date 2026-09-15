import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, Sparkles, AlertCircle } from 'lucide-react';
import Header from './components/Header';
import ChatMessage from './components/ChatMessage';
import QuickActions from './components/QuickActions';
import SettingsModal from './components/SettingsModal';

const INITIAL_WELCOME = {
  id: 'welcome-1',
  sender: 'bot',
  text: "Hello! 👋 I'm **DishBot**, your AI assistant for DishTV.\n\nI can help you with:\n- 📦 **Products & Devices**: Set-top boxes, smart TV keys, remotes & pricing\n- 💳 **Recharge Packs & Plans**: Browse dynamic catalog & instant recharges\n- 📜 **Transaction History**: View your recent account recharges\n- 🛠️ **Troubleshooting**: Step-by-step diagnostics for Error 101/102, Rain Fade, etc.\n- 🏢 **Company Information**: Learn about TechChefz & DishTV solutions\n\nHow can I assist you today?",
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
};

export default function App() {
  const [messages, setMessages] = useState([INITIAL_WELCOME]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState('checking');
  const [userId, setUserId] = useState(() => localStorage.getItem('dishbot_user_id') || 'user_123');
  const [conversationId, setConversationId] = useState(() => 
    localStorage.getItem('dishbot_conv_id') || `session_${Math.random().toString(36).substring(2, 8)}`
  );
  const [backendUrl, setBackendUrl] = useState(() => 
    localStorage.getItem('dishbot_backend_url') || 'http://localhost:8000'
  );
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Sync session state to localStorage
  useEffect(() => {
    localStorage.setItem('dishbot_user_id', userId);
  }, [userId]);

  useEffect(() => {
    localStorage.setItem('dishbot_conv_id', conversationId);
  }, [conversationId]);

  useEffect(() => {
    localStorage.setItem('dishbot_backend_url', backendUrl);
  }, [backendUrl]);

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Check backend health periodically
  const checkHealth = async () => {
    try {
      const res = await fetch(`${backendUrl}/health`, { method: 'GET' });
      if (res.ok) {
        setBackendStatus('online');
      } else {
        setBackendStatus('offline');
      }
    } catch {
      setBackendStatus('offline');
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, [backendUrl]);

  // Start fresh conversation
  const handleNewChat = () => {
    const newConvId = `session_${Math.random().toString(36).substring(2, 8)}`;
    setConversationId(newConvId);
    setMessages([
      {
        ...INITIAL_WELCOME,
        id: `welcome-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
  };

  // Send message to FastAPI backend
  const handleSendMessage = async (customText = null) => {
    const textToSend = (customText !== null ? customText : inputText).trim();
    if (!textToSend || isLoading) return;

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMsg = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: timeStr
    };

    setMessages((prev) => [...prev, userMsg]);
    if (customText === null) {
      setInputText('');
    }
    setIsLoading(true);

    try {
      const response = await fetch(`${backendUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: textToSend,
          user_id: userId,
          conversation_id: conversationId
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: 'Server Error' }));
        throw new Error(errData.detail || `HTTP error ${response.status}`);
      }

      const data = await response.json();

      const botMsg = {
        id: `bot-${Date.now()}`,
        sender: 'bot',
        text: data.response || 'No response returned from agent.',
        source: data.source || null,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, botMsg]);
      setBackendStatus('online');
    } catch (err) {
      console.error('Chat error:', err);
      const errorMsg = {
        id: `err-${Date.now()}`,
        sender: 'bot',
        text: `⚠️ **Unable to connect to DishBot agent.**\n\n${err.message}\n\nPlease verify that the FastAPI backend is running on \`${backendUrl}\` with \`uv run uvicorn app.main:app --reload\`.`,
        isError: true,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
      setBackendStatus('offline');
    } finally {
      setIsLoading(false);
      // Refocus input
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <Header 
        backendStatus={backendStatus}
        onNewChat={handleNewChat}
        onOpenSettings={() => setIsSettingsOpen(true)}
        userId={userId}
        conversationId={conversationId}
      />

      {/* Main Chat Canvas */}
      <main className="chat-canvas">
        {messages.map((msg) => (
          <ChatMessage 
            key={msg.id} 
            message={msg} 
            onConfirmAction={(val) => handleSendMessage(val)}
          />
        ))}

        {isLoading && (
          <div className="message-wrapper bot">
            <div className="message-avatar bot">
              <Bot size={18} />
            </div>
            <div className="message-content-container">
              <div className="message-bubble bot typing-indicator">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* Quick Actions Bar */}
      <QuickActions 
        onSelectPrompt={(prompt) => handleSendMessage(prompt)}
        disabled={isLoading}
      />

      {/* Message Input Section */}
      <footer className="input-section">
        <div className="input-box-wrapper">
          <textarea
            ref={textareaRef}
            rows={1}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your question or request here (Press Enter to send)..."
            className="chat-input"
            disabled={isLoading}
          />
          <button 
            className="send-btn" 
            onClick={() => handleSendMessage()}
            disabled={!inputText.trim() || isLoading}
            title="Send Message"
          >
            <Send size={16} />
          </button>
        </div>

        <div className="input-footer">
          <span 
            className="active-session-pill" 
            onClick={() => setIsSettingsOpen(true)}
            title="Click to change session or user"
          >
            User: <strong>{userId}</strong> &bull; Thread: <strong>{conversationId}</strong>
          </span>
          <span>Powered by LangGraph & FastAPI</span>
        </div>
      </footer>

      {/* Settings Modal */}
      <SettingsModal 
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        userId={userId}
        setUserId={setUserId}
        conversationId={conversationId}
        setConversationId={setConversationId}
        backendUrl={backendUrl}
        setBackendUrl={setBackendUrl}
      />
    </div>
  );
}
