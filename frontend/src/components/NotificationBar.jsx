import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const NotificationBar = ({ title, items, position }) => {
  return (
    <div className={`sidebar ${position}`}>
      <h3>{title}</h3>
      <div className="log-container">
        <AnimatePresence>
          {items.map((item) => (
            <motion.div
              key={item.id}
              initial={{ x: position === 'left' ? -50 : 50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="notification-card"
            >
              {item.text}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default NotificationBar;
