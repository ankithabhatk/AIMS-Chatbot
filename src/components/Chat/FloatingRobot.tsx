"use client";

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useChat } from '../../context/ChatContext';
import { RobotAvatar } from './RobotAvatar';

export const FloatingRobot: React.FC = () => {
  const { isChatOpen, setIsChatOpen } = useChat();

  return (
    <AnimatePresence>
      {!isChatOpen && (
        <motion.div
          className="floating-robot-trigger"
          initial={{ scale: 0, opacity: 0, y: 50, rotate: -20 }}
          animate={{ scale: 1, opacity: 1, y: 0, rotate: 0 }}
          exit={{ scale: 0, opacity: 0, y: 50, rotate: 20 }}
          whileHover={{ 
            scale: 1.1, 
            y: -8,
            transition: { type: "spring", stiffness: 400, damping: 10 }
          }}
          whileTap={{ scale: 0.9 }}
          onClick={() => setIsChatOpen(true)}
          style={{
            position: 'fixed',
            bottom: '30px',
            right: '30px',
            zIndex: 1000,
            cursor: 'pointer',
            padding: '10px'
          }}
        >
          <RobotAvatar size={60} eyesOpen={false} isAnimated={true} className="text-white" />
          
          <AnimatePresence>
            <motion.div 
              className="robot-label"
              initial={{ opacity: 0, x: 20, scale: 0.8 }}
              animate={{ 
                opacity: [0, 1, 1, 0],
                x: [20, -10, -10, 20],
                scale: [0.8, 1, 1, 0.8]
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                repeatDelay: 6,
                times: [0, 0.1, 0.9, 1]
              }}
              style={{
                position: 'absolute',
                right: '100%',
                backgroundColor: 'var(--aims-primary)',
                color: 'white',
                padding: '10px 20px',
                borderRadius: '16px',
                whiteSpace: 'nowrap',
                fontSize: '14px',
                fontWeight: '700',
                pointerEvents: 'none',
                marginRight: '20px',
                boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
                border: '1px solid rgba(255,255,255,0.1)'
              }}
            >
              Hi! Need any help? 👋
              <div style={{
                position: 'absolute',
                right: '-8px',
                top: '50%',
                transform: 'translateY(-50%) rotate(45deg)',
                width: '12px',
                height: '12px',
                backgroundColor: 'var(--aims-primary)',
                borderRight: '1px solid rgba(255,255,255,0.1)',
                borderTop: '1px solid rgba(255,255,255,0.1)'
              }}></div>
            </motion.div>
          </AnimatePresence>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
