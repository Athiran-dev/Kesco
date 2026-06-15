import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileSpreadsheet, Settings, Filter, BarChart3, Database, Save, Search, X, Check } from 'lucide-react';
import axios from 'axios';
import './index.css';

const API_URL = 'http://127.0.0.1:8000/api';

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [year, setYear] = useState('2024');
  const [month, setMonth] = useState('April');
  const [status, setStatus] = useState({ base_loaded: false, merged_loaded: false, base_headers: [], merged_headers: [] });
  
  // File Loading State
  const [loading, setLoading] = useState(false);
  
  // Filters
  const [filters, setFilters] = useState({
    smart_meter: ['All'],
    govt: ['All'],
    bill_basis: ['All'],
    tariff_type: ['All']
  });

  // Analysis State
  const [analysis, setAnalysis] = useState({
    f1: 'Select...', h1: 'Select...',
    f2: 'Select...', h2: 'Select...'
  });
  const [tables, setTables] = useState({ t1: null, d1_total: 0, t2: null, d2_total: 0 });
  
  // Operation
  const [operation, setOperation] = useState('Select Operation...');
  
  // Record Search
  const [searchAcct, setSearchAcct] = useState('');
  const [record, setRecord] = useState(null);
  const [updateField, setUpdateField] = useState('');
  const [updateValue, setUpdateValue] = useState('');

  const fetchStatus = async () => {
    try {
      const res = await axios.get(`${API_URL}/status`);
      setStatus(res.data);
    } catch (e) { console.error(e); }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleUpload = async (e, type) => {
    const file = e.target.files[0];
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', type);
    formData.append('year', year);
    formData.append('month', month);

    try {
      await axios.post(`${API_URL}/upload`, formData);
      await fetchStatus();
    } catch (err) {
      alert("Error uploading file");
    }
    setLoading(false);
  };

  const handleAnalysis = async () => {
    try {
      const res = await axios.post(`${API_URL}/analysis`, {
        filters,
        f1: analysis.f1, h1: analysis.h1,
        f2: analysis.f2, h2: analysis.h2
      });
      setTables({
        t1: res.data.table1, d1_total: res.data.d1_total,
        t2: res.data.table2, d2_total: res.data.d2_total
      });
    } catch (err) { console.error(err); }
  };

  useEffect(() => {
    if (analysis.f1 !== 'Select...' || analysis.f2 !== 'Select...') {
      handleAnalysis();
    }
  }, [analysis, filters]);

  const handleSearch = async () => {
    if (!searchAcct) return;
    try {
      const res = await axios.get(`${API_URL}/search/${searchAcct}`);
      setRecord(res.data.record);
    } catch (err) {
      alert("Account not found");
      setRecord(null);
    }
  };

  const handleUpdate = async () => {
    if (!updateField || !updateValue) return;
    try {
      await axios.post(`${API_URL}/update/${searchAcct}`, {
        field: updateField,
        value: updateValue
      });
      alert("Updated successfully!");
      handleSearch();
    } catch (err) {
      alert("Error updating record");
    }
  };

  const renderOperationResult = () => {
    if (operation === 'Select Operation...') return null;
    let res = 0, resStr = '';
    const d1 = tables.d1_total;
    const d2 = tables.d2_total;
    if (d2 === 0 && operation.includes('÷ D2')) return <div className="text-red-400 mt-4">Error: Division by zero</div>;
    if (d1 === 0 && operation.includes('÷ D1')) return <div className="text-red-400 mt-4">Error: Division by zero</div>;

    if (operation === 'D1 ÷ D2 × 100') { res = (d1/d2)*100; resStr = `${res.toFixed(2)} %`; }
    if (operation === 'D2 ÷ D1 × 100') { res = (d2/d1)*100; resStr = `${res.toFixed(2)} %`; }
    if (operation === 'D1 − D2') { res = d1 - d2; resStr = `${res.toLocaleString()}`; }
    if (operation === 'D2 − D1') { res = d2 - d1; resStr = `${res.toLocaleString()}`; }
    if (operation === 'D1 ÷ D2') { res = d1 / d2; resStr = `${res.toFixed(4)}`; }
    if (operation === 'D2 ÷ D1') { res = d2 / d1; resStr = `${res.toFixed(4)}`; }

    return (
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-4 p-4 glass-card border-green-500/30 bg-green-500/10">
        <h4 style={{ color: '#4ADE80', fontSize: '1.5rem', fontWeight: 'bold' }}>{resStr}</h4>
        <p style={{ color: 'var(--text-muted)' }}>{operation}</p>
      </motion.div>
    );
  };

  const navItems = [
    { id: 'upload', icon: <Upload size={18}/>, label: 'Data Hub' },
    { id: 'analysis', icon: <BarChart3 size={18}/>, label: 'Analysis' },
    { id: 'records', icon: <Database size={18}/>, label: 'Records' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      
      {/* Sidebar */}
      <motion.div 
        initial={{ x: -200 }} animate={{ x: 0 }}
        style={{ width: '260px', borderRight: '1px solid var(--border-color)', background: 'rgba(15, 23, 42, 0.8)', backdropFilter: 'blur(10px)', padding: '24px', display: 'flex', flexDirection: 'column' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '40px' }}>
          <div style={{ background: 'var(--primary)', padding: '8px', borderRadius: '8px' }}><Settings size={20} color="white"/></div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: '600' }}>KESCO Dashboard</h2>
        </div>

        <div style={{ marginBottom: '40px' }}>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px', display: 'block' }}>Workspace Year</label>
          <select className="select-styled" value={year} onChange={e => setYear(e.target.value)}>
            {['2024','2025','2026','2027'].map(y => <option key={y}>{y}</option>)}
          </select>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px', marginTop: '16px', display: 'block' }}>Workspace Month</label>
          <select className="select-styled" value={month} onChange={e => setMonth(e.target.value)}>
            {['April','May','June','July','August','September','October','November','December','January','February','March'].map(m => <option key={m}>{m}</option>)}
          </select>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {navItems.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', borderRadius: '8px', cursor: 'pointer',
                background: activeTab === item.id ? 'var(--primary)' : 'transparent',
                color: activeTab === item.id ? 'white' : 'var(--text-muted)',
                border: 'none', textAlign: 'left', fontWeight: '500', transition: 'all 0.2s'
              }}
            >
              {item.icon} {item.label}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Main Content */}
      <div style={{ flex: 1, padding: '40px', overflowY: 'auto' }}>
        <AnimatePresence mode="wait">
          
          {/* UPLOAD TAB */}
          {activeTab === 'upload' && (
            <motion.div key="upload" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
              <h1 style={{ fontSize: '2rem', marginBottom: '8px' }}>Data Hub</h1>
              <p style={{ color: 'var(--text-muted)', marginBottom: '32px' }}>Upload and manage your KESCO base and merged files.</p>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                <div className="glass-card" style={{ padding: '32px', textAlign: 'center' }}>
                  <FileSpreadsheet size={48} color={status.base_loaded ? '#4ADE80' : 'var(--text-muted)'} style={{ margin: '0 auto 16px' }} />
                  <h3 style={{ marginBottom: '8px' }}>Base File</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '24px' }}>{status.base_loaded ? "Loaded Successfully" : "Waiting for upload"}</p>
                  <label className="btn-primary" style={{ cursor: 'pointer' }}>
                    <Upload size={16}/> Upload Base
                    <input type="file" style={{ display: 'none' }} accept=".xlsx" onChange={e => handleUpload(e, 'base')} />
                  </label>
                </div>
                
                <div className="glass-card" style={{ padding: '32px', textAlign: 'center' }}>
                  <FileSpreadsheet size={48} color={status.merged_loaded ? '#4ADE80' : 'var(--text-muted)'} style={{ margin: '0 auto 16px' }} />
                  <h3 style={{ marginBottom: '8px' }}>Merged File</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '24px' }}>{status.merged_loaded ? "Loaded Successfully" : "Waiting for upload"}</p>
                  <label className="btn-primary" style={{ cursor: 'pointer' }}>
                    <Upload size={16}/> Upload Merged
                    <input type="file" style={{ display: 'none' }} accept=".xlsx" onChange={e => handleUpload(e, 'merged')} />
                  </label>
                </div>
              </div>
            </motion.div>
          )}

          {/* ANALYSIS TAB */}
          {activeTab === 'analysis' && (
            <motion.div key="analysis" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <h1 style={{ fontSize: '2rem' }}>Statistical Analysis</h1>
              </div>

              {/* Filters */}
              <div className="glass-card" style={{ padding: '24px', marginBottom: '32px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                  <Filter size={18} color="var(--primary)"/> <h3 style={{ fontSize: '1.1rem' }}>Global Filters</h3>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
                  {['smart_meter', 'govt', 'bill_basis', 'tariff_type'].map(f => (
                    <div key={f}>
                      <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px', display: 'block', textTransform: 'capitalize' }}>{f.replace('_', ' ')}</label>
                      <select className="select-styled" onChange={e => setFilters({...filters, [f]: [e.target.value]})}>
                        <option value="All">All</option>
                        {/* Dummy hardcoded options for simple UI demonstration */}
                        {f==='smart_meter' && <> <option>GENUS</option><option>GP</option><option>LT</option><option>Y</option><option>Others</option> </>}
                        {f==='govt' && <> <option>GOVTTT</option><option>Others</option> </>}
                        {f==='bill_basis' && <> <option>ASS</option><option>CEIL</option><option>MU</option><option>PROV</option><option>Others</option> </>}
                        {f==='tariff_type' && <> <option>HV1</option><option>LMV1</option><option>LMV2</option><option>LMV5</option> </>}
                      </select>
                    </div>
                  ))}
                </div>
              </div>

              {/* Analysis Boards */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
                <div className="glass-card" style={{ padding: '24px' }}>
                  <h3 style={{ marginBottom: '16px' }}>Data Set 1</h3>
                  <select className="select-styled" style={{ marginBottom: '12px' }} value={analysis.f1} onChange={e => setAnalysis({...analysis, f1: e.target.value})}>
                    <option>Select...</option>
                    {status.base_loaded && <option>Base File</option>}
                    {status.merged_loaded && <option>Merged File</option>}
                  </select>
                  <select className="select-styled" style={{ marginBottom: '24px' }} value={analysis.h1} onChange={e => setAnalysis({...analysis, h1: e.target.value})}>
                    <option>Select...</option>
                    {(analysis.f1 === 'Base File' ? status.base_headers : analysis.f1 === 'Merged File' ? status.merged_headers : []).map(h => <option key={h}>{h}</option>)}
                  </select>

                  {tables.t1 && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                      <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                        <table>
                          <thead><tr><th>{analysis.h1}</th><th>Count</th><th>%</th></tr></thead>
                          <tbody>
                            {tables.t1.map((r, i) => (
                              <tr key={i}><td>{r.value}</td><td>{r.count.toLocaleString()}</td><td>{r.percent}</td></tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Total Count:</span> <strong style={{ fontSize: '1.2rem', float: 'right' }}>{tables.d1_total.toLocaleString()}</strong>
                      </div>
                    </motion.div>
                  )}
                </div>

                <div className="glass-card" style={{ padding: '24px' }}>
                  <h3 style={{ marginBottom: '16px' }}>Data Set 2</h3>
                  <select className="select-styled" style={{ marginBottom: '12px' }} value={analysis.f2} onChange={e => setAnalysis({...analysis, f2: e.target.value})}>
                    <option>Select...</option>
                    {status.base_loaded && <option>Base File</option>}
                    {status.merged_loaded && <option>Merged File</option>}
                  </select>
                  <select className="select-styled" style={{ marginBottom: '24px' }} value={analysis.h2} onChange={e => setAnalysis({...analysis, h2: e.target.value})}>
                    <option>Select...</option>
                    {(analysis.f2 === 'Base File' ? status.base_headers : analysis.f2 === 'Merged File' ? status.merged_headers : []).map(h => <option key={h}>{h}</option>)}
                  </select>

                  {tables.t2 && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                      <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                        <table>
                          <thead><tr><th>{analysis.h2}</th><th>Count</th><th>%</th></tr></thead>
                          <tbody>
                            {tables.t2.map((r, i) => (
                              <tr key={i}><td>{r.value}</td><td>{r.count.toLocaleString()}</td><td>{r.percent}</td></tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Total Count:</span> <strong style={{ fontSize: '1.2rem', float: 'right' }}>{tables.d2_total.toLocaleString()}</strong>
                      </div>
                    </motion.div>
                  )}
                </div>
              </div>

              <div className="glass-card" style={{ padding: '24px' }}>
                <h3 style={{ marginBottom: '16px' }}>Operation</h3>
                <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
                  <select className="select-styled" style={{ width: '300px' }} value={operation} onChange={e => setOperation(e.target.value)}>
                    {['Select Operation...', 'D1 ÷ D2 × 100', 'D2 ÷ D1 × 100', 'D1 − D2', 'D2 − D1', 'D1 ÷ D2', 'D2 ÷ D1'].map(o => <option key={o}>{o}</option>)}
                  </select>
                  {renderOperationResult()}
                </div>
              </div>

            </motion.div>
          )}

          {/* RECORDS TAB */}
          {activeTab === 'records' && (
            <motion.div key="records" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
              <h1 style={{ fontSize: '2rem', marginBottom: '8px' }}>Live Record Update</h1>
              <p style={{ color: 'var(--text-muted)', marginBottom: '32px' }}>Search and modify individual records instantly.</p>

              <div className="glass-card" style={{ padding: '24px', marginBottom: '24px' }}>
                <div style={{ display: 'flex', gap: '16px' }}>
                  <input className="input-styled" placeholder="Enter ACCT_ID..." value={searchAcct} onChange={e => setSearchAcct(e.target.value)} />
                  <button className="btn-primary" onClick={handleSearch}><Search size={18}/> Search</button>
                </div>
              </div>

              {record && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card" style={{ padding: '24px' }}>
                  <h3 style={{ marginBottom: '16px' }}>Edit Record</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', marginBottom: '24px' }}>
                    <div>
                      <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px', display: 'block' }}>Field to Update</label>
                      <select className="select-styled" value={updateField} onChange={e => setUpdateField(e.target.value)}>
                        <option>Select...</option>
                        {Object.keys(record).map(k => <option key={k}>{k}</option>)}
                      </select>
                    </div>
                    <div>
                      <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px', display: 'block' }}>Current Value</label>
                      <input className="input-styled" disabled value={updateField && record[updateField] ? record[updateField] : ''} />
                    </div>
                    <div>
                      <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px', display: 'block' }}>New Value</label>
                      <input className="input-styled" value={updateValue} onChange={e => setUpdateValue(e.target.value)} />
                    </div>
                  </div>
                  <button className="btn-primary" style={{ background: '#4ADE80', color: '#0F172A' }} onClick={handleUpdate}>
                    <Check size={18}/> Confirm Update
                  </button>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default App;
