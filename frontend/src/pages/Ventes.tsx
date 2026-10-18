import { formatFcfa } from '../format';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import type { Page, Vente } from '../types';

const TAILLE_PAGE = 30;

export default function Ventes() {
  const [recherche, setRecherche] = useState('');
  const [rechercheEnvoyee, setRechercheEnvoyee] = useState('');
  const [jour, setJour] = useState('');
  const [page, setPage] = useState(1);
  const [donnees, setDonnees] = useState<Page<Vente> | null>(null);
  const [chargement, setChargement] = useState(false);
  const [erreur, setErreur] = useState('');

  // Attend 400 ms après la dernière frappe avant d'interroger l'API
  useEffect(() => {
    const minuteur = setTimeout(() => {
      setRechercheEnvoyee(recherche);
      setPage(1);
    }, 400);
    return () => clearTimeout(minuteur);
  }, [recherche]);

  useEffect(() => {
    let annule = false;
    setChargement(true);
    setErreur('');
    api
      .get<Page<Vente>>('/ventes/', {
        params: {
          q: rechercheEnvoyee || undefined,
          date: jour || undefined,
          page,
        },
      })
      .then((r) => { if (!annule) setDonnees(r.data); })
      .catch((e) => {
        if (annule) return;
        setErreur(
          e.response?.status === 403
            ? "Ce compte n'a pas accès aux ventes."
            : 'Impossible de charger les ventes.'
        );
      })
      .finally(() => { if (!annule) setChargement(false); });
    return () => { annule = true; };
  }, [rechercheEnvoyee, jour, page]);

  const nbPages = donnees ? Math.max(1, Math.ceil(donnees.count / TAILLE_PAGE)) : 1;

  return (
    <div style={{ maxWidth: 1000, margin: '24px auto', fontFamily: 'sans-serif' }}>
      <h2>Ventes</h2>

      <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
        <input
          placeholder="Rechercher par nom de client"
          value={recherche}
          onChange={(e) => setRecherche(e.target.value)}
          style={{ flex: 1, minWidth: 240, padding: 8 }}
        />
        <input
          type="date"
          value={jour}
          onChange={(e) => { setJour(e.target.value); setPage(1); }}
          style={{ padding: 8 }}
        />
        {jour && (
          <button onClick={() => { setJour(''); setPage(1); }}>Toutes les dates</button>
        )}
      </div>

      {erreur && <p style={{ color: 'crimson' }}>{erreur}</p>}
      {chargement && <p>Chargement...</p>}

      {donnees && (
        <>
          <table width="100%" cellPadding={8} style={{ borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '2px solid #ddd' }}>
                <th>Code</th>
                <th>Date</th>
                <th>Client</th>
                <th>Vendeur</th>
                <th style={{ textAlign: 'right' }}>Articles</th>
                <th style={{ textAlign: 'right' }}>Total</th>
              </tr>
            </thead>
            <tbody>
              {donnees.results.map((v) => (
                <tr key={v.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td><Link to={`/ventes/${v.id}`}>{v.code}</Link></td>
                  <td>{new Date(v.date_vente).toLocaleString('fr-FR')}</td>
                  <td>{v.client ?? 'Client anonyme'}</td>
                  <td>{v.vendeur ?? '—'}</td>
                  <td style={{ textAlign: 'right' }}>{v.nb_lignes}</td>
                  <td style={{ textAlign: 'right' }}>{formatFcfa(v.total)}</td>
                </tr>
              ))}
              {donnees.results.length === 0 && (
                <tr><td colSpan={6} style={{ textAlign: 'center', color: '#777' }}>Aucune vente</td></tr>
              )}
            </tbody>
          </table>

          <div style={{ display: 'flex', gap: 12, alignItems: 'center', justifyContent: 'center', marginTop: 16 }}>
            <button disabled={!donnees.previous} onClick={() => setPage((p) => p - 1)}>Précédent</button>
            <span>Page {page} / {nbPages}</span>
            <button disabled={!donnees.next} onClick={() => setPage((p) => p + 1)}>Suivant</button>
          </div>
        </>
      )}
    </div>
  );
}

