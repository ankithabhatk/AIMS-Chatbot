"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { useChat } from '../../context/ChatContext';

export const ImportantDates: React.FC = () => {
  const { profile } = useChat();
  const course = profile?.course || 'MBA';
  
  const dates = [
    { event: `Application Deadline (${course})`, date: "30 April 2026", type: "urgent" },
    { event: `${course} Entrance Exam Mock Test`, date: "05 May 2026", type: "info" },
    { event: "Interview Rounds Start", date: "15 May 2026", type: "info" },
    { event: "Commencement of Classes", date: "01 July 2026", type: "future" }
  ];

  return (
    <div className="important-dates-container" style={{ width: '100%', maxWidth: '600px', marginTop: '24px' }}>
      <h4 style={{ fontSize: '14px', fontWeight: '800', color: 'var(--text-muted)', marginBottom: '16px', textTransform: 'uppercase' }}>Upcoming Deadlines</h4>
      <div style={{ display: 'grid', gap: '12px' }}>
        {dates.map((item, index) => (
          <motion.div 
            key={index}
            whileHover={{ x: 5 }}
            style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center', 
              padding: '12px 16px', 
              backgroundColor: 'var(--card-bg)', 
              borderRadius: '10px',
              borderLeft: `4px solid ${item.type === 'urgent' ? '#EF4444' : 'var(--aims-accent)'}`,
              boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
            }}
          >
            <span style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-main)' }}>{item.event}</span>
            <span style={{ fontSize: '13px', fontWeight: '700', color: item.type === 'urgent' ? '#EF4444' : 'var(--aims-accent)' }}>{item.date}</span>
          </motion.div>
        ))}
      </div>
    </div>
  );
};
