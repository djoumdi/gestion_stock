import { formatFcfa } from '../format';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import type { Produit } from '../types';

interface ClientOption {
  id: number;
  nom: string;
}

interface LigneSaisie {
  produitId: number;
  quantite: number;
}

export default function NouvelleVente() {
  const navigate = useNavigate();
  const [produits, setProduits] = useState<Produit[]>([]);
  const [clients, setClients] = useState<ClientOption[]>([]);
  const [client, setClient] = useState('');
  const [lignes, setLignes] = useState<LigneSaisie[]>([]);
  const [choixProduit, setChoixProduit] = useState('');
  const [envoi, setEnvoi] = useState(false);
  const [erreur, setErreur] = useState('');

  // Charge les produits (pour le choix) et les clients (pour la liste déroulante)
  useEffect(() => {
    api.get<{ results: Produit[] }>('/produits/', { params: { page_size: 200 } })
      .then((r) => setProduits(r.data.results))
      .catch(() => setErreur('Impossible de charger les produits.'));
    api.get<ClientOption[]>('/clients/')
      .then((r) => setClients(r.data))
      .catch(() => setClients([]));
  }, []);

  const produitParId = new Map(produits.map((p) => [p.id, p]));

  // Total calculé pendant la saisie. Le serveur le recalcule de son côté.
  const total = lignes.reduce((somme, l) => {
    const produit = produitParId.get(l.produitId);
    return somme + (produit ? Number(produit.prix_vente) * l.quantite : 0);
  }, 0);

  function ajouterProduit() {
    const id = Number(choixProduit);
    if (!id || lignes.some((l) => l.produitId === id)) return;
    setLignes([...lignes, { produitId: id, quantite: 1 }]);
    setChoixProduit('');
  }

  function changerQuantite(produitId: number, quantite: number) {
    setLignes(lignes.map((l) =>
      l.produitId === produitId ? { ...l, quantite: Math.max(1, quantite) } : l
    ));
  }

  function retirer(produitId: number) {
    setLignes(lignes.filter((l) => l.produitId !== produitId));
  }

  async function valider() {
    setErreur('');
    if (lignes.length === 0) {
      setErreur('Ajoutez au moins un produit.');
      return;
    }
    setEnvoi(true);
    try {
      const reponse = await api.post('/ventes/', {
        client: client ? Number(client) : null,
        lignes: lignes.map((l) => ({ produit: l.produitId, quantite: l.quantite })),
      });
      navigate(`/ventes/${reponse.data.id}`, { replace: true });
    } catch (e: any) {
      // Le message vient du serveur : stock insuffisant, produit introuvable, etc.
      const detail = e.response?.data?.detail;
      setErreur(detail ?? "La vente n'a pas pu être enregistrée.");
    } finally {
      setEnvoi(false);
    }
  }

  const produitsDisponibles = produits.filter((p) => !lignes.some((l) => l.produitId === p.id));

  return (
    <div style={{ maxWidth: 800, margin: '24px auto', fontFamily: 'sans-serif' }}>
      <h2>Nouvelle vente</h2>

      <div style={{ marginBottom: 16 }}>
        <label>
          <b>Client</b>{' '}
          <select value={client} onChange={(e) => setClient(e.target.value)} style={{ padding: 6 }}>
            <option value="">Client anonyme</option>
            {clients.map((c) => (
              <option key={c.id} value={c.id}>{c.nom}</option>
            ))}
          </select>
        </label>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <select value={choixProduit} onChange={(e) => setChoixProduit(e.target.value)} style={{ flex: 1, padding: 6 }}>
          <option value="">Choisir un produit...</option>
          {produitsDisponibles.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nom} — {formatFcfa(p.prix_vente)} (stock : {p.quantite_stock})
            </option>
          ))}
        </select>
        <button onClick={ajouterProduit} disabled={!choixProduit}>Ajouter</button>
      </div>

      <table width="100%" cellPadding={8} style={{ borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ textAlign: 'left', borderBottom: '2px solid #ddd' }}>
            <th>Produit</th>
            <th style={{ textAlign: 'right' }}>Prix</th>
            <th style={{ textAlign: 'right' }}>Quantité</th>
            <th style={{ textAlign: 'right' }}>Sous-total</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {lignes.map((l) => {
            const produit = produitParId.get(l.produitId);
            if (!produit) return null;
            return (
              <tr key={l.produitId} style={{ borderBottom: '1px solid #eee' }}>
                <td>{produit.nom}</td>
                <td style={{ textAlign: 'right' }}>{formatFcfa(produit.prix_vente)}</td>
                <td style={{ textAlign: 'right' }}>
                  <input
                    type="number"
                    min={1}
                    value={l.quantite}
                    onChange={(e) => changerQuantite(l.produitId, Number(e.target.value))}
                    style={{ width: 70, padding: 4 }}
                  />
                </td>
                <td style={{ textAlign: 'right' }}>
                  {formatFcfa(Number(produit.prix_vente) * l.quantite)}
                </td>
                <td><button onClick={() => retirer(l.produitId)}>Retirer</button></td>
              </tr>
            );
          })}
          {lignes.length === 0 && (
            <tr><td colSpan={5} style={{ textAlign: 'center', color: '#777' }}>Aucun produit ajouté</td></tr>
          )}
        </tbody>
        <tfoot>
          <tr>
            <td colSpan={3} style={{ textAlign: 'right', fontWeight: 700 }}>Total</td>
            <td style={{ textAlign: 'right', fontWeight: 700 }}>{formatFcfa(total)}</td>
            <td></td>
          </tr>
        </tfoot>
      </table>

      {erreur && <p style={{ color: 'crimson', marginTop: 16 }}>{erreur}</p>}

      <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
        <button onClick={valider} disabled={envoi || lignes.length === 0}>
          {envoi ? 'Enregistrement...' : 'Enregistrer la vente'}
        </button>
        <button onClick={() => navigate('/ventes')}>Annuler</button>
      </div>
    </div>
  );
}

