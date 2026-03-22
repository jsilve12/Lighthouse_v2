import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function AppShell() {
  return (
    <div className="flex min-h-screen bg-[#0a0a0f]">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto px-8 py-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
