import type { ReactNode } from 'react';
import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router-dom';
import Login from './pages/Login';
import Produits from './pages/Produits';
import FicheProduit from './pages/FicheProduit';
import Ventes from './pages/Ventes';
import FicheVente from './pages/FicheVente';
import NouvelleVente from './pages/NouvelleVente';
import { estConnecte } from './api';

// Page protégée : redirige vers la connexion sans jeton, sinon affiche la barre de navigation
function Securisee({ children }: { children: ReactNode }) {
  if (!estConnecte()) return <Navigate to="/login" replace />;
  return (
    <div>
      <nav style={{ display: 'flex', gap: 16, padding: '12px 24px', background: '#f3f4f6', fontFamily: 'sans-serif' }}>
        <Link to="/">Produits</Link>
        <Link to="/ventes">Ventes</Link>
        <Link to="/ventes/nouvelle">Nouvelle vente</Link>
      </nav>
      {children}
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Securisee><Produits /></Securisee>} />
        <Route path="/produits/:id" element={<Securisee><FicheProduit /></Securisee>} />
        <Route path="/ventes" element={<Securisee><Ventes /></Securisee>} />
        <Route path="/ventes/nouvelle" element={<Securisee><NouvelleVente /></Securisee>} />
        <Route path="/ventes/:id" element={<Securisee><FicheVente /></Securisee>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
