import React, { useState, useEffect, useCallback } from 'react';
import { Search, Download, RefreshCw, ExternalLink, BarChart3, TrendingDown } from 'lucide-react';
import { getBenchmark, refreshBenchmark, exportBenchmarkExcel } from '../utils/api';
import { formatPrice, formatNumber, getSiteLabel } from '../utils/helpers';
import toast from 'react-hot-toast';

const PriceCell = ({ price, isMin, isMax, url }) => {
  if (!price) return <span className="benchmark-na">N/D</span>;
  const cls = isMin ? 'benchmark-cheapest' : isMax ? 'benchmark-expensive' : '';
  return (
    <div className="benchmark-cell">
      <span className={`benchmark-price ${cls}`}>{formatPrice(price)}</span>
      {isMin && <span style={{ fontSize: '10px', color: '#10b981' }}>▼ Moins cher</span>}
      {isMax && <span style={{ fontSize: '10px', color: '#f43f5e' }}>▲ Plus cher</span>}
      {url && (
        <a href={url} target="_blank" rel="noreferrer" style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '3px' }}>
          Voir <ExternalLink size={9} />
        </a>
      )}
    </div>
  );
};

const DiffBadge = ({ diff }) => {
  if (!diff) return '—';
  const cls = diff > 30 ? 'diff-high' : diff > 10 ? 'diff-mid' : 'diff-low';
  return <span className={`diff-badge ${cls}`}>{diff.toFixed(1)}%</span>;
};

export default function Benchmark() {
  const [data, setData] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const [brand, setBrand] = useState('');
  const [minDiff, setMinDiff] = useState('');

  const load = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const params = { page: p, limit: 25 };
      if (search) params.search = search;
      if (brand) params.brand = brand;
      if (minDiff) params.min_diff = minDiff;
      const res = await getBenchmark(params);
      setData(res.data.data);
      setTotal(res.data.total);
      setPages(res.data.pages);
      setPage(p);
    } catch {
      toast.error('Erreur de chargement');
    } finally {
      setLoading(false);
    }
  }, [search, brand, minDiff]);

  useEffect(() => { load(1); }, [search, brand, minDiff]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshBenchmark();
      toast.success('Benchmark en cours de mise à jour...');
      setTimeout(() => load(1), 2000);
    } catch {
      toast.error('Erreur lors de la mise à jour');
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Comparateur de Prix</h1>
          <p className="page-subtitle">Benchmark multi-sites — {formatNumber(total)} produits comparés</p>
        </div>
        <div className="page-actions">
          <button className="btn btn-secondary btn-sm" onClick={() => { exportBenchmarkExcel(); toast.success('Export en cours...'); }}>
            <Download size={14} /> Excel
          </button>
          <button className="btn btn-primary btn-sm" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw size={14} className={refreshing ? 'spinning' : ''} />
            {refreshing ? 'Mise à jour...' : 'Mettre à jour Benchmark'}
          </button>
        </div>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {[
          { label: 'Parashop', color: '#6366f1' },
          { label: 'Parafendri', color: '#22d3ee' },
          { label: 'TunisiePara', color: '#f59e0b' },
        ].map(s => (
          <div key={s.label} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: s.color }} />
            {s.label}
          </div>
        ))}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#10b981', marginLeft: '8px' }}>
          ▼ Prix le plus bas
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#f43f5e' }}>
          ▲ Prix le plus haut
        </div>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
          <div className="search-wrapper">
            <Search size={14} className="search-icon" />
            <input className="input search-input" placeholder="Rechercher un produit..."
              value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <input className="input" placeholder="Filtrer par marque..."
            value={brand} onChange={e => setBrand(e.target.value)} />
          <select className="select" value={minDiff} onChange={e => setMinDiff(e.target.value)}>
            <option value="">Toutes les différences</option>
            <option value="5">Différence &gt; 5%</option>
            <option value="10">Différence &gt; 10%</option>
            <option value="20">Différence &gt; 20%</option>
            <option value="30">Différence &gt; 30%</option>
          </select>
        </div>
      </div>

      {/* Benchmark Table */}
      <div className="card">
        {loading ? (
          <div className="loading-wrapper">
            <div className="spinner" />
            <span>Chargement du benchmark...</span>
          </div>
        ) : data.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon"><BarChart3 size={40} opacity={0.3} /></div>
            <p style={{ fontWeight: 600 }}>Aucun produit comparé disponible</p>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Le benchmark se génère automatiquement après le scraping de 2+ sites
            </p>
          </div>
        ) : (
          <>
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th style={{ minWidth: '220px' }}>Produit</th>
                    <th>Marque</th>
                    <th style={{ color: '#818cf8' }}>Parashop</th>
                    <th style={{ color: '#22d3ee' }}>Parafendri</th>
                    <th style={{ color: '#f59e0b' }}>TunisiePara</th>
                    <th>Diff. Prix</th>
                    <th>Économie Max</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map(item => {
                    const prices = {
                      parashop: item.price_parashop,
                      parafendri: item.price_parafendri,
                      tunisiepara: item.price_tunisiepara,
                    };
                    const validPrices = Object.values(prices).filter(p => p !== null && p !== undefined);
                    const min = validPrices.length ? Math.min(...validPrices) : null;
                    const max = validPrices.length ? Math.max(...validPrices) : null;
                    const economy = min && max ? max - min : null;

                    return (
                      <tr key={item.id}>
                        <td>
                          <div style={{ fontWeight: 500, fontSize: '12px', maxWidth: '220px',
                                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                               title={item.product_name_normalized}>
                            {item.product_name_normalized}
                          </div>
                        </td>
                        <td>
                          <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{item.brand || '—'}</span>
                        </td>
                        <td>
                          <PriceCell price={item.price_parashop} isMin={item.price_parashop === min}
                            isMax={item.price_parashop === max && min !== max} url={item.url_parashop} />
                        </td>
                        <td>
                          <PriceCell price={item.price_parafendri} isMin={item.price_parafendri === min}
                            isMax={item.price_parafendri === max && min !== max} url={item.url_parafendri} />
                        </td>
                        <td>
                          <PriceCell price={item.price_tunisiepara} isMin={item.price_tunisiepara === min}
                            isMax={item.price_tunisiepara === max && min !== max} url={item.url_tunisiepara} />
                        </td>
                        <td>
                          <DiffBadge diff={item.price_diff_percent} />
                        </td>
                        <td>
                          {economy ? (
                            <span style={{ fontWeight: 700, color: '#10b981', fontSize: '13px' }}>
                              {formatPrice(economy)}
                            </span>
                          ) : '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="pagination">
              <div className="pagination-info">Page {page} / {pages} — {formatNumber(total)} comparaisons</div>
              <div className="pagination-btns">
                <button className="page-btn" onClick={() => load(page - 1)} disabled={page === 1}>‹</button>
                {Array.from({ length: Math.min(5, pages) }, (_, i) => {
                  const pg = Math.max(1, page - 2) + i;
                  if (pg > pages) return null;
                  return <button key={pg} className={`page-btn ${pg === page ? 'active' : ''}`} onClick={() => load(pg)}>{pg}</button>;
                })}
                <button className="page-btn" onClick={() => load(page + 1)} disabled={page === pages}>›</button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
