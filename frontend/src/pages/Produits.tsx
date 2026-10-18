import { formatFcfa } from '../format';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, effacerJetons } from '../api';
import type { Categorie, Page, Produit } from '../types';

const TAILLE_PAGE = 30;

export default function Produits() {
  const navigate = useNavigate();
  const [recherche, setRecherche] = useState('');
  const [rechercheEnvoyee, setRechercheEnvoyee] = useState('');
  const [alerte, setAlerte] = useState(false);
  const [categorie, setCategorie] = useState('');
  const [categories, setCategories] = useState<Categorie[]>([]);
  const [page, setPage] = useState(1);
  const [donnees, setDonnees] = useState<Page<Produit> | null>(null);
  const [chargement, setChargement] = useState(false);
  const [erreur, setErreur] = useState('');

  // Charge les catégories une seule fois, au premier affichage
  useEffect(() => {
    api.get<Categorie[]>('/categories/')
      .then((r) => setCategories(r.data))
      .catch(() => setCategories([]));
  }, []);

  // Attend 400 ms après la dernière frappe avant d'interroger l'API
  useEffect(() => {
    const minuteur = setTimeout(() => {
      setRechercheEnvoyee(recherche);
      setPage(1);
    }, 400);
    return () => clearTimeout(minuteur);
  }, [recherche]);

  // Recharge la liste à chaque changement de filtre ou de page
  useEffect(() => {
    let annule = false;
    setChargement(true);
    setErreur('');
    api
      .get<Page<Produit>>('/produits/', {
        params: {
          q: rechercheEnvoyee || undefined,
          alerte: alerte ? 1 : undefined,
          categorie: categorie || undefined,
          page,
        },
      })
      .then((r) => { if (!annule) setDonnees(r.data); })
      .catch((e) => {
        if (annule) return;
        setErreur(
          e.response?.status === 403
            ? "Ce compte n'a pas accès aux produits."
            : 'Impossible de charger les produits.'
        );
      })
      .finally(() => { if (!annule) setChargement(false); });
    return () => { annule = true; };
  }, [rechercheEnvoyee, alerte, categorie, page]);

  function deconnecter() {
    effacerJetons();
    navigate('/login', { replace: true });
  }

  const nbPages = donnees ? Math.max(1, Math.ceil(donnees.count / TAILLE_PAGE)) : 1;

  return (
    <div style={{ maxWidth: 1000, margin: '24px auto', fontFamily: 'sans-serif' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Produits</h2>
        <button onClick={deconnecter}>Déconnexion</button>
      </header>

      <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
        <input
          placeholder="Rechercher un nom, une référence ou un code-barres"
          value={recherche}
          onChange={(e) => setRecherche(e.target.value)}
          style={{ flex: 1, minWidth: 240, padding: 8 }}
        />
        <select value={categorie} onChange={(e) => { setCategorie(e.target.value); setPage(1); }} style={{ padding: 8 }}>
          <option value="">Toutes les catégories</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>{c.nom}</option>
          ))}
        </select>
        <label>
          <input
            type="checkbox"
            checked={alerte}
            onChange={(e) => { setAlerte(e.target.checked); setPage(1); }}
          />{' '}
          Stock faible uniquement
        </label>
      </div>

      {erreur && <p style={{ color: 'crimson' }}>{erreur}</p>}
      {chargement && <p>Chargement...</p>}

      {donnees && (
        <>
          <table width="100%" cellPadding={8} style={{ borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '2px solid #ddd' }}>
                <th>Réf.</th>
                <th>Nom</th>
                <th>Marque</th>
                <th>Catégorie</th>
                <th style={{ textAlign: 'right' }}>Stock</th>
                <th style={{ textAlign: 'right' }}>Prix de vente</th>
                <th style={{ textAlign: 'right' }}>Prix d'achat</th>
              </tr>
            </thead>
            <tbody>
              {donnees.results.map((p) => (
                <tr key={p.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td>{p.reference}</td>
                  <td><Link to={`/produits/${p.id}`}>{p.nom}</Link></td>
                  <td>{p.marque ?? '—'}</td>
                  <td>{p.categorie?.nom ?? '—'}</td>
                  <td style={{ textAlign: 'right', color: p.en_alerte ? 'crimson' : undefined, fontWeight: p.en_alerte ? 700 : 400 }}>
                    {p.quantite_stock}{p.en_alerte ? ' ⚠' : ''}
                  </td>
                  <td style={{ textAlign: 'right' }}>{formatFcfa(p.prix_vente)}</td>
                  <td style={{ textAlign: 'right' }}>
                    {p.prix_achat !== undefined ? `${formatFcfa(p.prix_achat)}` : '—'}
                  </td>
                </tr>
              ))}
              {donnees.results.length === 0 && (
                <tr><td colSpan={7} style={{ textAlign: 'center', color: '#777' }}>Aucun produit</td></tr>
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

