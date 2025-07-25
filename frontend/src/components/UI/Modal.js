import React from 'react';
import Button from './Button';

const Modal = ({ isOpen, onClose, title, children, footer }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-900 bg-opacity-50 transition-opacity backdrop-blur-sm" onClick={onClose}></div>
        
        <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-light-lg transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full border border-gray-200">
          {title && (
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
              <h3 className="text-lg font-semibold text-heading">{title}</h3>
            </div>
          )}
          
          <div className="px-6 py-4">
            {children}
          </div>
          
          {footer && (
            <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end space-x-3">
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Modal;