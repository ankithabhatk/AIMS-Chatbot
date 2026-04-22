"use client";

import React from 'react';
import { useChat } from '../../context/ChatContext';
import { ChatItem } from './ChatItem';
import { UserProfile } from './UserProfile';
import { AdmissionContact } from './AdmissionContact';

export const Sidebar: React.FC = () => {
  const { conversations, currentConversationId, switchConversation, startNewConversation, renameConversation, deleteConversation, profile } = useChat();

  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <button
          onClick={startNewConversation}
          className="new-chat-btn"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          New Chat
        </button>
      </div>
      
      <div className="sidebar-history">
        <h3 className="history-title">RECENT HISTORY</h3>
        
        {conversations.length === 0 ? (
          <div style={{ padding: '0 12px', fontSize: '13px', color: 'var(--text-light)', fontStyle: 'italic' }}>
            No previous conversations.
          </div>
        ) : (
          conversations.map(conv => (
            <ChatItem
              key={conv.id}
              id={conv.id}
              title={conv.title}
              timestamp={conv.updatedAt}
              isActive={conv.id === currentConversationId}
              onClick={() => switchConversation(conv.id)}
              onRename={renameConversation}
              onDelete={deleteConversation}
            />
          ))
        )}
      </div>

      <div className="sidebar-footer-container">
        <AdmissionContact />
        <UserProfile profile={profile} />
      </div>
    </aside>
  );
};
