import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';
import ScanPage from './pages/ScanPage';
import InventoryPage from './pages/InventoryPage';

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/inventory" replace />} />
          <Route path="/scan" element={<ScanPage />} />
          <Route path="/inventory" element={<InventoryPage />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
