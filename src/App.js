import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import Navbar from './components/Navbar';
import {
  HomePage,
  DatabasePage,
  AnalysisPage,
  InstructionsPage,
  AnalyzingPage,
  SNPResultsPage,
  CRISPRDesignPage,
  BindingViewPage,
  EditResultsPage,
} from './pages';

/**
 * Root App component.
 * AppProvider must be inside BrowserRouter (set up in index.js)
 * so that useNavigate() works inside the context.
 */
export default function App() {
  return (
    <AppProvider>
      <div style={{ minHeight: '100vh' }}>
        <Navbar />
        <Routes>
          {/* Main pages (accessible from navbar) */}
          <Route path="/" element={<HomePage />} />
          <Route path="/database" element={<DatabasePage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
          <Route path="/instructions" element={<InstructionsPage />} />

          {/* Analysis pipeline routes */}
          <Route path="/analyzing" element={<AnalyzingPage />} />
          <Route path="/results/snps" element={<SNPResultsPage />} />
          <Route path="/results/crispr" element={<CRISPRDesignPage />} />
          <Route path="/results/binding" element={<BindingViewPage />} />
          <Route path="/results/edit" element={<EditResultsPage />} />

          {/* Fallback — redirect unknown routes to home */}
          <Route path="*" element={<HomePage />} />
        </Routes>
      </div>
    </AppProvider>
  );
}
