"use client";

import { useAuth } from '../../context/AuthContext';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '../../components/Auth/ProtectedRoute';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/auth');
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-slate-900">
        <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-white">AIMS Dashboard</h1>
            <div className="flex items-center gap-4">
              <span className="text-slate-400">
                {user?.name} ({user?.role})
              </span>
              <button
                onClick={handleLogout}
                className="text-sm text-slate-400 hover:text-white transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        <main className="p-6">
          {children}
        </main>
      </div>
    </ProtectedRoute>
  );
}
