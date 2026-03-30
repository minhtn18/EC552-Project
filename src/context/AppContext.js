import React, { createContext, useContext, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { MOCK_DB_SEQUENCES } from '../data/mockData';

const AppContext = createContext(null);

/**
 * Custom hook to access the global app context.
 */
export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}

/**
 * Provider that wraps the entire app, supplying shared state and navigation.
 */
export function AppProvider({ children }) {
  const routerNavigate = useNavigate();

  // ── Sequence input state ──
  const [inputSequence, setInputSequence] = useState(null);
  const [inputMeta, setInputMeta] = useState(null);

  // ── Analysis results ──
  const [snpResults, setSnpResults] = useState(null);
  const [selectedSNP, setSelectedSNP] = useState(null);
  const [grnaCacheMap, setGrnaCacheMap] = useState(new Map());
  const [selectedGRNA, setSelectedGRNA] = useState(null);
  const [bindingSiteData, setBindingSiteData] = useState(null);

  // ── Database sequences ──
  const [dbSequences, setDbSequences] = useState(MOCK_DB_SEQUENCES);

  /**
   * Navigate to a route path.
   */
  const navigate = useCallback(
    (path) => {
      routerNavigate(path);
    },
    [routerNavigate]
  );

  /**
   * Reset all analysis state (for starting fresh).
   */
  const resetAnalysis = useCallback(() => {
    setInputSequence(null);
    setInputMeta(null);
    setSnpResults(null);
    setSelectedSNP(null);
    setGrnaCacheMap(new Map());
    setSelectedGRNA(null);
    setBindingSiteData(null);
  }, []);

  const value = {
    navigate,
    resetAnalysis,
    inputSequence, setInputSequence,
    inputMeta, setInputMeta,
    snpResults, setSnpResults,
    selectedSNP, setSelectedSNP,
    grnaCacheMap, setGrnaCacheMap,
    selectedGRNA, setSelectedGRNA,
    bindingSiteData, setBindingSiteData,
    dbSequences, setDbSequences,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
