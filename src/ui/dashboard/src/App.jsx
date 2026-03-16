import React, { useState, useEffect } from 'react';
import {
  Shield,
  ShieldAlert,
  Activity,
  LogOut,
  User,
  Lock,
  AlertTriangle,
  Search,
  Filter,
  CheckCircle,
  Clock,
  Server,
  Bell,
  MoreVertical,
  Zap,
  TrendingUp,
  LayoutDashboard,
  TerminalSquare,
  Network,
  Settings,
  Menu
} from 'lucide-react';

const initialIncidents = [
  { id: 'INC-2041', severity: 'Critical', score: 98, mitre: 'T1486 Data Encrypted', ip: '10.0.0.52', desc: 'Ransomware encryption pattern detected via EDR telemetry', status: 'Open', time: '10:42 AM', assignee: null },
  { id: 'INC-2042', severity: 'High', score: 85, mitre: 'T1110 Brute Force', ip: '192.168.1.105', desc: 'Multiple failed SSH login attempts from external origin', status: 'Investigating', time: '10:38 AM', assignee: 'AJ' },
  { id: 'INC-2043', severity: 'Medium', score: 62, mitre: 'T1071 Standard Port', ip: '172.16.0.8', desc: 'Unusual outbound traffic beaconing to known malicious C2 IP', status: 'Open', time: '10:15 AM', assignee: null },
  { id: 'INC-2044', severity: 'Low', score: 25, mitre: 'T1046 Network Service', ip: '192.168.1.200', desc: 'Internal port scan detected originating from guest VLAN', status: 'Resolved', time: '09:05 AM', assignee: 'KL' },
  { id: 'INC-2045', severity: 'High', score: 78, mitre: 'T1068 Exploitation', ip: '10.0.0.19', desc: 'Privilege escalation attempt detected on critical database server', status: 'Open', time: '08:50 AM', assignee: 'AJ' },
];

export default function App() {
  const [userRole, setUserRole] = useState(null);
  const [incidents, setIncidents] = useState(initialIncidents);
  const [searchTerm, setSearchTerm] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const handleLogout = () => {
    setUserRole(null);
  };

  useEffect(() => {
    if (!userRole) return;

    const interval = setInterval(() => {
      const severities = ['Critical', 'High', 'Medium', 'Low'];
      const randomSeverity = severities[Math.floor(Math.random() * 4)];
      const baseScores = { Critical: 90, High: 70, Medium: 40, Low: 10 };

      const newIncident = {
        id: `INC-${Math.floor(Math.random() * 1000) + 2046}`,
        severity: randomSeverity,
        score: baseScores[randomSeverity] + Math.floor(Math.random() * 10),
        mitre: 'T1204 User Execution',
        ip: `192.168.1.${Math.floor(Math.random() * 255)}`,
        desc: 'Suspicious payload behavior detected by advanced behavioral analytics',
        status: 'Open',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        assignee: null
      };

      setIncidents((prev) => [newIncident, ...prev].slice(0, 15));
    }, 12000);

    return () => clearInterval(interval);
  }, [userRole]);

  const filteredIncidents = incidents.filter((inc) =>
    inc.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    inc.ip.includes(searchTerm) ||
    inc.desc.toLowerCase().includes(searchTerm.toLowerCase()) ||
    inc.mitre.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const SeverityBadge = ({ severity }) => {
    const styles = {
      Critical: 'bg-rose-500/10 text-rose-500 border-rose-500/20 shadow-[0_0_10px_rgba(244,63,94,0.2)]',
      High: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
      Medium: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
      Low: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    };
    return (
      <span className={`px-2.5 py-1 inline-flex text-xs font-semibold rounded-md border ${styles[severity]}`}>
        {severity}
      </span>
    );
  };

  const ThreatScoreBar = ({ score }) => {
    let colorClass = 'bg-blue-500';
    let textColorClass = 'text-blue-500';
    if (score >= 80) {
      colorClass = 'bg-rose-500';
      textColorClass = 'text-rose-500';
    } else if (score >= 60) {
      colorClass = 'bg-orange-500';
      textColorClass = 'text-orange-500';
    } else if (score >= 40) {
      colorClass = 'bg-amber-500';
      textColorClass = 'text-amber-500';
    }

    return (
      <div className="flex items-center space-x-2">
        <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div className={`h-full ${colorClass} transition-all duration-500`} style={{ width: `${score}%` }} />
        </div>
        <span className={`text-xs font-mono font-medium ${textColorClass}`}>{score}</span>
      </div>
    );
  };

  if (!userRole) {
    return (
      <div className="min-h-screen bg-[#0B1120] flex items-center justify-center font-sans relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTAgMGg0MHY0MEgwVjB6bTIwIDIwaDIwdjIwSDIwdi0yMHpNMCAwaDIwdjIwSDBWMHoiIGZpbGw9IiMxZTI5M2IiIGZpbGwtb3BhY2l0eT0iMC4wNSIgZmlsbC1ydWxlPSJldmVub2RkIi8+PC9zdmc+')] opacity-20" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-rose-600/10 rounded-full blur-[120px]" />

        <div className="bg-[#0F172A]/80 backdrop-blur-xl p-10 rounded-2xl border border-slate-800/60 shadow-2xl w-full max-w-md relative z-10">
          <div className="flex flex-col items-center mb-10">
            <div className="relative mb-4">
              <div className="absolute inset-0 bg-blue-500 blur-lg opacity-20 rounded-full" />
              <div className="bg-gradient-to-br from-slate-800 to-slate-900 p-4 rounded-xl border border-slate-700 relative">
                <Shield className="w-10 h-10 text-blue-500" />
              </div>
            </div>
            <h1 className="text-3xl font-bold text-white tracking-tight">AGNI SOAR</h1>
            <p className="text-slate-400 text-sm mt-2">Enterprise Security Orchestration</p>
          </div>

          <div className="space-y-5">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Authentication ID</label>
              <div className="relative group">
                <User className="absolute left-3 top-3 text-slate-500 w-5 h-5 group-focus-within:text-blue-500 transition-colors" />
                <input
                  type="text"
                  className="w-full bg-slate-900/50 border border-slate-700 rounded-lg py-2.5 pl-10 pr-4 text-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-slate-600"
                  defaultValue="sec_ops_demo"
                />
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Access Token</label>
              <div className="relative group">
                <Lock className="absolute left-3 top-3 text-slate-500 w-5 h-5 group-focus-within:text-blue-500 transition-colors" />
                <input
                  type="password"
                  className="w-full bg-slate-900/50 border border-slate-700 rounded-lg py-2.5 pl-10 pr-4 text-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-slate-600"
                  defaultValue="************"
                />
              </div>
            </div>

            <div className="pt-6 grid grid-cols-2 gap-4">
              <button
                onClick={() => setUserRole('analyst')}
                className="w-full bg-slate-800 hover:bg-slate-700 text-white font-medium py-2.5 px-4 rounded-lg transition-all border border-slate-700 hover:border-slate-600 flex items-center justify-center shadow-lg"
              >
                Analyst Portal
              </button>
              <button
                onClick={() => setUserRole('admin')}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2.5 px-4 rounded-lg transition-all shadow-[0_0_15px_rgba(37,99,235,0.3)] hover:shadow-[0_0_20px_rgba(37,99,235,0.5)] flex items-center justify-center"
              >
                Admin Gateway
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B1120] font-sans text-slate-300 flex overflow-hidden selection:bg-blue-500/30">
      <aside className={`bg-[#0F172A] border-r border-slate-800 transition-all duration-300 flex flex-col ${isSidebarOpen ? 'w-64' : 'w-20'} relative z-20`}>
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800">
          <div className="flex items-center space-x-3 overflow-hidden">
            <ShieldAlert className="w-8 h-8 text-blue-500 flex-shrink-0" />
            {isSidebarOpen && <span className="text-lg font-bold text-white tracking-wide whitespace-nowrap">AGNI SOAR</span>}
          </div>
        </div>

        <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
          {[
            { icon: LayoutDashboard, label: 'Dashboard', active: true },
            { icon: ShieldAlert, label: 'Incidents', badge: incidents.filter((i) => i.status === 'Open').length },
            { icon: TerminalSquare, label: 'Playbooks' },
            { icon: Network, label: 'Threat Intel' },
          ].map((item, idx) => (
            <button key={idx} className={`w-full flex items-center ${isSidebarOpen ? 'justify-between' : 'justify-center'} px-3 py-2.5 rounded-lg transition-colors ${item.active ? 'bg-blue-600/10 text-blue-400' : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'}`}>
              <div className="flex items-center">
                <item.icon size={20} className={item.active ? 'text-blue-500' : ''} />
                {isSidebarOpen && <span className="ml-3 font-medium text-sm">{item.label}</span>}
              </div>
              {isSidebarOpen && item.badge && (
                <span className="bg-rose-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">{item.badge}</span>
              )}
            </button>
          ))}

          <div className="pt-8 pb-2">
            {isSidebarOpen && <p className="px-4 text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">Administration</p>}
            {[
              { icon: Server, label: 'Connectors' },
              { icon: Settings, label: 'Settings' },
            ].map((item, idx) => (
              <button key={idx} className={`w-full flex items-center ${isSidebarOpen ? 'justify-start' : 'justify-center'} px-3 py-2.5 rounded-lg text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 transition-colors`}>
                <item.icon size={20} />
                {isSidebarOpen && <span className="ml-3 font-medium text-sm">{item.label}</span>}
              </button>
            ))}
          </div>
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className={`flex items-center ${isSidebarOpen ? 'justify-between' : 'justify-center'}`}>
            <div className="flex items-center overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-cyan-600 flex items-center justify-center text-white font-bold text-xs flex-shrink-0">
                {userRole === 'admin' ? 'AD' : 'AN'}
              </div>
              {isSidebarOpen && (
                <div className="ml-3">
                  <p className="text-sm font-medium text-white capitalize">{userRole}</p>
                  <p className="text-xs text-slate-500">Active Session</p>
                </div>
              )}
            </div>
            {isSidebarOpen && (
              <button onClick={handleLogout} className="text-slate-500 hover:text-rose-400 transition-colors">
                <LogOut size={18} />
              </button>
            )}
          </div>
        </div>
      </aside>

      <main className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden relative">
        <header className="h-16 bg-[#0B1120]/80 backdrop-blur-md border-b border-slate-800 flex items-center justify-between px-6 sticky top-0 z-10">
          <div className="flex items-center space-x-4">
            <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="text-slate-400 hover:text-white transition-colors">
              <Menu size={20} />
            </button>
            <div className="h-4 w-px bg-slate-700"></div>
            <h2 className="text-lg font-semibold text-white tracking-tight flex items-center">
              Active Incidents
              <span className="ml-3 px-2 py-0.5 bg-emerald-500/10 text-emerald-400 text-xs rounded-full border border-emerald-500/20 flex items-center">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full mr-1.5 animate-pulse"></span>
                Live
              </span>
            </h2>
          </div>

          <div className="flex items-center space-x-5">
            <div className="relative group">
              <Search className="absolute left-3 top-2 text-slate-500 w-4 h-4 group-focus-within:text-blue-500 transition-colors" />
              <input
                type="text"
                placeholder="Search IoCs, IDs, descriptions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-72 max-w-[45vw] bg-[#0F172A] border border-slate-700 rounded-lg py-1.5 pl-9 pr-4 text-sm text-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-slate-500 shadow-inner"
              />
            </div>
            <button className="relative text-slate-400 hover:text-white transition-colors">
              <Bell size={20} />
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-rose-500 border-2 border-[#0B1120] rounded-full"></span>
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {[
              { label: 'Unresolved Alerts', value: incidents.filter((i) => i.status !== 'Resolved').length, icon: Activity, color: 'blue', textClass: 'text-blue-400', bgClass: 'bg-blue-500/5', trend: '+12%', trendUp: true },
              { label: 'Critical Severity', value: incidents.filter((i) => i.severity === 'Critical').length, icon: ShieldAlert, color: 'rose', textClass: 'text-rose-400', bgClass: 'bg-rose-500/5', trend: '+2', trendUp: true },
              { label: 'Avg Triage Time', value: '14m', icon: Clock, color: 'amber', textClass: 'text-amber-400', bgClass: 'bg-amber-500/5', trend: '-3m', trendUp: false },
              { label: 'Automated Actions', value: '1,842', icon: Zap, color: 'emerald', textClass: 'text-emerald-400', bgClass: 'bg-emerald-500/5', trend: '+18%', trendUp: true },
            ].map((kpi, idx) => (
              <div key={idx} className="bg-[#0F172A] border border-slate-800 rounded-xl p-5 relative overflow-hidden group hover:border-slate-700 transition-colors shadow-sm">
                <div className={`absolute top-0 right-0 w-24 h-24 ${kpi.bgClass} rounded-bl-full -mr-8 -mt-8 transition-transform group-hover:scale-110`}></div>
                <div className="flex justify-between items-start relative z-10">
                  <div>
                    <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">{kpi.label}</p>
                    <div className="flex items-baseline space-x-2">
                      <h3 className="text-3xl font-bold text-white">{kpi.value}</h3>
                      <span className={`text-xs font-medium flex items-center ${kpi.trendUp ? (kpi.color === 'rose' ? 'text-rose-400' : 'text-emerald-400') : 'text-emerald-400'}`}>
                        {kpi.trendUp ? <TrendingUp size={12} className="mr-0.5" /> : <TrendingUp size={12} className="mr-0.5 transform rotate-180" />}
                        {kpi.trend}
                      </span>
                    </div>
                  </div>
                  <div className={`bg-[#0B1120] border border-slate-800 p-2.5 rounded-lg ${kpi.textClass} shadow-inner`}>
                    <kpi.icon size={20} />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-[#0F172A] border border-slate-800 rounded-xl shadow-lg flex flex-col h-[calc(100vh-280px)] min-h-[400px]">
            <div className="px-5 py-4 border-b border-slate-800 flex justify-between items-center bg-[#0F172A] rounded-t-xl z-10">
              <div className="flex space-x-2">
                <button className="bg-[#0B1120] border border-slate-700 hover:border-slate-500 text-slate-300 px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center shadow-sm">
                  <Filter size={14} className="mr-1.5 text-slate-400" /> Filter
                </button>
                <button className="bg-[#0B1120] border border-slate-700 hover:border-slate-500 text-slate-300 px-3 py-1.5 rounded-md text-xs font-medium transition-colors shadow-sm">
                  Status: All Open
                </button>
              </div>
              <div className="flex space-x-3">
                {userRole === 'admin' && (
                  <button className="bg-slate-800 hover:bg-slate-700 text-white px-3 py-1.5 rounded-md text-xs font-medium transition-colors border border-slate-700 shadow-sm">
                    Export CSV
                  </button>
                )}
                <button className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-1.5 rounded-md text-xs font-medium transition-colors shadow-[0_0_10px_rgba(37,99,235,0.2)] flex items-center">
                  <Zap size={14} className="mr-1.5" /> Run Playbook
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-auto relative">
              <table className="w-full text-left border-collapse">
                <thead className="sticky top-0 bg-[#0F172A] border-b border-slate-800 z-10 shadow-sm">
                  <tr className="text-slate-400 text-[10px] uppercase tracking-widest font-semibold">
                    <th className="px-5 py-3 w-10 text-center"><input type="checkbox" className="rounded bg-slate-900 border-slate-700 text-blue-500 focus:ring-blue-500/30" /></th>
                    <th className="px-5 py-3">Incident ID</th>
                    <th className="px-5 py-3">Severity</th>
                    <th className="px-5 py-3">Threat Score</th>
                    <th className="px-5 py-3">Source IP & MITRE</th>
                    <th className="px-5 py-3">Description</th>
                    <th className="px-5 py-3">Assignee & Status</th>
                    <th className="px-5 py-3 text-right">Time</th>
                    <th className="px-5 py-3 w-12 text-center"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredIncidents.length === 0 ? (
                    <tr>
                      <td colSpan="9" className="px-6 py-16 text-center">
                        <Shield className="w-12 h-12 text-slate-700 mx-auto mb-3" />
                        <p className="text-slate-400 text-sm">No security incidents match your criteria.</p>
                      </td>
                    </tr>
                  ) : (
                    filteredIncidents.map((incident) => (
                      <tr
                        key={incident.id}
                        className="hover:bg-[#151E32] transition-colors group cursor-pointer"
                      >
                        <td className="px-5 py-4 text-center">
                          <input type="checkbox" className="rounded bg-slate-900 border-slate-700 text-blue-500 focus:ring-blue-500/30 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <div className="text-sm font-bold text-slate-200">{incident.id}</div>
                          <div className="text-[10px] text-slate-500 uppercase tracking-wider mt-0.5 font-mono">EDR-Alert</div>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <SeverityBadge severity={incident.severity} />
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap w-40">
                          <ThreatScoreBar score={incident.score} />
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <div className="text-sm text-slate-300 font-mono tracking-tight">{incident.ip}</div>
                          <div className="text-[10px] text-slate-500 mt-0.5 truncate max-w-[150px]">{incident.mitre}</div>
                        </td>
                        <td className="px-5 py-4">
                          <p
                            className="text-sm text-slate-300 max-w-md pr-4 leading-relaxed overflow-hidden"
                            style={{
                              display: '-webkit-box',
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: 'vertical'
                            }}
                          >
                            {incident.desc}
                          </p>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-3">
                            {incident.assignee ? (
                              <div className="w-6 h-6 rounded-full bg-slate-700 text-slate-300 text-[10px] font-bold flex items-center justify-center border border-slate-600">
                                {incident.assignee}
                              </div>
                            ) : (
                              <div className="w-6 h-6 rounded-full border border-dashed border-slate-600 flex items-center justify-center text-slate-600 hover:border-slate-400 hover:text-slate-400 transition-colors">
                                +
                              </div>
                            )}
                            <span className={`text-xs font-medium flex items-center ${
                              incident.status === 'Open' ? 'text-rose-400' :
                              incident.status === 'Investigating' ? 'text-amber-400' :
                              'text-slate-400'
                            }`}>
                              {incident.status === 'Open' ? <AlertTriangle size={12} className="mr-1" /> :
                               incident.status === 'Investigating' ? <Clock size={12} className="mr-1" /> :
                               <CheckCircle size={12} className="mr-1" />}
                              {incident.status}
                            </span>
                          </div>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap text-xs text-slate-500 text-right font-medium">
                          {incident.time}
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap text-center">
                          <button className="text-slate-500 hover:text-white transition-colors p-1 rounded hover:bg-slate-700">
                            <MoreVertical size={16} />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
