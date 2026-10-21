/**
 * Lakeforge Web App - Main Entry Point
 * 
 * This is a React 18 application built with Vite
 * It provides a web interface for the Lakeforge data inspection tool
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Inspector from './pages/Inspector';
import QA from './pages/QA';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/inspect" element={<Inspector />} />
            <Route path="/qa" element={<QA />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
