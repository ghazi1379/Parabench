import React, { useState, useEffect, useRef } from 'react';
import { Play, RefreshCw, Clock, CheckCircle, AlertCircle, Info, Terminal, Zap, Settings } from 'lucide-react';
import {
  startScraping, getScrapingJobs, getScrapingLogs,
  getScrapingStatus, refreshBenchmark
} from '../utils/api';
import { formatNumber } from '../utils/helpers';
import toast from 'react-hot-toast';

const SITES_INFO = [
  { id: 'parashop', label: 'Parashop', url: 'parashop.tn', color: '#6366f1' },
  { id: 'parafendri', label: 'Parafendri', url: 'parafendri.tn', color: '#22d3ee' },
  { id: 'tunisiepara', label: 'TunisiePara', url: 'tunisiepara.com', color: '#f59e0b' },
];

function StatusBadge({ status }) {
  const map = {
    running: { cls: 'job-status-running', label: 'En cours', pulse: true },
    completed: { cls: 'job-status-completed', label: 'Terminé' },
    failed: { cls: 'job-status-failed', label: 'Échoué' },
    pending: { cls: 'job-status-pending', label: 'En attente' },
    partial: { cls: 'job-status-partial', label: 'Partiel' },
  };
  const s = map[status] || map.pending;
  return (
    <span className={`job-status ${s.cls}`}>
      {s.pulse && <span className="status-pulse" />}
      {s.label}
    </span>
  );
}

function LogLine({ log }) {
  const cls = {
    INFO: 'log-info',
    ERROR: 'log-error',
    WARNING: 'log-warning',
    SUCCESS: 'log-success',
  }[log.level] || '';
  
  const time = new Date(log.created_at).toLocaleTimeString('fr-TN');
  
  return (
    <div style={{ borderBottom: '1px solid #111', paddingBottom: '2px', marginBottom: '2px' }}>
      <span style={{ color: '#4a6080' }}>[{time}]</span>{' '}
      <span style={{ color: log.site === 'system' ? '#8b5cf6' : '#94a3b8' }}>[{log.site}]</span>{' '}
      <span className={cls}>{log.message}</span>
    </div>
  );
}

export default function Admin() {
  const [selectedSites, setSelectedSites] = useState(['parashop', 'parafendri', 'tunisiepara']);
  const [status, setStatus] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [logs, setLogs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const logRef = useRef(null);
  const pollRef = useRef(null);

  const loadStatus = async () => {
    try {
      const res = await getScrapingStatus();
      setStatus(res.data);
    } catch {}
  };

  const loadJobs = async () => {
    try {
      const res = await getScrapingJobs();
      setJobs(res.data);
      if (res.data.length > 0 && !selectedJobId) {
        setSelectedJobId(res.data[0].job_id);
      }
    } catch {}
  };

  const loadLogs = async (jobId) => {
    if (!jobId) return;
    setLoadingLogs(true);
    try {
      const res = await getScrapingLogs(jobId, 200);
      setLogs(res.data.reverse());
      setTimeout(() => {
        if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
      }, 100);
    } catch {}
    setLoadingLogs(false);
  };

  useEffect(() => {
    loadStatus();
    loadJobs();
    
    pollRef.current = setInterval(() => {
      loadStatus();
      if (selectedJobId) loadLogs(selectedJobId);
    }, 5000);
    
    return () => clearInterval(pollRef.current);
  }, []);

  useEffect(() => {
    if (selectedJobId) loadLogs(selectedJobId);
  }, [selectedJobId]);

  const handleStartScraping = async () => {
    if (selectedSites.length === 0) {
      toast.error('Sélectionnez au moins un site');
      return;
    }
    setLoading(true);
    try {
      const res = await startScraping(selectedSites);
      if (res.data.status === 'already_running') {
        toast.error('Un scraping est déjà en cours');
      } else {
        toast.success(`Scraping démarré ! Job: ${res.data.job_id}`);
        setSelectedJobId(res.data.job_id);
        setTimeout(() => {
          loadStatus();
          loadJobs();
        }, 1000);
      }
    } catch (err) {
      toast.error('Erreur lors du démarrage');
    } finally {
      setLoading(false);
    }
  };

  const toggleSite = (siteId) => {
    setSelectedSites(prev =>
      prev.includes(siteId) ? prev.filter(s => s !== siteId) : [...prev, siteId]
    );
  };

  const currentJob = status?.current_job;
  const progress = currentJob ? 
    Math.round((currentJob.scraped_products / Math.max(currentJob.total_products, 1)) * 100) : 0;

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Administration & Scraping</h1>
          <p className="page-subtitle">Contrôle du moteur de collecte de données</p>
        </div>
      </div>

      {/* Main Scraping Control */}
      <div className="scraping-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '6px' }}>
          <Zap size={22} style={{ color: '#6366f1' }} />
          <div className="scraping-title">Lancer le Scraping</div>
          {status?.is_running && <StatusBadge status="running" />}
        </div>
        <div className="scraping-subtitle">
          Collecte automatique des données depuis les 3 sites parapharmaceutiques tunisiens
        </div>

        {/* Site Selection */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Sites à scraper
          </div>
          <div className="site-checkboxes">
            {SITES_INFO.map(site => (
              <label key={site.id} className={`site-checkbox ${selectedSites.includes(site.id) ? 'checked' : ''}`}>
                <input type="checkbox" checked={selectedSites.includes(site.id)} onChange={() => toggleSite(site.id)} />
                <div className="site-checkbox-dot" style={{ background: site.color }} />
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>{site.label}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{site.url}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        <div className="scraping-controls">
          <button
            className="btn btn-primary btn-lg"
            onClick={handleStartScraping}
            disabled={loading || status?.is_running || selectedSites.length === 0}
          >
            {loading || status?.is_running ? (
              <><RefreshCw size={18} style={{ animation: 'spin 1s linear infinite' }} /> Scraping en cours...</>
            ) : (
              <><Play size={18} /> Lancer le Scraping</>
            )}
          </button>
          
          <button className="btn btn-secondary" onClick={async () => {
            await refreshBenchmark();
            toast.success('Benchmark en cours de mise à jour');
          }}>
            <RefreshCw size={16} />
            Mettre à jour Benchmark
          </button>
        </div>

        {/* Progress */}
        {status?.is_running && currentJob && (
          <div style={{ marginTop: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
              <span>Progression: {currentJob.scraped_products} produits traités</span>
              <span>Nouveaux: {currentJob.new_products} | Mis à jour: {currentJob.updated_products}</span>
            </div>
            <div className="progress-bar-wrapper">
              <div className="progress-bar" style={{ width: `${Math.max(5, progress)}%` }} />
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px' }}>
              Erreurs: {currentJob.failed_products} | Job ID: {currentJob.job_id}
            </div>
          </div>
        )}

        {/* Last completed */}
        {!status?.is_running && status?.last_completed && (
          <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.15)', borderRadius: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#10b981', fontWeight: 600, marginBottom: '4px' }}>
              <CheckCircle size={14} />
              Dernier scraping réussi
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {new Date(status.last_completed.completed_at).toLocaleString('fr-TN')} —{' '}
              {formatNumber(status.last_completed.total_products)} produits traités
              ({formatNumber(status.last_completed.new_products)} nouveaux)
            </div>
          </div>
        )}
      </div>

      {/* Automation Info */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div className="card-title">
            <Clock size={16} style={{ color: '#f59e0b' }} />
            Automatisation
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
          {[
            { label: 'Scraping quotidien', value: 'Tous les jours à 02:00', icon: <Clock size={14} />, color: '#f59e0b' },
            { label: 'Cron Jobs', value: 'Celery Beat + Redis', icon: <Settings size={14} />, color: '#6366f1' },
            { label: 'Rétention données', value: 'Historique prix illimité', icon: <Info size={14} />, color: '#22d3ee' },
          ].map(item => (
            <div key={item.label} style={{ padding: '14px', background: 'var(--bg-elevated)', borderRadius: '10px', border: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: item.color, marginBottom: '6px' }}>
                {item.icon}
                <span style={{ fontSize: '12px', fontWeight: 600 }}>{item.label}</span>
              </div>
              <div style={{ fontSize: '13px', color: 'var(--text-primary)' }}>{item.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Jobs History + Logs */}
      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '20px' }}>
        {/* Jobs list */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Clock size={14} style={{ color: '#8b5cf6' }} />
              Historique Jobs
            </div>
            <button className="btn btn-secondary btn-sm btn-icon" onClick={loadJobs}>
              <RefreshCw size={12} />
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '400px', overflowY: 'auto' }}>
            {jobs.length === 0 ? (
              <div className="empty-state" style={{ padding: '30px' }}>
                <div className="empty-state-icon">📋</div>
                <p>Aucun job</p>
              </div>
            ) : jobs.map(job => (
              <div key={job.job_id}
                onClick={() => setSelectedJobId(job.job_id)}
                style={{
                  padding: '12px',
                  background: selectedJobId === job.job_id ? 'rgba(99,102,241,0.1)' : 'var(--bg-elevated)',
                  border: `1px solid ${selectedJobId === job.job_id ? 'rgba(99,102,241,0.3)' : 'var(--border)'}`,
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ fontSize: '12px', fontFamily: 'monospace', color: 'var(--text-muted)' }}>#{job.job_id}</span>
                  <StatusBadge status={job.status} />
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                  Sites: {job.sites}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  {job.total_products > 0 && `${formatNumber(job.total_products)} produits`}
                  {job.created_at && ` · ${new Date(job.created_at).toLocaleString('fr-TN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}`}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Logs */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Terminal size={14} style={{ color: '#22d3ee' }} />
              Logs en Temps Réel
              {selectedJobId && <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>#{selectedJobId}</span>}
            </div>
            <button className="btn btn-secondary btn-sm btn-icon" onClick={() => loadLogs(selectedJobId)} disabled={!selectedJobId}>
              <RefreshCw size={12} />
            </button>
          </div>
          
          {!selectedJobId ? (
            <div className="empty-state">
              <div className="empty-state-icon">📄</div>
              <p>Sélectionnez un job pour voir les logs</p>
            </div>
          ) : loadingLogs ? (
            <div className="loading-wrapper" style={{ padding: '30px' }}>
              <div className="spinner" />
            </div>
          ) : (
            <div className="log-container" ref={logRef}>
              {logs.length === 0 ? (
                <span style={{ color: 'var(--text-muted)' }}>Aucun log disponible</span>
              ) : logs.map(log => (
                <LogLine key={log.id} log={log} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
