import React, { useState } from 'react';
import { 
  LayoutDashboard, 
  Settings, 
  User, 
  Menu, 
  Bell, 
  Database, 
  Activity, 
  Clock, 
  ShieldCheck 
} from 'lucide-react';

// --- REUSABLE KPI CARD COMPONENT ---
const KpiCard = ({ title, value, Icon, colorClass, bgClass }) => (
  <div className="flex items-center p-6 bg-white border border-gray-200 rounded-xl shadow-sm">
    <div className={`flex items-center justify-center w-14 h-14 rounded-full ${bgClass} ${colorClass} mr-4`}>
      <Icon className="w-7 h-7" />
    </div>
    <div>
      <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">{title}</p>
      <h4 className="text-2xl font-bold text-gray-900 mt-1">{value}</h4>
    </div>
  </div>
);

export default function DashboardShell() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Navigation Data
  const navItems = [
    { name: 'Dashboard', icon: LayoutDashboard, active: true },
    { name: 'Profile', icon: User, active: false },
    { name: 'Settings', icon: Settings, active: false },
  ];

  // KPI Data
  const kpiData = [
    { title: "Total Records", value: "19,100", Icon: Database, colorClass: "text-blue-600", bgClass: "bg-blue-50" },
    { title: "Processing Speed", value: "1.4s", Icon: Activity, colorClass: "text-indigo-600", bgClass: "bg-indigo-50" },
    { title: "Uptime", value: "99.9%", Icon: Clock, colorClass: "text-purple-600", bgClass: "bg-purple-50" },
    { title: "Data Integrity", value: "Pass", Icon: ShieldCheck, colorClass: "text-emerald-600", bgClass: "bg-emerald-50" },
  ];

  return (
    <div className="flex h-screen w-full bg-gray-50 font-sans text-gray-900">
      
      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 z-20 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Fixed Left Sidebar */}
      <aside 
        className={`fixed inset-y-0 left-0 z-30 w-64 transform bg-slate-900 text-white transition-transform duration-300 ease-in-out lg:static lg:translate-x-0 ${
          isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-16 items-center justify-center border-b border-slate-800">
          <h1 className="text-xl font-bold tracking-wider">PIPELINE OS</h1>
        </div>
        
        <nav className="mt-6 px-4 space-y-2">
          {navItems.map((item) => (
            <a
              key={item.name}
              href="#"
              className={`flex items-center gap-3 rounded-lg px-4 py-3 transition-colors ${
                item.active 
                  ? 'bg-blue-600 text-white' 
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <item.icon className="h-5 w-5" />
              <span className="font-medium">{item.name}</span>
            </a>
          ))}
        </nav>
      </aside>

      {/* Main Content Wrapper */}
      <div className="flex flex-1 flex-col overflow-hidden">
        
        {/* Top Header Navbar */}
        <header className="flex h-16 items-center justify-between border-b bg-white px-6 shadow-sm z-10 flex-shrink-0">
          <div className="flex items-center">
            <button
              onClick={() => setIsMobileMenuOpen(true)}
              className="mr-4 text-gray-500 hover:text-gray-700 focus:outline-none lg:hidden"
            >
              <Menu className="h-6 w-6" />
            </button>
            <h2 className="text-xl font-semibold text-gray-800">Executive Overview</h2>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              System Online
            </div>
            <button className="text-gray-400 hover:text-gray-600 ml-2">
              <Bell className="h-5 w-5" />
            </button>
            <div className="h-9 w-9 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold border border-blue-200">
              SB
            </div>
          </div>
        </header>

        {/* Scrollable Main Content Area */}
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
          <div className="mx-auto max-w-7xl">
            
            {/* The Responsive KPI Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-6">
              {kpiData.map((kpi, index) => (
                <KpiCard 
                  key={index}
                  title={kpi.title}
                  value={kpi.value}
                  Icon={kpi.Icon}
                  colorClass={kpi.colorClass}
                  bgClass={kpi.bgClass}
                />
              ))}
            </div>

            {/* Wireframe Placeholder for Main Layout (Charts & Briefing) */}
            <div className="flex flex-col lg:flex-row gap-6 min-h-[500px]">
              <div className="flex-[2.5] rounded-xl bg-white border border-gray-200 shadow-sm p-6 flex flex-col items-center justify-center text-slate-400">
                <span className="text-lg font-medium mb-2">Main Chart Area</span>
                <span>(Recharts component will go here)</span>
              </div>
              <div className="flex-1 rounded-xl bg-white border border-gray-200 shadow-sm p-6 flex flex-col items-center justify-center text-slate-400">
                <span className="text-lg font-medium mb-2">Weekly Briefing Side Panel</span>
                <span>(Alerts and summaries will go here)</span>
              </div>
            </div>

          </div>
        </main>

      </div>
    </div>
  );
}