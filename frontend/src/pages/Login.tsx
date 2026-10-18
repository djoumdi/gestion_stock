import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { connecter } from '../api';

export default function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [erreur, setErreur] = useState('');
  const [envoi, setEnvoi] = useState(false);

  async function soumettre(e: FormEvent) {
    e.preventDefault();
    setErreur('');
    setEnvoi(true);
    try {
      await connecter(username, password);
      navigate('/', { replace: true });
    } catch {
      setErreur("Nom d'utilisateur ou mot de passe incorrect.");
    } finally {
      setEnvoi(false);
    }
  }

  return (
    <div style={{ maxWidth: 360, margin: '80px auto', fontFamily: 'sans-serif' }}>
      <h2>Connexion</h2>
      <form onSubmit={soumettre} style={{ display: 'grid', gap: 12 }}>
        <input placeholder="Nom d'utilisateur" value={username}
               onChange={(e) => setUsername(e.target.value)} required />
        <input type="password" placeholder="Mot de passe" value={password}
               onChange={(e) => setPassword(e.target.value)} required />
        <button type="submit" disabled={envoi}>
          {envoi ? 'Connexion...' : 'Se connecter'}
        </button>
        {erreur && <p style={{ color: 'crimson' }}>{erreur}</p>}
      </form>
    </div>
  );
}
