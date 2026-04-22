"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export const AnnouncementBanner: React.FC = () => {
  const [isVisible, setIsVisible] = useState(true);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="announcement-banner"
          style={{
            width: '100%',
            backgroundColor: 'rgba(99, 102, 241, 0.1)',
            border: '1px solid var(--aims-accent)',
            borderRadius: '12px',
            padding: '12px 16px',
            marginBottom: '24px',
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}
        >
          <div style={{ color: 'var(--aims-accent)' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
          </div>
          <div style={{ flex: 1, fontSize: '13px', fontWeight: '500', color: 'var(--text-main)' }}>
            <strong>Admissions Open:</strong> MBA & MCA batches for 2026 are now filling fast. Apply before April 30th to secure your seat.
          </div>
          <button 
            onClick={() => setIsVisible(false)}
            style={{ 
              background: 'none', 
              border: 'none', 
              cursor: 'pointer', 
              color: 'var(--text-muted)',
              padding: '4px'
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
