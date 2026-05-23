import React, { useState, useEffect } from 'react';
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend, LineChart, Line
} from 'recharts';
import {
  TrendingUp, AlertTriangle, Package, Zap,
  RefreshCw, Search, BarChart3, Globe
} from 'lucide-react';
import api from '../utils/api';
import { formatPrice, formatNumber, getSiteLabel, getSiteColor } from '../utils/helpers';
import toast from 'react-hot-toast';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: '#111827', border: '1px solid #1e2d45',
      borderRadius: '10px', padding: '10px 14px', fontSize: '12px'
    }}>
      <p style={{ color: '#8fa8cc', marginBottom: '6px', fontWeight: 600 }}>{label}</p>
      {payload.map((e, i) => (
        <p key={i} style={{ color: e.color }}>
          {e.name}: <strong>{typeof e.value === 'number' ? e.value.toFixed(2) : e.value}</strong>
        </p>
      ))}
    </div>
  );
};

// ── Onglet Aperçu Marché ──────────────────────────────────
function MarketOverview() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/analytics/market-overview').then(r => {
      setData(r.data); setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-wrapper"><div className="spinner" /></div>;
  if (!data) return <div className="empty-state"><p>Aucune donnée disponible</p></div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* KPIs globaux */}
      <div className="stats-grid">
        {[
          { label: 'Produits indexés', value: formatNumber(data.total_products), color: '#6366f1' },
          { label: 'Avec prix', value: formatNumber(data.total_with_price), color: '#22d3ee' },
          { label: 'Prix moyen marché', value: `${data.avg_price_market} TND`, color: '#f59e0b' },
          { label: 'Sites comparés', value: data.sites.length, color: '#10b981' },
        ].map((s, i) => (
          <div key={i} className="stat-card">
            <div className="stat-card-accent" style={{ background: s.color }} />
            <div className="stat-card-value">{s.value}</div>
            <div className="stat-card-label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Comparaison par site */}
      <div className="charts-grid">
        <div className="card">
          <div className="card-header">
            <div className="card-title"><Globe size={16} style={{ color: '#6366f1' }} />Produits par site</div>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.sites}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2d45" />
              <XAxis dataKey="site" stroke="#4a6080" tick={{ fontSize: 11 }}
                tickFormatter={(v) => getSiteLabel(v)} />
              <YAxis stroke="#4a6080" tick={{ fontSize: 11 }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" name="Produits" radius={[6, 6, 0, 0]}>
                {data.sites.map((s, i) => <Cell key={i} fill={getSiteColor(s.site)} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title"><TrendingUp size={16} style={{ color: '#22d3ee' }} />Prix moyen par site (TND)</div>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.sites}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2d45" />
              <XAxis dataKey="site" stroke="#4a6080" tick={{ fontSize: 11 }}
                tickFormatter={(v) => getSiteLabel(v)} />
              <YAxis stroke="#4a6080" tick={{ fontSize: 11 }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="avg_price" name="Prix moyen" radius={[6, 6, 0, 0]}>
                {data.sites.map((s, i) => <Cell key={i} fill={getSiteColor(s.site)} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title"><Zap size={16} style={{ color: '#f43f5e' }} />Taux de promotion (%)</div>
          </div>
          <div style={{ padding: '8px 0' }}>
            {data.sites.map(s => (
              <div key={s.site} style={{ marginBottom: '14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                  <span style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 500 }}>
                    {getSiteLabel(s.site)}
                  </span>
                  <span style={{ fontSize: '13px', fontWeight: 700, color: getSiteColor(s.site) }}>
                    {s.promo_rate}% <small style={{ color: 'var(--text-muted)', fontWeight: 400 }}>({formatNumber(s.promo_count)} produits)</small>
                  </span>
                </div>
                <div className="progress-bar-wrapper">
                  <div className="progress-bar" style={{
                    width: `${s.promo_rate}%`,
                    background: `linear-gradient(90deg, ${getSiteColor(s.site)}, ${getSiteColor(s.site)}88)`
                  }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Onglet Alertes Prix ──────────────────────────────────
function PriceAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [threshold, setThreshold] = useState(20);
  const [loading, setLoading] = useState(true);

  const load = (t) => {
    setLoading(true);
    api.get(`/api/analytics/price-alerts?threshold=${t}`).then(r => {
      setAlerts(r.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  };

  useEffect(() => { load(threshold); }, []);

  return (
    <div>
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap' }}>
        <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Seuil d'alerte :</div>
        {[10, 20, 30, 50].map(t => (
          <button key={t}
            className={`btn btn-sm ${threshold === t ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setThreshold(t); load(t); }}>
            &gt;{t}%
          </button>
        ))}
        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{alerts.length} alertes</span>
      </div>

      {loading ? (
        <div className="loading-wrapper"><div className="spinner" /></div>
      ) : alerts.length === 0 ? (
        <div className="empty-state">
          <AlertTriangle size={36} opacity={0.3} />
          <p>Aucune alerte avec ce seuil</p>
        </div>
      ) : (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Produit</th>
                <th>Marque</th>
                <th>Site le - cher</th>
                <th>Prix min</th>
                <th>Site le + cher</th>
                <th>Prix max</th>
                <th>Écart</th>
                <th>Économie</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((a, i) => (
                <tr key={i}>
                  <td style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '12px' }}>{a.product}</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{a.brand || '—'}</td>
                  <td><span className={`site-tag site-tag-${a.cheapest_site}`}>{getSiteLabel(a.cheapest_site)}</span></td>
                  <td style={{ fontWeight: 700, color: '#10b981' }}>{formatPrice(a.cheapest_price)}</td>
                  <td><span className={`site-tag site-tag-${a.expensive_site}`}>{getSiteLabel(a.expensive_site)}</span></td>
                  <td style={{ fontWeight: 700, color: '#f43f5e' }}>{formatPrice(a.expensive_price)}</td>
                  <td>
                    <span className={`diff-badge ${a.diff_percent > 30 ? 'diff-high' : a.diff_percent > 10 ? 'diff-mid' : 'diff-low'}`}>
                      {a.diff_percent?.toFixed(1)}%
                    </span>
                  </td>
                  <td style={{ fontWeight: 700, color: '#10b981', fontSize: '13px' }}>{formatPrice(a.saving)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Onglet Gaps Assortiment ──────────────────────────────────
function AssortmentGaps() {
  const [gaps, setGaps] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/analytics/assortment-gaps').then(r => {
      setGaps(r.data); setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-wrapper"><div className="spinner" /></div>;

  const only1 = gaps.filter(g => g.sites_count === 1);
  const only2 = gaps.filter(g => g.sites_count === 2);

  return (
    <div>
      <div style={{ display: 'flex', gap: '16px', marginBottom: '20px', flexWrap: 'wrap' }}>
        <div className="stat-card" style={{ flex: 1, minWidth: '160px' }}>
          <div className="stat-card-accent" style={{ background: '#f43f5e' }} />
          <div className="stat-card-value">{only1.length}</div>
          <div className="stat-card-label">Marques exclusives (1 site)</div>
        </div>
        <div className="stat-card" style={{ flex: 1, minWidth: '160px' }}>
          <div className="stat-card-accent" style={{ background: '#f59e0b' }} />
          <div className="stat-card-value">{only2.length}</div>
          <div className="stat-card-label">Marques sur 2 sites</div>
        </div>
        <div className="stat-card" style={{ flex: 1, minWidth: '160px' }}>
          <div className="stat-card-accent" style={{ background: '#10b981' }} />
          <div className="stat-card-value">{gaps.length > 0 ? gaps.length : '—'}</div>
          <div className="stat-card-label">Total gaps identifiés</div>
        </div>
      </div>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Marque</th>
              <th>Sites présents</th>
              <th>Sites manquants</th>
              <th>Couverture</th>
            </tr>
          </thead>
          <tbody>
            {gaps.slice(0, 80).map((g, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 600, fontSize: '13px' }}>{g.brand}</td>
                <td>
                  <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                    {g.present_on.map(s => (
                      <span key={s} className={`site-tag site-tag-${s}`}>{getSiteLabel(s)}</span>
                    ))}
                  </div>
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                    {g.missing_on.map(s => (
                      <span key={s} style={{
                        padding: '2px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: 600,
                        background: 'rgba(244,63,94,0.1)', color: '#f43f5e', border: '1px solid rgba(244,63,94,0.2)'
                      }}>{getSiteLabel(s)} ✗</span>
                    ))}
                  </div>
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ flex: 1, height: '6px', background: 'var(--bg-elevated)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%', borderRadius: '3px',
                        width: `${(g.sites_count / 3) * 100}%`,
                        background: g.sites_count === 1 ? '#f43f5e' : g.sites_count === 2 ? '#f59e0b' : '#10b981'
                      }} />
                    </div>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{g.sites_count}/3</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Onglet Évolution Marque ──────────────────────────────────
function BrandEvolution() {
  const [brand, setBrand] = useState('');
  const [searchBrand, setSearchBrand] = useState('');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  const search = () => {
    if (!brand.trim()) return;
    setLoading(true);
    api.get(`/api/analytics/brand-evolution?brand=${encodeURIComponent(brand)}&days=60`).then(r => {
      setData(r.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  };

  // Group by date/site
  const byDateSite = data.reduce((acc, d) => {
    const key = d.date;
    if (!acc[key]) acc[key] = { date: key };
    acc[key][d.site] = d.avg_price;
    return acc;
  }, {});
  const chartData = Object.values(byDateSite).sort((a, b) => a.date.localeCompare(b.date));

  return (
    <div>
      <div style={{ display: 'flex', gap: '12px', marginBottom: '24px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: '200px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px' }}>Rechercher une marque</div>
          <input className="input" placeholder="ex: Avène, Vichy, Bioderma..."
            value={brand} onChange={e => setBrand(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && search()} />
        </div>
        <button className="btn btn-primary" onClick={search} disabled={loading || !brand.trim()}>
          <Search size={14} /> Analyser
        </button>
      </div>

      {loading ? (
        <div className="loading-wrapper"><div className="spinner" /></div>
      ) : chartData.length === 0 ? (
        <div className="empty-state">
          <BarChart3 size={36} opacity={0.3} />
          <p>Recherchez une marque pour voir l'évolution de ses prix</p>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Données disponibles après plusieurs sessions de scraping</p>
        </div>
      ) : (
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <TrendingUp size={16} style={{ color: '#6366f1' }} />
              Évolution des prix — {brand}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2d45" />
              <XAxis dataKey="date" stroke="#4a6080" tick={{ fontSize: 10 }} />
              <YAxis stroke="#4a6080" tick={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              {['parashop', 'parafendri', 'tunisiepara'].map(site => (
                <Line key={site} type="monotone" dataKey={site} stroke={getSiteColor(site)}
                  strokeWidth={2} name={getSiteLabel(site)} connectNulls dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

// ── Page principale ──────────────────────────────────
const TABS = [
  { id: 'overview', label: 'Aperçu Marché', icon: Globe },
  { id: 'alerts', label: 'Alertes Prix', icon: AlertTriangle },
  { id: 'gaps', label: 'Gaps Assortiment', icon: Package },
  { id: 'brand', label: 'Évolution Marque', icon: TrendingUp },
];

export default function Analytics() {
  const [tab, setTab] = useState('overview');

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Market Intelligence</h1>
          <p className="page-subtitle">Analyses avancées du marché parapharmaceutique tunisien</p>
        </div>
      </div>

      {/* Tab Nav */}
      <div style={{
        display: 'flex', gap: '4px', marginBottom: '24px',
        background: 'var(--bg-card)', padding: '4px', borderRadius: '10px',
        border: '1px solid var(--border)', width: 'fit-content', flexWrap: 'wrap'
      }}>
        {TABS.map(({ id, label, icon: Icon }) => (
          <button key={id}
            className={`btn btn-sm ${tab === id ? 'btn-primary' : 'btn-secondary'}`}
            style={{ border: 'none' }}
            onClick={() => setTab(id)}>
            <Icon size={13} />
            {label}
          </button>
        ))}
      </div>

      {tab === 'overview' && <MarketOverview />}
      {tab === 'alerts' && <PriceAlerts />}
      {tab === 'gaps' && <AssortmentGaps />}
      {tab === 'brand' && <BrandEvolution />}
    </div>
  );
}
