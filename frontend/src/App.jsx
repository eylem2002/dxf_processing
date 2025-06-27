// -----------------------------------------------------------------------------
// App.jsx
//
// Root component for the DXF Viewer application.
// Sets up the client-side routing using React Router.
// -----------------------------------------------------------------------------

import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

// Importing main pages of the application
import HomePage from './pages/HomePage';             // Upload and list DXFs
import DXFDetailPage from './pages/DXFDetailPage';   // View details of a selected DXF

/**
 * App Component
 *
 * Defines the top-level routing structure of the application.
 * Uses <BrowserRouter> to manage URL-based navigation.
 *
 * Routes:
 *  - "/" renders the HomePage (upload + DXF list)
 *  - "/dxfs/:id" renders DXFDetailPage (floor views for a specific DXF)
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Route to display the upload form and processed DXF list */}
        <Route path="/" element={<HomePage />} />

        {/* Route to display detailed view of selected DXF (based on ID param) */}
        <Route path="/dxfs/:id" element={<DXFDetailPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
