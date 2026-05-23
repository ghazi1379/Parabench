export const SITE_COLORS = {
  parashop: '#6366f1',
  parafendri: '#22d3ee',
  tunisiepara: '#f59e0b',
};

export const SITE_LABELS = {
  parashop: 'Parashop',
  parafendri: 'Parafendri',
  tunisiepara: 'TunisiePara',
};

export const SITE_URLS = {
  parashop: 'https://www.parashop.tn',
  parafendri: 'https://parafendri.tn',
  tunisiepara: 'https://www.tunisiepara.com',
};

export const formatPrice = (price) => {
  if (price === null || price === undefined) return 'N/D';
  return `${Number(price).toFixed(3)} TND`;
};

export const formatDate = (dateStr) => {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('fr-TN', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
  });
};

export const formatNumber = (n) => {
  if (n === null || n === undefined) return '0';
  return Number(n).toLocaleString('fr-TN');
};

export const getSiteColor = (site) => SITE_COLORS[site] || '#94a3b8';
export const getSiteLabel = (site) => SITE_LABELS[site] || site;
