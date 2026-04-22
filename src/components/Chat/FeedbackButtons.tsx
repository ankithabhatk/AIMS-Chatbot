"use client";

import React, { useState } from 'react';
import { motion } from 'framer-motion';

export const FeedbackButtons: React.FC = () => {
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);

  return (
    <div className="feedback-buttons" style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
      <motion.button
        whileHover={{ scale: 1.2 }}
        whileTap={{ scale: 0.8 }}
        onClick={() => setFeedback('up')}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: feedback === 'up' ? 'var(--aims-accent)' : 'var(--text-muted)',
          padding: '4px'
        }}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill={feedback === 'up' ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
        </svg>
      </motion.button>
      <motion.button
        whileHover={{ scale: 1.2 }}
        whileTap={{ scale: 0.8 }}
        onClick={() => setFeedback('down')}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: feedback === 'down' ? '#EF4444' : 'var(--text-muted)',
          padding: '4px'
        }}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill={feedback === 'down' ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zM17 2h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"></path>
        </svg>
      </motion.button>
    </div>
  );
};
