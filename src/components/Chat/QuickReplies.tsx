"use client";

import React from 'react';
import { motion } from 'framer-motion';

interface QuickRepliesProps {
  onSelect: (query: string) => void;
  suggestions?: string[];
}

export const QuickReplies: React.FC<QuickRepliesProps> = ({ onSelect, suggestions: propSuggestions }) => {
  const defaultSuggestions = [
    "Courses offered?",
    "Admission process",
    "Fees structure",
    "Campus facilities",
    "Scholarship info",
    "Important dates",
    "Contact admissions"
  ];
  
  const suggestions = propSuggestions && propSuggestions.length > 0 ? propSuggestions : defaultSuggestions;

  return (
    <motion.div 
      className="quick-replies-container"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
    >
      {suggestions.map((sug, index) => (
        <motion.button
          key={index}
          className="quick-reply-chip"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => onSelect(sug)}
        >
          {sug}
        </motion.button>
      ))}
    </motion.div>
  );
};
