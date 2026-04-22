import React, { useState } from 'react';

interface ChatItemProps {
  id: string;
  title: string;
  timestamp: number;
  isActive: boolean;
  onClick: () => void;
  onRename: (id: string, newTitle: string) => void;
  onDelete: (id: string) => void;
}

export const ChatItem: React.FC<ChatItemProps> = ({
  id,
  title,
  timestamp,
  isActive,
  onClick,
  onRename,
  onDelete
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(title);

  const handleRenameSubmit = () => {
    if (editValue.trim() && editValue.trim() !== title) {
      onRename(id, editValue.trim());
    } else {
      setEditValue(title);
    }
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleRenameSubmit();
    if (e.key === 'Escape') {
      setEditValue(title);
      setIsEditing(false);
    }
  };

  return (
    <div className={`chat-item ${isActive ? 'active' : ''}`} onClick={!isEditing ? onClick : undefined}>
      <div className="chat-item-content">
        {isEditing ? (
          <input 
            type="text" 
            className="chat-item-rename-input"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={handleRenameSubmit}
            onKeyDown={handleKeyDown}
            autoFocus
            onClick={(e) => e.stopPropagation()}
            style={{ 
              width: '100%', 
              background: 'transparent', 
              border: 'none', 
              fontSize: '13px', 
              outline: 'none',
              color: 'inherit'
            }}
          />
        ) : (
          <div className="chat-item-title">{title}</div>
        )}
      </div>
      
      {!isEditing && (
        <div className="chat-item-actions" onClick={(e) => e.stopPropagation()}>
          <button 
            className="chat-action-btn" 
            onClick={() => setIsEditing(true)}
            title="Rename"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
          </button>
          <button 
            className="chat-action-btn delete" 
            onClick={() => onDelete(id)}
            title="Delete"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
          </button>
        </div>
      )}
    </div>
  );
};
