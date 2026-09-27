import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, Link } from 'react-router-dom';
import {
  ShieldCheck,
  Activity,
  MessageSquare,
  Pill,
  BarChart3,
  Menu,
  X,
  HeartPulse,
} from 'lucide-react';

import Dashboard from './pages/Dashboard';
import SentimentAnalyzer from './pages/SentimentAnalyzer';
import DrugExplorer from './pages/DrugExplorer';
import DrugDetails from './pages/DrugDetails';
import Conditions from './pages/Conditions';
import ModelMetrics from './pages/ModelMetrics';

export default function App() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { to: '/', label: 'Recommendation Dashboard', icon: HeartPulse, end: true },
    { to: '/sentiment', label: 'Sentiment Analyzer', icon: MessageSquare },
    { to: '/drugs', label: 'Medication Catalog', icon: Pill },
    { to: '/conditions', label: 'Conditions', icon: Activity },
    { to: '/metrics', label: 'Model Metrics', icon: BarChart3 },
  ];

  return (
    <Router>
      <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
        {/* Navigation Header */}
        <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              {/* Logo / Brand */}
              <div className="flex items-center">
                <Link to="/" className="flex items-center gap-2.5 group">
                  <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-200 group-hover:bg-indigo-700 transition-colors">
                    <ShieldCheck className="w-6 h-6" />
                  </div>
                  <div>
                    <h1 className="text-sm font-bold tracking-tight text-slate-900 group-hover:text-indigo-600 transition-colors">
                      Explainable Drug Recommender
                    </h1>
                    <p className="text-[10px] text-slate-500 font-medium">
                      Safety-Aware Decision Support System
                    </p>
                  </div>
                </Link>
              </div>

              {/* Desktop Navigation Links */}
              <nav className="hidden md:flex items-center space-x-1">
                {navLinks.map((link) => {
                  const Icon = link.icon;
                  return (
                    <NavLink
                      key={link.to}
                      to={link.to}
                      end={link.end}
                      className={({ isActive }) =>
                        `inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                          isActive
                            ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                        }`
                      }
                    >
                      <Icon className="w-4 h-4 opacity-75" />
                      <span>{link.label}</span>
                    </NavLink>
                  );
                })}
              </nav>

              {/* Mobile Menu Toggle Button */}
              <div className="flex items-center md:hidden">
                <button
                  type="button"
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className="p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 focus:outline-none"
                >
                  {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                </button>
              </div>
            </div>
          </div>

          {/* Mobile Dropdown Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-2 pb-3 space-y-1 shadow-lg">
              {navLinks.map((link) => {
                const Icon = link.icon;
                return (
                  <NavLink
                    key={link.to}
                    to={link.to}
                    end={link.end}
                    onClick={() => setMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-2 px-3 py-2.5 rounded-lg text-xs font-semibold ${
                        isActive
                          ? 'bg-indigo-50 text-indigo-700 font-bold'
                          : 'text-slate-700 hover:bg-slate-100'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4" />
                    <span>{link.label}</span>
                  </NavLink>
                );
              })}
            </div>
          )}
        </header>

        {/* Main Content Area */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/sentiment" element={<SentimentAnalyzer />} />
            <Route path="/drugs" element={<DrugExplorer />} />
            <Route path="/drugs/:drugId" element={<DrugDetails />} />
            <Route path="/conditions" element={<Conditions />} />
            <Route path="/metrics" element={<ModelMetrics />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="bg-white border-t border-slate-200 py-6 text-xs text-slate-500">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-center sm:text-left">
              © 2026 Explainable Personalized Drug Recommendation and Safety Screening System. Academic B.Tech Capstone Prototype.
            </p>
            <p className="text-center sm:text-right font-medium text-slate-400">
              Deterministic Safety Screening • Decoupled Recommendation Engine
            </p>
          </div>
        </footer>
      </div>
    </Router>
  );
}
