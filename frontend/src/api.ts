import axios from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';

const API_URL = 'http://127.0.0.1:8000/api';

export const api = axios.create({ baseURL: API_URL });

const CLE_ACCES = 'access_token';
const CLE_REFRESH = 'refresh_token';

export function enregistrerJetons(acces: string, refresh: string) {
  localStorage.setItem(CLE_ACCES, acces);
  localStorage.setItem(CLE_REFRESH, refresh);
}

export function effacerJetons() {
  localStorage.removeItem(CLE_ACCES);
  localStorage.removeItem(CLE_REFRESH);
}

export function estConnecte() {
  return !!localStorage.getItem(CLE_ACCES);
}

export async function connecter(username: string, password: string) {
  const { data } = await axios.post(`${API_URL}/auth/token/`, { username, password });
  enregistrerJetons(data.access, data.refresh);
}

// Ajoute le jeton à chaque requête
api.interceptors.request.use((config) => {
  const jeton = localStorage.getItem(CLE_ACCES);
  if (jeton) config.headers.Authorization = `Bearer ${jeton}`;
  return config;
});

let renouvellement: Promise<string> | null = null;

// Si le jeton a expiré (401), on le renouvelle une fois puis on rejoue la requête
api.interceptors.response.use(
  (reponse) => reponse,
  async (erreur) => {
    const requete = erreur.config as InternalAxiosRequestConfig & { _dejaRetente?: boolean };
    if (erreur.response?.status !== 401 || requete._dejaRetente) throw erreur;

    const refresh = localStorage.getItem(CLE_REFRESH);
    if (!refresh) {
      effacerJetons();
      window.location.href = '/login';
      throw erreur;
    }

    try {
      renouvellement ??= axios
        .post(`${API_URL}/auth/token/refresh/`, { refresh })
        .then((r) => {
          localStorage.setItem(CLE_ACCES, r.data.access);
          if (r.data.refresh) localStorage.setItem(CLE_REFRESH, r.data.refresh);
          return r.data.access as string;
        })
        .finally(() => { renouvellement = null; });

      const nouvelAcces = await renouvellement;
      requete._dejaRetente = true;
      requete.headers.Authorization = `Bearer ${nouvelAcces}`;
      return api(requete);
    } catch {
      effacerJetons();
      window.location.href = '/login';
      throw erreur;
    }
  }
);
