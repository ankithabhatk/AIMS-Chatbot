"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { useChat } from '../../context/ChatContext';
import { ThemeToggle } from '../UI/ThemeToggle';
import Image from 'next/image';

export const ChatHeader: React.FC = () => {
  const { isSidebarOpen, setIsSidebarOpen } = useChat();

  return (
    <header className="chat-header">
      <div className="header-left" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Hamburger — visible only on mobile via CSS; hidden on desktop */}
        <button
          className="mobile-hamburger"
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          aria-label="Toggle navigation menu"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>

        <motion.div
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          style={{ display: 'flex', alignItems: 'center', gap: '20px' }}
        >
          <div className="header-logo-container" style={{ position: 'relative', height: '40px', width: '40px' }}>
            <Image 
              src="/aims logo.jpg" 
              alt="AIMS Logo" 
              fill
              style={{ objectFit: 'contain' }}
              priority
            />
          </div>
          <div className="header-title-container">
            <h1 style={{ lineHeight: '1.2' }}>AIMS Chat Interface</h1>
            <p className="header-subtitle">Automated Academic Reference System</p>
          </div>
        </motion.div>
      </div>
      
      <div className="header-right">
        <ThemeToggle />
      </div>
    </header>
  );
};
