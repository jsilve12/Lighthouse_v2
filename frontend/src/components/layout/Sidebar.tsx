import { NavLink } from 'react-router-dom';
import { Database, Code2, GitBranch, Activity } from 'lucide-react';
import { cn } from '../../utils/cn';

const navItems = [
  { to: '/datasets', icon: Database, label: 'Datasets' },
  { to: '/transformations', icon: Code2, label: 'Transformations' },
  { to: '/pipelines', icon: GitBranch, label: 'Pipelines' },
  { to: '/monitoring', icon: Activity, label: 'Monitoring' },
];

export default function Sidebar() {
  return (
    <aside className="w-56 bg-gray-900 text-gray-300 flex flex-col min-h-screen">
      <div className="p-4 border-b border-gray-700">
        <h1 className="text-lg font-bold text-white tracking-tight">Lighthouse</h1>
        <p className="text-xs text-gray-500">Data Platform</p>
      </div>
      <nav className="flex-1 p-2">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors mb-1',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'hover:bg-gray-800 text-gray-400 hover:text-white'
              )
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
