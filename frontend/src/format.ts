// Formatage des montants : "150000" -> "150 000 FCFA"
export function formatFcfa(valeur: string | number | null | undefined): string {
  if (valeur === null || valeur === undefined || valeur === '') return '—';
  return `${Math.round(Number(valeur)).toLocaleString('fr-FR')} FCFA`;
}
