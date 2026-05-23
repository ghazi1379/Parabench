import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import {
  LayoutDashboard, Search, BarChart3, Settings, 
  TrendingUp, Package, Tag, Zap, Menu, X, ChevronRight,
  Activity, Globe
} from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import Products from './pages/Products';
import Benchmark from './pages/Benchmark';
import Admin from './pages/Admin';
import './App.css';

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/products', label: 'Produits', icon: Package },
  { path: '/benchmark', label: 'Benchmark Prix', icon: BarChart3 },
  { path: '/admin', label: 'Admin & Scraping', icon: Settings },
  { path: '/analytics', label: 'Market Intelligence', icon: Brain },
];

function Sidebar({ isOpen, setIsOpen }) {
  const location = useLocation();

  return (
    <>
      {isOpen && (
        <div className="sidebar-overlay" onClick={() => setIsOpen(false)} />
      )}
      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="logo">
            <div className="logo-icon">
              <Zap size={20} />
            </div>
            <div className="logo-text">
              <span className="logo-name">ParaBench</span>
              <span className="logo-sub">Tunisia · v1.0</span>
            </div>
          </div>
          <button className="sidebar-close" onClick={() => setIsOpen(false)}>
            <X size={16} />
          </button>
        </div>

        <div className="sidebar-section-label">Navigation</div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              end={path === '/'}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setIsOpen(false)}
            >
              <Icon size={18} />
              <span>{label}</span>
              <ChevronRight size={14} className="nav-arrow" />
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-section-label" style={{marginTop: 'auto'}}>Sites Suivis</div>
        <div className="sidebar-sites">
          {[
            { name: 'Parashop', color: '#6366f1', url: 'parashop.tn' },
            { name: 'Parafendri', color: '#22d3ee', url: 'parafendri.tn' },
            { name: 'TunisiePara', color: '#f59e0b', url: 'tunisiepara.com' },
          ].map(site => (
            <div key={site.name} className="site-badge">
              <div className="site-dot" style={{ background: site.color }} />
              <div>
                <div className="site-badge-name">{site.name}</div>
                <div className="site-badge-url">{site.url}</div>
              </div>
              <div className="site-status-dot" />
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          <Globe size={12} />
          <span>Marché Parapharmaceutique TN</span>
        </div>
      </aside>
    </>
  );
}

function TopBar({ setIsOpen }) {
  const location = useLocation();
  const currentPage = NAV_ITEMS.find(i => i.path === location.pathname || 
    (i.path !== '/' && location.pathname.startsWith(i.path)));
  
  return (
    <header className="topbar">
      <div className="topbar-left">
        <button className="menu-btn" onClick={() => setIsOpen(true)}>
          <Menu size={20} />
        </button>
        <div className="breadcrumb">
          <span className="breadcrumb-home">ParaBench</span>
          {currentPage && (
            <>
              <ChevronRight size={14} className="breadcrumb-sep" />
              <span className="breadcrumb-current">{currentPage.label}</span>
            </>
          )}
        </div>
      </div>
      <div className="topbar-right">
        <div className="topbar-badge">
          <Activity size={12} />
          <span>Live Data</span>
        </div>
      </div>
    </header>
  );
}

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <Router>
      <div className="app">
        <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
        <div className="main-layout">
          <TopBar setIsOpen={setSidebarOpen} />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/products" element={<Products />} />
              <Route path="/benchmark" element={<Benchmark />} />
              <Route path="/admin" element={<Admin />} />
              <Route path="/analytics" element={<Analytics />} />
            </Routes>
          </main>
        </div>
      </div>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1e293b',
            color: '#e2e8f0',
            border: '1px solid #334155',
            borderRadius: '12px',
            fontSize: '13px',
          },
        }}
      />
    </Router>
  );
}
