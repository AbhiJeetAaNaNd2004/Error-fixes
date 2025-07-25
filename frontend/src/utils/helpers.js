export const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleString();
};

export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString();
};

export const formatTime = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleTimeString();
};

export const getStatusColor = (status) => {
  switch (status?.toLowerCase()) {
    case 'checked_in':
    case 'active':
    case 'running':
      return 'text-green-400';
    case 'checked_out':
    case 'inactive':
    case 'stopped':
      return 'text-red-400';
    default:
      return 'text-gray-400';
  }
};

export const getStatusText = (status) => {
  switch (status?.toLowerCase()) {
    case 'checked_in':
      return 'Checked In';
    case 'checked_out':
      return 'Checked Out';
    case 'running':
      return 'Running';
    case 'stopped':
      return 'Stopped';
    default:
      return status || 'Unknown';
  }
};

export const handleApiError = (error, defaultMessage = 'An error occurred') => {
  console.error('API Error:', error);
  return error.message || defaultMessage;
};

export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

export const truncateText = (text, maxLength = 50) => {
  if (!text) return '';
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
};