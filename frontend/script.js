import React, { useState } from 'react';
import { 
  ShieldAlert, 
  FileText, 
  Cpu, 
  AlertTriangle, 
  UploadCloud, 
  Activity, 
  DollarSign, 
  RefreshCw,
  Layers,
  Sun,
  Moon
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Sample data for the Savings & Anomalies chart
const chartData = [
  { month: 'Jan', savings: 4000, anomalies: 24 },
  { month: 'Feb', savings: 3000, anomalies: 18 },
  { month: 'Mar', savings: 5000, anomalies: 29 },
  { month: 'Apr', savings: 8000, anomalies: 42 },
  { month: 'May', savings: 6000, anomalies: 33 },
  { month: 'Jun', savings: 9500, anomalies: 38 },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [darkMode, setDarkMode] = useState(false); // Default is Light Theme
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [auditResult, setAuditResult] = useState(null);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file.name);
      setIsAnalyzing(true);
      setAuditResult(null);

      setTimeout(() => {
        setIsAnalyzing(false);
        setAuditResult({
          invoiceId: "INV-2026-9482",
          vendor: "Global Logistics & Supplies Corp.",
          amount: "$14,850.00",
          riskScore: "High Risk (87%)",
          anomaliesDetected: 2,
          agentsTriggered: ["OCR Extractor Agent", "Tax Compliance Agent", "Duplicate Check Agent", "Anomaly & Fraud Detector"],
          findings: [
            { type: "Warning", message: "Potential duplicate invoice detected: matches INV-2026-9411 paid 14 days ago." },
            { type: "Alert", message: "Line item unit price deviates +24% from historical vendor benchmark." }
          ]
        });
      }, 3000);
    }
  };

  return (
    <div className={`min-h-screen flex font-sans transition-colors duration-300 ${darkMode ? 'bg-slate-950 text-slate-100' : 'bg-slate-50 text-slate-800'}`}>
      
      {/* SIDEBAR NAVIGATION */}
      <aside className={`w-64 border-r p-6 flex flex-col justify-between hidden md:flex transition-colors duration-300 ${darkMode ? 'border-slate-800 bg-slate-900/50' : 'border-slate-200 bg-white shadow-sm'}`}>
        <div>
          <div className="flex items-center gap-3 mb-10">
            <div className="p-2.5 bg-indigo-600 rounded-xl shadow-lg shadow-indigo-500/20 text-white">
              <ShieldAlert size={24} />
            </div>
            <div>
              <h1 className="font-bold text-xl tracking-wide bg-gradient-to-r from-indigo-500 to-cyan-500 bg-clip-text text-transparent">AuditX</h1>
              <p className={`text-xs font-medium ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>Multi-Agent Auditor</p>
            </div>
          </div>

          <nav className="space-y-2">
            <button 
              onClick={() => setActiveTab('dashboard')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'dashboard' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30' : darkMode ? 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}`}
            >
              <Activity size={18} /> Dashboard
            </button>
            <button 
              onClick={() => setActiveTab('upload')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'upload' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30' : darkMode ? 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}`}
            >
              <UploadCloud size={18} /> New Audit
            </button>
            <button 
              onClick={() => setActiveTab('agents')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === 'agents' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30' : darkMode ? 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}`}
            >
              <Cpu size={18} /> Agent Swarm
            </button>
          </nav>
        </div>

        <div className={`p-4 rounded-xl border ${darkMode ? 'bg-slate-800/50 border-slate-700/50' : 'bg-slate-50 border-slate-200'}`}>
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-500 mb-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> All Agents Online
          </div>
          <p className={`text-xs ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>Connected to Backend Node</p>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        
        {/* TOP HEADER */}
        <header className={`h-20 border-b px-8 flex items-center justify-between backdrop-blur-md sticky top-0 z-10 transition-colors duration-300 ${darkMode ? 'border-slate-800 bg-slate-900/30' : 'border-slate-200 bg-white/70'}`}>
          <div className="flex items-center gap-4">
            <h2 className={`text-lg font-semibold capitalize ${darkMode ? 'text-slate-200' : 'text-slate-800'}`}>
              {activeTab === 'dashboard' && 'System Overview & Metrics'}
              {activeTab === 'upload' && 'Invoice Audit & Extraction Studio'}
              {activeTab === 'agents' && 'Multi-Agent Pipeline Status'}
            </h2>
          </div>
          
          <div className="flex items-center gap-4">
            <span className="px-3 py-1 bg-indigo-500/10 border border-indigo-500/20 text-indigo-500 rounded-full text-xs font-semibold">
              Branch: sania-frontend
            </span>

            {/* THEME TOGGLE BUTTON */}
            <button 
              onClick={() => setDarkMode(!darkMode)}
              className={`p-2.5 rounded-xl border transition-all ${darkMode ? 'bg-slate-800 border-slate-700 text-amber-400 hover:bg-slate-700' : 'bg-white border-slate-200 text-slate-700 shadow-sm hover:bg-slate-100'}`}
              title="Toggle Theme"
            >
              {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </div>
        </header>

        {/* CONTENT DYNAMIC SECTIONS */}
        <div className="p-8 max-w-7xl mx-auto w-full space-y-8">

          {activeTab === 'dashboard' && (
            <>
              {/* METRIC CARDS */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                  { title: "Total Audited", value: "1,284", icon: <FileText size={20} />, change: "↑ 12% from last week", color: "text-indigo-500" },
                  { title: "Anomalies Flagged", value: "42", icon: <AlertTriangle size={20} />, change: "Requires Review", color: "text-rose-500" },
                  { title: "Potential Savings", value: "$64,200", icon: <DollarSign size={20} />, change: "Prevented duplicate payouts", color: "text-emerald-500" },
                  { title: "Active Agents", value: "4 / 4", icon: <Cpu size={20} />, change: "Fully operational swarm", color: "text-cyan-500" }
                ].map((stat, i) => (
                  <div key={i} className={`p-6 rounded-2xl border shadow-xl transition-colors duration-300 ${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200 shadow-sm'}`}>
                    <div className="flex items-center justify-between mb-4">
                      <span className={`text-sm font-medium ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>{stat.title}</span>
                      <div className={`p-2.5 rounded-xl bg-slate-500/10 ${stat.color}`}>{stat.icon}</div>
                    </div>
                    <div className={`text-3xl font-bold ${darkMode ? 'text-slate-100' : 'text-slate-900'}`}>{stat.value}</div>
                    <div className={`text-xs mt-2 font-medium ${stat.color}`}>{stat.change}</div>
                  </div>
                ))}
              </div>

              {/* INTEGRATED SAVINGS CHART */}
              <div className={`p-6 rounded-2xl border shadow-xl transition-colors duration-300 ${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200 shadow-sm'}`}>
                <h3 className={`text-base font-semibold mb-6 ${darkMode ? 'text-slate-200' : 'text-slate-800'}`}>
                  Monthly Potential Savings & Cost Reductions ($)
                </h3>
                <div className="h-80 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#1e293b' : '#e2e8f0'} />
                      <XAxis dataKey="month" stroke={darkMode ? '#94a3b8' : '#64748b'} fontSize={12} tickLine={false} />
                      <YAxis stroke={darkMode ? '#94a3b8' : '#64748b'} fontSize={12} tickLine={false} axisLine={false} />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: darkMode ? '#0f172a' : '#ffffff', 
                          border: darkMode ? '1px solid #334155' : '1px solid #cbd5e1', 
                          borderRadius: '8px',
                          color: darkMode ? '#f1f5f9' : '#0f172a'
                        }} 
                      />
                      <defs>
                        <linearGradient id="colorSavings" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <Area type="monotone" dataKey="savings" stroke="#6366f1" fillOpacity={1} fill="url(#colorSavings)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* RECENT AUDITS TABLE */}
              <div className={`border rounded-2xl p-6 shadow-xl transition-colors duration-300 ${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200 shadow-sm'}`}>
                <h3 className={`text-base font-semibold mb-6 flex items-center gap-2 ${darkMode ? 'text-slate-200' : 'text-slate-800'}`}>
                  <Layers size={18} className="text-indigo-500" /> Recent Auditing History
                </h3>
                <div className="overflow-x-auto">
                  <table className={`w-full text-left text-sm ${darkMode ? 'text-slate-300' : 'text-slate-600'}`}>
                    <thead className={`border-b text-xs uppercase ${darkMode ? 'border-slate-800 text-slate-400' : 'border-slate-100 text-slate-400'}`}>
                      <tr>
                        <th className="pb-3 font-semibold">Invoice ID</th>
                        <th className="pb-3 font-semibold">Vendor Name</th>
                        <th className="pb-3 font-semibold">Amount</th>
                        <th className="pb-3 font-semibold">Status</th>
                        <th className="pb-3 font-semibold">Timestamp</th>
                      </tr>
                    </thead>
                    <tbody className={`divide-y ${darkMode ? 'divide-slate-800/60' : 'divide-slate-100'}`}>
                      <tr>
                        <td className={`py-4 font-medium ${darkMode ? 'text-slate-200' : 'text-slate-900'}`}>INV-2026-9481</td>
                        <td className="py-4">Apex Cloud Services</td>
                        <td className="py-4 font-mono">$3,420.00</td>
                        <td className="py-4"><span className="px-2.5 py-1 bg-emerald-500/10 text-emerald-500 rounded-full text-xs font-semibold">Passed</span></td>
                        <td className={`py-4 ${darkMode ? 'text-slate-400' : 'text-slate-400'}`}>10 mins ago</td>
                      </tr>
                      <tr>
                        <td className={`py-4 font-medium ${darkMode ? 'text-slate-200' : 'text-slate-900'}`}>INV-2026-9480</td>
                        <td className="py-4">Metro Office Supplies</td>
                        <td className="py-4 font-mono">$1,150.50</td>
                        <td className="py-4"><span className="px-2.5 py-1 bg-rose-500/10 text-rose-500 rounded-full text-xs font-semibold">Flagged</span></td>
                        <td className={`py-4 ${darkMode ? 'text-slate-400' : 'text-slate-400'}`}>1 hour ago</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}

          {activeTab === 'upload' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className={`border rounded-2xl p-8 shadow-xl flex flex-col justify-center items-center text-center transition-colors duration-300 ${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200 shadow-sm'}`}>
                <div className="w-16 h-16 bg-indigo-500/10 text-indigo-500 rounded-2xl flex items-center justify-center mb-6 border border-indigo-500/20">
                  <UploadCloud size={32} />
                </div>
                <h3 className={`text-xl font-bold mb-2 ${darkMode ? 'text-slate-100' : 'text-slate-900'}`}>Upload Invoice Document</h3>
                <p className={`text-sm mb-6 max-w-sm ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
                  Drag and drop your PDF or image invoice here to trigger multi-agent auditing and anomaly detection.
                </p>
                <label className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl shadow-lg shadow-indigo-600/30 cursor-pointer transition-all">
                  Browse Files
                  <input type="file" className="hidden" onChange={handleFileUpload} accept=".pdf,.png,.jpg,.jpeg" />
                </label>
                {selectedFile && (
                  <p className={`mt-4 text-xs font-medium ${darkMode ? 'text-slate-300' : 'text-slate-600'}`}>Selected: {selectedFile}</p>
                )}
              </div>

              <div className={`border rounded-2xl p-8 shadow-xl flex flex-col justify-between transition-colors duration-300 ${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200 shadow-sm'}`}>
                <div>
                  <h3 className={`text-lg font-bold mb-6 flex items-center gap-2 ${darkMode ? 'text-slate-100' : 'text-slate-900'}`}>
                    <Activity className="text-indigo-500" size={20} /> Multi-Agent Audit Log
                  </h3>

                  {isAnalyzing && (
                    <div className="flex flex-col items-center justify-center py-16 space-y-4">
                      <RefreshCw className="animate-spin text-indigo-500" size={36} />
                      <p className={`text-sm font-medium ${darkMode ? 'text-slate-300' : 'text-slate-600'}`}>Agents collaborating & verifying line items...</p>
                    </div>
                  )}

                  {!isAnalyzing && !auditResult && (
                    <div className="flex flex-col items-center justify-center py-16 text-slate-400 text-center">
                      <FileText size={40} className="mb-3 opacity-40" />
                      <p className="text-sm">Upload an invoice on the left to begin the multi-agent inspection workflow.</p>
                    </div>
                  )}

                  {!isAnalyzing && auditResult && (
                    <div className="space-y-6">
                      <div className={`p-4 rounded-xl border ${darkMode ? 'bg-slate-800/50 border-slate-700/50' : 'bg-slate-50 border-slate-200'}`}>
                        <div>
                          <p className="text-xs text-slate-400">Invoice Reference</p>
                          <p className={`font-bold ${darkMode ? 'text-slate-200' : 'text-slate-900'}`}>{auditResult.invoiceId}</p>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Audit Findings</p>
                        {auditResult.findings.map((f, i) => (
                          <div key={i} className="p-3 bg-rose-500/5 border border-rose-500/20 rounded-xl flex items-start gap-3 text-sm text-rose-500">
                            <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                            <span>{f.message}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'agents' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                { name: "OCR Extraction Agent", role: "Parses structured table items, vendor details, and totals from raw PDFs/Images.", status: "Active" },
                { name: "Tax Compliance Agent", role: "Cross-checks VAT/GST percentages against regional tax laws.", status: "Active" },
                { name: "Duplicate Detection Agent", role: "Scans vector database for duplicate invoices or historical overlapping line items.", status: "Active" },
                { name: "Fraud & Anomaly Detector", role: "Calculates outlier risk scores based on pricing benchmarks.", status: "Active" }
              ].map((agent, i) => (
                <div key={i} className={`p-6 border rounded-2xl shadow-xl flex flex-col justify-between transition-colors duration-300 ${darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200 shadow-sm'}`}>
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h4 className={`font-bold text-base ${darkMode ? 'text-slate-200' : 'text-slate-900'}`}>{agent.name}</h4>
                      <span className="px-2.5 py-1 bg-emerald-500/10 text-emerald-500 rounded-full text-xs font-semibold flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> {agent.status}
                      </span>
                    </div>
                    <p className={`text-sm leading-relaxed mb-6 ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>{agent.role}</p>
                  </div>
                  <div className={`pt-4 border-t flex items-center justify-between text-xs font-mono ${darkMode ? 'border-slate-800 text-slate-500' : 'border-slate-100 text-slate-400'}`}>
                    <span>Model: LLM + LangGraph</span>
                    <span>Status: Healthy</span>
                  </div>
                </div>
              ))}
            </div>
          )}

        </div>
      </main>
    </div>
  );
}