"use client";

import React, { useState, KeyboardEvent, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useChat } from '../../context/ChatContext';

export const ChatInput: React.FC = () => {
  const { sendMessage, isLoading } = useChat();
  const [query, setQuery] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (query.trim() && !isLoading) {
      sendMessage(query);
      setQuery('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [query]);

  return (
    <div className="input-container">
      <textarea
        ref={textareaRef}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your inquiry here..."
        className="chat-textarea"
        disabled={isLoading}
        rows={1}
      />
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {/* Voice button could go here */}
        <motion.button
          onClick={handleSend}
          disabled={isLoading || !query.trim()}
          className={`send-btn ${query.trim() ? 'active' : ''}`}
          whileHover={query.trim() ? { scale: 1.1 } : {}}
          whileTap={query.trim() ? { scale: 0.9 } : {}}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </motion.button>
      </div>
    </div>
  );
};
