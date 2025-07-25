import React from 'react';

const Card = ({ children, title, className = '' }) => {
  return (
    <div className={`bg-white rounded-xl shadow-light-md border border-gray-200 overflow-hidden ${className}`}>
      {title && (
        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
          <h3 className="text-lg font-semibold text-heading">{title}</h3>
        </div>
      )}
      <div className="p-6">
        {children}
      </div>
    </div>
  );
};

export default Card;