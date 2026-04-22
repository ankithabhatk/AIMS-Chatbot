"use client";

import React from 'react';
import { motion } from 'framer-motion';

interface RobotAvatarProps {
  size?: number;
  eyesOpen?: boolean;
  isAnimated?: boolean;
  className?: string;
}

export const RobotAvatar: React.FC<RobotAvatarProps> = ({ 
  size = 40, 
  eyesOpen = true, 
  isAnimated = true,
  className = "" 
}) => {
  return (
    <div 
      className={`robot-avatar-container ${className}`}
      style={{ width: size, height: size, position: 'relative' }}
    >
      {isAnimated && (
        <motion.div
          className="robot-glow-outer"
          style={{
            position: 'absolute',
            top: '-20%',
            left: '-20%',
            right: '-20%',
            bottom: '-20%',
            borderRadius: '50%',
            background: 'radial-gradient(circle, var(--aims-accent) 0%, transparent 70%)',
            zIndex: -1,
          }}
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.1, 0.3, 0.1]
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      )}
      
      <motion.div 
        className={`robot-svg-wrapper ${className}`}
        animate={isAnimated ? {
          y: [0, -4, 0],
          rotate: [0, 1, -1, 0]
        } : {}}
        transition={{
          duration: 5,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      >
        <svg 
          viewBox="0 0 100 100" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
          style={{ width: size, height: size }}
        >
          {/* Head Shell */}
          <rect x="15" y="20" width="70" height="60" rx="20" fill="currentColor" fillOpacity="0.1" />
          <rect x="15" y="20" width="70" height="60" rx="20" stroke="currentColor" strokeWidth="4" />
          
          {/* Antennas */}
          <motion.g
            animate={isAnimated ? { rotate: [0, 5, -5, 0] } : {}}
            transition={{ duration: 2, repeat: Infinity }}
            style={{ originX: '50px', originY: '20px' }}
          >
            <line x1="50" y1="20" x2="50" y2="5" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
            <circle cx="50" cy="5" r="4" fill="currentColor" />
          </motion.g>
          
          {/* Face Display area */}
          <rect x="25" y="35" width="50" height="30" rx="10" fill="currentColor" fillOpacity="0.2" />
          
          {/* Eyes */}
          <motion.ellipse 
            cx="40" 
            cy="50" 
            rx="5" 
            ry={eyesOpen ? 5 : 1} 
            fill="currentColor"
            animate={isAnimated && eyesOpen ? { 
              scaleY: [1, 1, 0.1, 1, 1, 1, 0.1, 1],
              transition: { duration: 6, repeat: Infinity, times: [0, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1] }
            } : {}}
          />
          <motion.ellipse 
            cx="60" 
            cy="50" 
            rx="5" 
            ry={eyesOpen ? 5 : 1} 
            fill="currentColor"
            animate={isAnimated && eyesOpen ? { 
              scaleY: [1, 1, 0.1, 1, 1, 1, 0.1, 1],
              transition: { duration: 6, repeat: Infinity, times: [0, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1], delay: 0.1 }
            } : {}}
          />
          
          {/* Mouth/Lights */}
          <motion.rect 
            x="42" y="60" width="16" height="2" rx="1" fill="currentColor" 
            animate={isAnimated ? { opacity: [0.4, 1, 0.4] } : {}}
            transition={{ duration: 2, repeat: Infinity }}
          />
        </svg>
      </motion.div>
    </div>
  );
};
