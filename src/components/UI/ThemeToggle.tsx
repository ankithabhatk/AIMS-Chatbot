"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { useChat } from '../../context/ChatContext';

export const ThemeToggle: React.FC = () => {
  const { theme, setThemeMode } = useChat();

  const modes: ('light' | 'dark' | 'high-contrast')[] = ['light', 'dark', 'high-contrast'];

  return (
    <div 
      className="theme-selector-pill"
      style={{
        display: 'flex',
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        padding: '4px',
        borderRadius: '20px',
        border: '1px solid rgba(255, 255, 255, 0.15)',
        position: 'relative'
      }}
    >
      {modes.map((mode) => {
        const isActive = theme === mode;
        const label = mode === 'high-contrast' ? 'Contrast' : mode;
        return (
          <button
            key={mode}
            onClick={() => setThemeMode(mode)}
            style={{
              padding: '6px 14px',
              fontSize: '11px',
              fontWeight: '700',
              textTransform: 'uppercase',
              color: isActive ? 'var(--aims-bg)' : 'rgba(255, 255, 255, 0.7)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              position: 'relative',
              zIndex: 1,
              transition: 'color 0.3s ease',
              borderRadius: '16px',
              whiteSpace: 'nowrap'
            }}
          >
            {isActive && (
              <motion.div
                layoutId="theme-active-pill"
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  backgroundColor: 'var(--aims-orange)',
                  borderRadius: '16px',
                  zIndex: -1
                }}
                transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
              />
            )}
            {label}
          </button>
        );
      })}
    </div>
  );
};
