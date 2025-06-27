// -----------------------------------------------------------------------------
// Entry Point (index.jsx or main.jsx)
//
// This file bootstraps the React application by rendering the root <App /> 
// component into the DOM. It uses React 18's createRoot API for improved 
// concurrent rendering.
//
// -----------------------------------------------------------------------------

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App'; // Main application component that handles routing

// Create a root to render the React app into the #root div in public/index.html
const root = ReactDOM.createRoot(document.getElementById('root'));

/**
 * Render the App component inside <React.StrictMode>.
 * React.StrictMode helps detect potential problems in development mode.
 * It doesn’t render anything visible to the user.
 */
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
