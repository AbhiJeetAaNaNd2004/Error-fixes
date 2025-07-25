import React from 'react';
import Header from './Header';
import Navigation from './Navigation';

const Layout = ({ children, title, subtitle }) => {
  return (
    <div className="bg-gray-50 text-gray-900 min-h-screen">
      <Header title={title} subtitle={subtitle} />
      <div className="flex">
        <Navigation />
        <main className="flex-1 p-6 bg-gray-50">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;