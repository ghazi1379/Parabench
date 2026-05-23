import React, { useState, useEffect, useCallback } from 'react';
import { Search, Filter, ExternalLink, Download, RefreshCw, Package } from 'lucide-react';
import { getProducts, getBrands, getCategories, exportCSV, exportExcel, exportPDF } from '../utils/api';
import { formatPrice, formatNumber, getSiteLabel } from '../utils/helpers';
import toast from 'react-hot-toast';

const SITES = ['parashop', 'parafendri', 'tunisiepara'];

export default function Products() {
  const [products, setProducts] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [brands, setBrands] = useState([]);
  const [categories, setCategories] = useState([]);

  const [filters, setFilters] = useState({
    search: '', site: '', brand: '', category: '',
    min_price: '', max_price: '', has_promotion: '', in_stock: '',
    sort_by: 'updated_at', sort_order: 'desc',
  });

  const loadFilters = async () => {
    try {
      const [br, cats] = await Promise.all([getBrands(), getCategories()]);
      setBrands(br.data);
      setCategories(cats.data);
    } catch {}
  };

  const load = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const params = { page: p, limit: 25, ...filters };
      if (!params.search) delete params.search;
      if (!params.site) delete params.site;
      if (!params.brand) delete params.brand;
      if (!params.category) delete params.category;
      if (!params.min_price) delete params.min_price;
      if (!params.max_price) delete params.max_price;
      if (params.has_promotion === '') delete params.has_promotion;
      if (params.in_stock === '') delete params.in_stock;
      
      const res = await getProducts(params);
      setProducts(res.data.products);
      setTotal(res.data.total);
      setPages(res.data.pages);
      setPage(p);
    } catch (err) {
      toast.error('Erreur lors du chargement des produits');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { loadFilters(); }, []);
  useEffect(() => { load(1); }, [filters]);

  const handleFilter = (key, value) => {
    setFilters(f => ({ ...f, [key]: value }));
  };

  const handleExportCSV = () => { exportCSV({}); toast.success('Export CSV en cours...'); };
  const handleExportExcel = () => { exportExcel({}); toast.success('Export Excel en cours...'); };
  const handleExportPDF = () => { exportPDF({}); toast.success('Export PDF en cours...'); };

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Catalogue Produits</h1>
          <p className="page-subtitle">{formatNumber(total)} produits trouvés</p>
        </div>
        <div className="page-actions">
          <div className="export-group">
            <button className="btn btn-secondary btn-sm" onClick={handleExportCSV}>
              <Download size={14} /> CSV
            </button>
            <button className="btn btn-secondary btn-sm" onClick={handleExportExcel}>
              <Download size={14} /> Excel
            </button>
            <button className="btn btn-secondary btn-sm" onClick={handleExportPDF}>
              <Download size={14} /> PDF
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
          <div className="search-wrapper">
            <Search size={14} className="search-icon" />
            <input
              className="input search-input"
              placeholder="Rechercher produit, marque..."
              value={filters.search}
              onChange={e => handleFilter('search', e.target.value)}
            />
          </div>

          <select className="select" value={filters.site} onChange={e => handleFilter('site', e.target.value)}>
            <option value="">Tous les sites</option>
            {SITES.map(s => <option key={s} value={s}>{getSiteLabel(s)}</option>)}
          </select>

          <select className="select" value={filters.brand} onChange={e => handleFilter('brand', e.target.value)}>
            <option value="">Toutes les marques</option>
            {brands.slice(0, 100).map(b => <option key={b} value={b}>{b}</option>)}
          </select>

          <select className="select" value={filters.category} onChange={e => handleFilter('category', e.target.value)}>
            <option value="">Toutes catégories</option>
            {categories.slice(0, 100).map(c => <option key={c} value={c}>{c}</option>)}
          </select>

          <select className="select" value={filters.has_promotion} onChange={e => handleFilter('has_promotion', e.target.value)}>
            <option value="">Promotions: Toutes</option>
            <option value="true">En promotion</option>
            <option value="false">Sans promotion</option>
          </select>

          <select className="select" value={filters.in_stock} onChange={e => handleFilter('in_stock', e.target.value)}>
            <option value="">Stock: Tous</option>
            <option value="true">En stock</option>
            <option value="false">Rupture</option>
          </select>

          <div style={{ display: 'flex', gap: '8px' }}>
            <input className="input" placeholder="Prix min" type="number"
              value={filters.min_price} onChange={e => handleFilter('min_price', e.target.value)} />
            <input className="input" placeholder="Prix max" type="number"
              value={filters.max_price} onChange={e => handleFilter('max_price', e.target.value)} />
          </div>

          <select className="select" value={`${filters.sort_by}_${filters.sort_order}`}
            onChange={e => {
              const [by, order] = e.target.value.split('_');
              handleFilter('sort_by', by);
              handleFilter('sort_order', order);
            }}>
            <option value="updated_at_desc">Plus récents</option>
            <option value="price_asc">Prix: croissant</option>
            <option value="price_desc">Prix: décroissant</option>
            <option value="discount_percent_desc">Remise: max</option>
            <option value="name_asc">Nom: A-Z</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="card">
        {loading ? (
          <div className="loading-wrapper">
            <div className="spinner" />
            <span>Chargement...</span>
          </div>
        ) : products.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📦</div>
            <p style={{ fontWeight: 600 }}>Aucun produit trouvé</p>
            <p style={{ fontSize: '12px' }}>Modifiez vos filtres ou lancez un scraping</p>
          </div>
        ) : (
          <>
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Image</th>
                    <th>Produit</th>
                    <th>Marque</th>
                    <th>Catégorie</th>
                    <th>Site</th>
                    <th>Prix</th>
                    <th>Ancien Prix</th>
                    <th>Remise</th>
                    <th>Stock</th>
                    <th>Lien</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map(p => (
                    <tr key={p.id}>
                      <td>
                        {p.image_url ? (
                          <img src={p.image_url} alt={p.name} className="product-img"
                            onError={e => { e.target.onerror = null; e.target.style.display = 'none'; }} />
                        ) : (
                          <div className="product-img-placeholder">🧴</div>
                        )}
                      </td>
                      <td style={{ maxWidth: '280px' }}>
                        <div style={{ fontWeight: 500, fontSize: '13px', 
                                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                                      maxWidth: '260px' }}
                             title={p.name}>{p.name}</div>
                      </td>
                      <td>
                        {p.brand ? <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{p.brand}</span> : '—'}
                      </td>
                      <td>
                        {p.category ? <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{p.category}</span> : '—'}
                      </td>
                      <td>
                        <span className={`site-tag site-tag-${p.site}`}>{getSiteLabel(p.site)}</span>
                      </td>
                      <td>
                        {p.price ? (
                          <span style={{ fontWeight: 700, fontSize: '14px', color: '#10b981' }}>
                            {formatPrice(p.price)}
                          </span>
                        ) : '—'}
                      </td>
                      <td>
                        {p.old_price ? (
                          <span style={{ textDecoration: 'line-through', color: 'var(--text-muted)', fontSize: '12px' }}>
                            {formatPrice(p.old_price)}
                          </span>
                        ) : '—'}
                      </td>
                      <td>
                        {p.discount_percent ? (
                          <span className="badge badge-promo">-{p.discount_percent}%</span>
                        ) : p.has_promotion ? (
                          <span className="badge badge-promo">Promo</span>
                        ) : '—'}
                      </td>
                      <td>
                        <span className={`badge ${p.in_stock ? 'badge-stock' : 'badge-nostock'}`}>
                          {p.in_stock ? '✓ Stock' : '✗ Rupture'}
                        </span>
                      </td>
                      <td>
                        <a href={p.product_url} target="_blank" rel="noreferrer"
                          className="btn btn-secondary btn-sm btn-icon">
                          <ExternalLink size={12} />
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="pagination">
              <div className="pagination-info">
                Page {page} / {pages} — {formatNumber(total)} produits
              </div>
              <div className="pagination-btns">
                <button className="page-btn" onClick={() => load(1)} disabled={page === 1}>«</button>
                <button className="page-btn" onClick={() => load(page - 1)} disabled={page === 1}>‹</button>
                {Array.from({ length: Math.min(5, pages) }, (_, i) => {
                  const p = Math.max(1, page - 2) + i;
                  if (p > pages) return null;
                  return (
                    <button key={p} className={`page-btn ${p === page ? 'active' : ''}`} onClick={() => load(p)}>{p}</button>
                  );
                })}
                <button className="page-btn" onClick={() => load(page + 1)} disabled={page === pages}>›</button>
                <button className="page-btn" onClick={() => load(pages)} disabled={page === pages}>»</button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
