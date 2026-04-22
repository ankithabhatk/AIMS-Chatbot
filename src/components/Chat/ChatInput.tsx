"use client";

import React, { useState, KeyboardEvent } from 'react';
import { useChat } from '../../context/ChatContext';

export const ChatInput: React.FC = () => {
  const { sendMessage, isLoading } = useChat();
  const [query, setQuery] = useState('');

  const handleSend = () => {
    if (query.trim()) {
      sendMessage(query);
      setQuery('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-input-container">
      <div className="chat-input-wrapper">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your inquiry here..."
          className="chat-textarea"
          disabled={isLoading}
          aria-label="Chat input field"
          rows={1}
        />
        <button
          onClick={handleSend}
          disabled={isLoading || !query.trim()}
          className="chat-send-btn"
          aria-label="Send message button"
          title="Send message"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2.01 21L23 12L2.01 3L2 10l15 2-15 2z" fill="currentColor" />
          </svg>
        </button>
      </div>
    </div>
  );
};
