"use client";

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: string[];
}

export default function ProtectedRoute({ 
  children, 
  allowedRoles 
}: ProtectedRouteProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading } = useAuth();
  const isAllowedRole = !allowedRoles?.length || Boolean(user && allowedRoles.includes(user.role));
  const isAuthorized = isAuthenticated && isAllowedRole;

  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated) {
      router.push(`/auth?redirect=${pathname}`);
      return;
    }

    if (!isAllowedRole) {
      router.push('/unauthorized');
    }
  }, [isAuthenticated, isAllowedRole, isLoading, pathname, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!isAuthorized) {
    return null;
  }

  return <>{children}</>;
}
