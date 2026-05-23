import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import {
  Package, Tag, TrendingUp, Percent, ShoppingBag,
  RefreshCw, ExternalLink, Award, Star
} from 'lucide-react';
import {
  getDashboardStats, getTopBrands, getTopCategories,
  getPriceDistribution, getPromotions, getPriceEvolution
} from '../utils/api';
import { formatPrice, formatNumber, getSiteColor, getSiteLabel } from '../utils/helpers';

const CHART_COLORS = {
  parashop: '#6366f1',
  parafendri: '#22d3ee',
  tunisiepara: '#f59e0b',
  indigo: '#6366f1',
  cyan: '#22d3ee',
  amber: '#f59e0b',
  emerald: '#10b981',
  rose: '#f43f5e',
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: '#111827', border: '1px solid #1e2d45', borderRadius: '10px',
      padding: '10px 14px', fontSize: '12px'
    }}>
      <p style={{ color: '#8fa8cc', marginBottom: '6px', fontWeight: 600 }}>{label}</p>
      {payload.map((entry, i) => (
        <p key={i} style={{ color: entry.color }}>
          {entry.name}: <strong>{typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}</strong>
        </p>
      ))}
    </div>
  );
};

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [brands, setBrands] = useState([]);
  const [categories, setCategories] = useState([]);
  const [priceDistrib, setPriceDistrib] = useState([]);
  const [promotions, setPromotions] = useState([]);
  const [priceEvolution, setPriceEvolution] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [statsRes, brandsRes, catsRes, distribRes, promosRes, evolRes] = await Promise.all([
        getDashboardStats(),
        getTopBrands(10),
        getTopCategories(10),
        getPriceDistribution(),
        getPromotions(12),
        getPriceEvolution(30),
      ]);
      setStats(statsRes.data);
      setBrands(brandsRes.data);
      setCategories(catsRes.data);
      setPriceDistrib(distribRes.data);
      setPromotions(promosRes.data);
      setPriceEvolution(evolRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAll(); }, []);

  // Transform price evolution for chart
  const evolutionByDate = priceEvolution.reduce((acc, item) => {
    if (!acc[item.date]) acc[item.date] = { date: item.date };
    acc[item.date][item.site] = item.avg_price;
    return acc;
  }, {});
  const evolutionData = Object.values(evolutionByDate).sort((a, b) => a.date.localeCompare(b.date));

  // Pie data for products per site
  const siteData = stats ? Object.entries(stats.products_per_site || {}).map(([site, count]) => ({
    name: getSiteLabel(site),
    value: count,
    site,
  })) : [];

  if (loading) {
    return (
      <div className="loading-wrapper">
        <div className="spinner" />
        <span>Chargement du dashboard...</span>
      </div>
    );
  }

  const STAT_CARDS = [
    {
      label: 'Total Produits',
      value: formatNumber(stats?.total_products),
      icon: <Package size={20} />,
      color: '#6366f1',
      sub: `Mis à jour: ${stats?.last_scraping ? new Date(stats.last_scraping).toLocaleDateString('fr-TN') : 'Jamais'}`
    },
    {
      label: 'Marques Suivies',
      value: formatNumber(stats?.total_brands),
      icon: <Award size={20} />,
      color: '#22d3ee',
      sub: 'Marques actives'
    },
    {
      label: 'Catégories',
      value: formatNumber(stats?.total_categories),
      icon: <Tag size={20} />,
      color: '#f59e0b',
      sub: 'Catégories distinctes'
    },
    {
      label: 'Promotions',
      value: formatNumber(stats?.promotions_count),
      icon: <Percent size={20} />,
      color: '#f43f5e',
      sub: 'Produits en promo'
    },
    {
      label: 'Prix Moyen',
      value: `${Number(stats?.avg_price || 0).toFixed(3)}`,
      icon: <TrendingUp size={20} />,
      color: '#10b981',
      sub: 'TND marché global'
    },
    {
      label: 'Benchmarks',
      value: formatNumber(stats?.benchmark_count),
      icon: <ShoppingBag size={20} />,
      color: '#8b5cf6',
      sub: 'Produits multi-sites'
    },
  ];

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard Marché</h1>
          <p className="page-subtitle">Vue d'ensemble du marché parapharmaceutique tunisien</p>
        </div>
        <div className="page-actions">
          <button className="btn btn-secondary btn-sm" onClick={loadAll}>
            <RefreshCw size={14} />
            Actualiser
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="stats-grid">
        {STAT_CARDS.map((s, i) => (
          <div key={i} className="stat-card">
            <div className="stat-card-accent" style={{ background: `linear-gradient(90deg, ${s.color}, ${s.color}88)` }} />
            <div className="stat-card-icon" style={{ background: `${s.color}18` }}>
              <span style={{ color: s.color }}>{s.icon}</span>
            </div>
            <div className="stat-card-value">{s.value}</div>
            <div className="stat-card-label">{s.label}</div>
            <div className="stat-card-sub">{s.sub}</div>
          </div>
        ))}
      </div>

      {/* Charts Row 1 */}
      <div className="charts-grid">
        {/* Price Evolution */}
        <div className="card" style={{ gridColumn: evolutionData.length ? 'span 2' : 'span 1' }}>
          <div className="card-header">
            <div className="card-title">
              <TrendingUp size={16} style={{ color: '#6366f1' }} />
              Évolution des Prix (30 jours)
            </div>
          </div>
          {evolutionData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={evolutionData}>
                <defs>
                  {['parashop', 'parafendri', 'tunisiepara'].map(site => (
                    <linearGradient key={site} id={`grad_${site}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={getSiteColor(site)} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={getSiteColor(site)} stopOpacity={0} />
                    </linearGradient>
                  ))}
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2d45" />
                <XAxis dataKey="date" stroke="#4a6080" tick={{ fontSize: 11 }} />
                <YAxis stroke="#4a6080" tick={{ fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                {['parashop', 'parafendri', 'tunisiepara'].map(site => (
                  <Area key={site} type="monotone" dataKey={site} stroke={getSiteColor(site)}
                    fill={`url(#grad_${site})`} strokeWidth={2} name={getSiteLabel(site)} connectNulls />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state" style={{ padding: '40px' }}>
              <div className="empty-state-icon">📈</div>
              <p>Lancez un scraping pour voir l'évolution des prix</p>
            </div>
          )}
        </div>

        {/* Products per site */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Package size={16} style={{ color: '#22d3ee' }} />
              Répartition par Site
            </div>
          </div>
          {siteData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={siteData} dataKey="value" nameKey="name"
                  cx="50%" cy="50%" outerRadius={90} innerRadius={50}
                  paddingAngle={4}>
                  {siteData.map((entry, i) => (
                    <Cell key={i} fill={getSiteColor(entry.site)} />
                  ))}
                </Pie>
                <Tooltip formatter={(val) => formatNumber(val)} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state" style={{ padding: '40px' }}>
              <div className="empty-state-icon">🥧</div>
              <p>Aucune donnée disponible</p>
            </div>
          )}
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="charts-grid">
        {/* Top Brands */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Award size={16} style={{ color: '#f59e0b' }} />
              Top 10 Marques
            </div>
          </div>
          {brands.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={brands} layout="vertical" margin={{ left: 8, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2d45" horizontal={false} />
                <XAxis type="number" stroke="#4a6080" tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="brand" stroke="#4a6080" tick={{ fontSize: 10 }} width={90} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" name="Produits" radius={[0, 4, 4, 0]}>
                  {brands.map((_, i) => (
                    <Cell key={i} fill={`hsl(${220 + i * 15}, 70%, ${55 + i * 2}%)`} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state"><div className="empty-state-icon">🏷️</div><p>Aucune donnée</p></div>
          )}
        </div>

        {/* Price Distribution */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <TrendingUp size={16} style={{ color: '#10b981' }} />
              Distribution des Prix
            </div>
          </div>
          {priceDistrib.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={priceDistrib}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2d45" />
                <XAxis dataKey="range" stroke="#4a6080" tick={{ fontSize: 10 }} />
                <YAxis stroke="#4a6080" tick={{ fontSize: 10 }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" name="Produits" fill="#10b981" radius={[4, 4, 0, 0]}>
                  {priceDistrib.map((_, i) => (
                    <Cell key={i} fill={`hsl(${160 - i * 20}, 70%, 50%)`} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state"><div className="empty-state-icon">💰</div><p>Aucune donnée</p></div>
          )}
        </div>

        {/* Top Categories */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Tag size={16} style={{ color: '#8b5cf6' }} />
              Top 10 Catégories
            </div>
          </div>
          {categories.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={categories} layout="vertical" margin={{ left: 8, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2d45" horizontal={false} />
                <XAxis type="number" stroke="#4a6080" tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="category" stroke="#4a6080" tick={{ fontSize: 10 }} width={100} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" name="Produits" radius={[0, 4, 4, 0]}>
                  {categories.map((_, i) => (
                    <Cell key={i} fill={`hsl(${260 + i * 15}, 65%, ${55 + i * 2}%)`} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state"><div className="empty-state-icon">📦</div><p>Aucune donnée</p></div>
          )}
        </div>
      </div>

      {/* Current Promotions */}
      {promotions.length > 0 && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <div className="card-header">
            <div className="card-title">
              <Star size={16} style={{ color: '#f43f5e' }} />
              Meilleures Promotions du Moment
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '12px' }}>
            {promotions.map(p => (
              <div key={p.id} style={{
                background: 'var(--bg-elevated)', border: '1px solid var(--border-light)',
                borderRadius: '10px', padding: '14px', display: 'flex', gap: '12px', alignItems: 'flex-start'
              }}>
                {p.image_url ? (
                  <img src={p.image_url} alt={p.name} className="product-img" onError={e => e.target.style.display='none'} />
                ) : (
                  <div className="product-img-placeholder">🧴</div>
                )}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px', 
                                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</div>
                  {p.brand && <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>{p.brand}</div>}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 700, color: '#10b981', fontSize: '14px' }}>{formatPrice(p.price)}</span>
                    {p.old_price && <span style={{ textDecoration: 'line-through', color: 'var(--text-muted)', fontSize: '11px' }}>{formatPrice(p.old_price)}</span>}
                    {p.discount_percent && (
                      <span className="badge badge-promo">-{p.discount_percent}%</span>
                    )}
                  </div>
                  <div style={{ marginTop: '6px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span className={`site-tag site-tag-${p.site}`}>{getSiteLabel(p.site)}</span>
                    <a href={p.product_url} target="_blank" rel="noreferrer" style={{ color: 'var(--text-muted)' }}>
                      <ExternalLink size={12} />
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
