import { formatFcfa } from '../format';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api';
import type { VenteDetail } from '../types';

export default function FicheVente() {
  const { id } = useParams();
  const [vente, setVente] = useState<VenteDetail | null>(null);
  const [erreur, setErreur] = useState('');

  useEffect(() => {
    api.get<VenteDetail>(`/ventes/${id}/`)
      .then((r) => setVente(r.data))
      .catch(() => setErreur('Vente introuvable.'));
  }, [id]);

  if (erreur) {
    return (
      <div style={{ maxWidth: 800, margin: '24px auto', fontFamily: 'sans-serif' }}>
        <p style={{ color: 'crimson' }}>{erreur}</p>
        <Link to="/ventes">← Retour aux ventes</Link>
      </div>
    );
  }
  if (!vente) return <p>Chargement...</p>;

  return (
    <div style={{ maxWidth: 800, margin: '24px auto', fontFamily: 'sans-serif' }}>
      <Link to="/ventes">← Retour aux ventes</Link>
      <h2>Vente {vente.code}</h2>

      <p>
        <b>Date :</b> {new Date(vente.date_vente).toLocaleString('fr-FR')}<br />
        <b>Client :</b> {vente.client ?? 'Client anonyme'}<br />
        <b>Vendeur :</b> {vente.vendeur ?? '—'}<br />
        <b>Facture :</b>{' '}
        {vente.facture
          ? `${vente.facture.numero} — ${vente.facture.est_payee ? 'payée' : 'non payée'}`
          : '—'}
      </p>

      <table width="100%" cellPadding={8} style={{ borderCollapse: 'collapse', marginTop: 16 }}>
        <thead>
          <tr style={{ textAlign: 'left', borderBottom: '2px solid #ddd' }}>
            <th>Produit</th>
            <th style={{ textAlign: 'right' }}>Quantité</th>
            <th style={{ textAlign: 'right' }}>Prix unitaire</th>
            <th style={{ textAlign: 'right' }}>Sous-total</th>
          </tr>
        </thead>
        <tbody>
          {vente.lignes.map((l) => (
            <tr key={l.produit_id} style={{ borderBottom: '1px solid #eee' }}>
              <td>{l.produit}</td>
              <td style={{ textAlign: 'right' }}>{l.quantite}</td>
              <td style={{ textAlign: 'right' }}>{formatFcfa(l.prix_unitaire)}</td>
              <td style={{ textAlign: 'right' }}>{formatFcfa(l.sous_total)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td colSpan={3} style={{ textAlign: 'right', fontWeight: 700 }}>Total</td>
            <td style={{ textAlign: 'right', fontWeight: 700 }}>{formatFcfa(vente.total)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

