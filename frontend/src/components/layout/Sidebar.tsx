import { NavLink } from 'react-router-dom';
import { Database, GitBranch, Activity, Compass } from 'lucide-react';
import { cn } from '../../utils/cn';

const navItems = [
  { to: '/datasets', icon: Database, label: 'Datasets' },
  { to: '/pipelines', icon: GitBranch, label: 'Pipelines' },
  { to: '/monitoring', icon: Activity, label: 'Monitoring' },
];

export default function Sidebar() {
  return (
    <aside className="w-52 bg-[#0d0d14] border-r border-[#1a1a25] flex flex-col min-h-screen">
      <div className="px-4 py-5 border-b border-[#1a1a25]">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-blue-600 flex items-center justify-center">
            <Compass size={14} className="text-white" />
          </div>
          <div>
            <h1 className="text-[13px] font-semibold text-white tracking-tight leading-none">Lighthouse</h1>
            <p className="text-[10px] text-[#4a4a58] mt-0.5">Data Platform</p>
          </div>
        </div>
      </div>
      <nav className="flex-1 px-2 py-3">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-2.5 px-2.5 py-[7px] rounded-md text-[13px] transition-all duration-150 mb-0.5',
                isActive
                  ? 'bg-[#16162a] text-white font-medium'
                  : 'text-[#6b6b7b] hover:text-[#a0a0b0] hover:bg-[#12121e]'
              )
            }
          >
            <Icon size={15} strokeWidth={1.8} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="px-4 py-3 border-t border-[#1a1a25]">
        <div className="text-[10px] text-[#3a3a48] font-mono">v0.1.0</div>
      </div>
    </aside>
  );
}
