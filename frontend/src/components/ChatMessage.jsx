import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User, ExternalLink, Check, Copy, CheckCircle2, XCircle } from 'lucide-react';

export default function ChatMessage({ message, onConfirmAction }) {
  const [copied, setCopied] = useState(false);
  const isBot = message.sender === 'bot';
  const isError = message.isError;

  const handleCopy = () => {
    navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Check if message asks for confirmation (Human-in-the-Loop)
  const isConfirmationPrompt = isBot && (
    (message.text.includes('Do you approve?') || 
     message.text.includes('(Yes/No)') || 
     message.text.toLowerCase().includes("reply with 'yes'") || 
     message.text.toLowerCase().includes("reply with **'yes'**"))
  );

  return (
    <div className={`message-wrapper ${message.sender}`}>
      <div className={`message-avatar ${message.sender}`}>
        {isBot ? <Bot size={18} /> : <User size={18} />}
      </div>

      <div className="message-content-container">
        <div className={`message-bubble ${message.sender} ${isError ? 'error' : ''}`}>
          {isBot ? (
            <div className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.text}
              </ReactMarkdown>
            </div>
          ) : (
            <div>{message.text}</div>
          )}

          {/* Source URL citation badge */}
          {message.source && (
            <a 
              href={message.source} 
              target="_blank" 
              rel="noopener noreferrer" 
              className="source-citation"
            >
              <ExternalLink size={13} />
              <span>Official Reference: {message.source.replace(/^https?:\/\//, '')}</span>
            </a>
          )}

          {/* Quick confirmation action buttons for HITL recharge flows */}
          {isConfirmationPrompt && (
            <div className="hitl-actions">
              <button 
                className="hitl-btn approve" 
                onClick={() => onConfirmAction('Yes')}
              >
                <CheckCircle2 size={15} />
                Approve (Yes)
              </button>
              <button 
                className="hitl-btn cancel" 
                onClick={() => onConfirmAction('No')}
              >
                <XCircle size={15} />
                Cancel (No)
              </button>
            </div>
          )}
        </div>

        <div className="message-meta">
          <span className="message-time">{message.timestamp}</span>
          <button 
            className="copy-btn" 
            onClick={handleCopy} 
            title="Copy message"
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
          </button>
        </div>
      </div>
    </div>
  );
}
