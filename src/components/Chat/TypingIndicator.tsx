"use client";

import React from 'react';
import { motion } from 'framer-motion';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="typing-indicator" style={{ display: 'flex', gap: '4px', padding: '4px 8px' }}>
      {[0, 1, 2].map((dot) => (
        <motion.div
          key={dot}
          style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'var(--text-muted)' }}
          animate={{ y: [0, -5, 0] }}
          transition={{ duration: 0.6, repeat: Infinity, ease: "easeInOut", delay: dot * 0.15 }}
        />
      ))}
    </div>
  );
};
