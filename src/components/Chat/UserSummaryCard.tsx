"use client";

import React from 'react';
import { motion } from 'framer-motion';

interface UserSummaryCardProps {
  profile: {
    name: string;
    email: string;
    mobile: string;
    course: string;
  };
}

export const UserSummaryCard: React.FC<UserSummaryCardProps> = ({ profile }) => {
  return (
    <motion.div 
      className="user-summary-card"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      style={{
        backgroundColor: 'var(--aims-primary)',
        color: 'white',
        padding: '24px',
        borderRadius: '20px',
        width: '100%',
        maxWidth: '400px',
        boxShadow: '0 10px 30px rgba(0,0,0,0.1)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <span style={{ fontSize: '12px', fontWeight: '800', opacity: 0.7, textTransform: 'uppercase' }}>Name:</span>
        <span style={{ fontSize: '16px', fontWeight: '600' }}>{profile.name}</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <span style={{ fontSize: '12px', fontWeight: '800', opacity: 0.7, textTransform: 'uppercase' }}>Email:</span>
        <span style={{ fontSize: '16px', fontWeight: '600' }}>{profile.email}</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <span style={{ fontSize: '12px', fontWeight: '800', opacity: 0.7, textTransform: 'uppercase' }}>Phone:</span>
        <span style={{ fontSize: '16px', fontWeight: '600' }}>{profile.mobile}</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <span style={{ fontSize: '12px', fontWeight: '800', opacity: 0.7, textTransform: 'uppercase' }}>Course:</span>
        <span style={{ fontSize: '16px', fontWeight: '600' }}>{profile.course}</span>
      </div>
    </motion.div>
  );
};
