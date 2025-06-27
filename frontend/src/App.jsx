import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import DXFDetailPage from './pages/DXFDetailPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/dxfs/:id" element={<DXFDetailPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
