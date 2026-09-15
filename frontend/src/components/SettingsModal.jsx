import React, { useState } from 'react';
import { X } from 'lucide-react';

export default function SettingsModal({ 
  isOpen, 
  onClose, 
  userId, 
  setUserId, 
  conversationId, 
  setConversationId,
  backendUrl,
  setBackendUrl
}) {
  const [localUser, setLocalUser] = useState(userId);
  const [localConv, setLocalConv] = useState(conversationId);
  const [localUrl, setLocalUrl] = useState(backendUrl);

  if (!isOpen) return null;

  const handleSave = (e) => {
    e.preventDefault();
    setUserId(localUser.trim() || 'user_123');
    setConversationId(localConv.trim() || `session_${Date.now()}`);
    setBackendUrl(localUrl.trim() || 'http://localhost:8000');
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Session & API Configuration</h3>
          <button className="icon-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSave}>
          <div className="field-group">
            <label>Backend API Base URL</label>
            <input 
              type="text" 
              value={localUrl} 
              onChange={(e) => setLocalUrl(e.target.value)}
              placeholder="http://localhost:8000"
            />
            <p className="field-hint">Points to the FastAPI server running the LangGraph workflow.</p>
          </div>

          <div className="field-group">
            <label>User ID / VC Number</label>
            <input 
              type="text" 
              value={localUser} 
              onChange={(e) => setLocalUser(e.target.value)}
              placeholder="user_123"
            />
            <p className="field-hint">Default <code>user_123</code> has 3 seeded recharge records for history check.</p>
          </div>

          <div className="field-group">
            <label>Conversation ID (Thread)</label>
            <input 
              type="text" 
              value={localConv} 
              onChange={(e) => setLocalConv(e.target.value)}
              placeholder="session_1"
            />
            <p className="field-hint">LangGraph MemorySaver thread key for multi-turn conversational state.</p>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
