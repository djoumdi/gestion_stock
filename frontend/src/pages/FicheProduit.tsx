import { formatFcfa } from '../format';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api';
import type { Produit } from '../types';

export default function FicheProduit() {
  const { id } = useParams();
  const [produit, setProduit] = useState<Produit | null>(null);
  const [erreur, setErreur] = useState('');

  useEffect(() => {
    api.get<Produit>(`/produits/${id}/`)
      .then((r) => setProduit(r.data))
      .catch(() => setErreur('Produit introuvable.'));
  }, [id]);

  if (erreur) {
    return (
      <div style={{ maxWidth: 700, margin: '24px auto', fontFamily: 'sans-serif' }}>
        <p style={{ color: 'crimson' }}>{erreur}</p>
        <Link to="/">← Retour à la liste</Link>
      </div>
    );
  }
  if (!produit) return <p>Chargement...</p>;

  return (
    <div style={{ maxWidth: 700, margin: '24px auto', fontFamily: 'sans-serif' }}>
      <Link to="/">← Retour à la liste</Link>
      <h2>{produit.nom}</h2>
      {produit.image_url && (
        <img src={produit.image_url} alt={produit.nom} style={{ maxWidth: 240, borderRadius: 8 }} />
      )}
      <table cellPadding={8} style={{ borderCollapse: 'collapse', marginTop: 16 }}>
        <tbody>
          <tr><td><b>Référence</b></td><td>{produit.reference}</td></tr>
          <tr><td><b>Code-barres</b></td><td>{produit.code_barres || '—'}</td></tr>
          <tr><td><b>Marque</b></td><td>{produit.marque ?? '—'}</td></tr>
          <tr><td><b>Catégorie</b></td><td>{produit.categorie?.nom ?? '—'}</td></tr>
          <tr><td><b>Fournisseur</b></td><td>{produit.fournisseur ?? '—'}</td></tr>
          <tr><td><b>Prix de vente</b></td><td>{formatFcfa(produit.prix_vente)}</td></tr>
          {produit.prix_achat !== undefined && (
            <tr><td><b>Prix d'achat</b></td><td>{formatFcfa(produit.prix_achat)}</td></tr>
          )}
          {produit.marge !== undefined && (
            <tr><td><b>Marge</b></td><td>{formatFcfa(produit.marge)} ({produit.taux_marge ?? '—'} %)</td></tr>
          )}
          <tr>
            <td><b>Stock</b></td>
            <td style={{ color: produit.en_alerte ? 'crimson' : undefined, fontWeight: produit.en_alerte ? 700 : 400 }}>
              {produit.quantite_stock}{produit.en_alerte ? ' ⚠ stock faible' : ''}
            </td>
          </tr>
          <tr><td><b>Seuil d'alerte</b></td><td>{produit.seuil_alerte}</td></tr>
        </tbody>
      </table>
    </div>
  );
}

