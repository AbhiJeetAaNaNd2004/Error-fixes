import React from 'react';

const Button = ({ 
  children, 
  onClick, 
  disabled = false, 
  variant = 'primary', 
  size = 'md',
  fullWidth = false,
  type = 'button',
  className = ''
}) => {
  const baseClasses = "font-semibold rounded-lg shadow-light focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-50";
  
  const variants = {
    primary: "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 disabled:bg-blue-300 shadow-light-md hover:shadow-light-lg",
    secondary: "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-400",
    danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 disabled:bg-red-300 shadow-light-md hover:shadow-light-lg",
    success: "bg-green-600 text-white hover:bg-green-700 focus:ring-green-500 disabled:bg-green-300 shadow-light-md hover:shadow-light-lg",
    outline: "border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-blue-500 disabled:text-gray-400 disabled:border-gray-200",
    ghost: "text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:ring-blue-500 disabled:text-gray-400",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };

  const classes = `
    ${baseClasses}
    ${variants[variant]}
    ${sizes[size]}
    ${fullWidth ? 'w-full' : ''}
    ${className}
  `.trim();

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={classes}
    >
      {children}
    </button>
  );
};

export default Button;