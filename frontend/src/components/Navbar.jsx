/**
 * Navbar component - Navigation and branding
 */

import React from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <Link to="/">
            <span className="logo">🚀 Lakeforge</span>
          </Link>
        </div>
        <ul className="navbar-menu">
          <li>
            <Link to="/">Dashboard</Link>
          </li>
          <li>
            <Link to="/inspect">Inspector</Link>
          </li>
          <li>
            <Link to="/qa">Q&A</Link>
          </li>
          <li>
            <Link to="/reports">Reports</Link>
          </li>
          <li>
            <Link to="/settings">Settings</Link>
          </li>
        </ul>
      </div>
    </nav>
  );
}

export default Navbar;
