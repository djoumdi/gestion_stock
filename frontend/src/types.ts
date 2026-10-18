export interface Categorie {
  id: number;
  nom: string;
}

export interface Produit {
  id: number;
  reference: string;
  code_barres: string;
  nom: string;
  marque: string | null;
  categorie: Categorie | null;
  fournisseur: string | null;
  prix_vente: string;
  prix_achat?: string;
  marge?: string;
  taux_marge?: number | null;
  quantite_stock: number;
  seuil_alerte: number;
  en_alerte: boolean;
  image_url: string | null;
}

export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Vente {
  id: number;
  code: string;
  date_vente: string;
  client: string | null;
  vendeur: string | null;
  total: string;
  nb_lignes: number;
}

export interface VenteLigne {
  produit_id: number;
  produit: string;
  quantite: number;
  prix_unitaire: string;
  sous_total: string;
}

export interface VenteDetail extends Vente {
  lignes: VenteLigne[];
  facture: { numero: string; est_payee: boolean } | null;
}
