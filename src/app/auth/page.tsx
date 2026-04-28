"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';
import { UserRole } from '../../types/auth';

type AuthMode = 'login' | 'signup';

const ROLES: { value: UserRole; label: string }[] = [
  { value: 'management', label: 'Management' },
  { value: 'teacher', label: 'Teacher' },
  { value: 'hod', label: 'HOD' },
  { value: 'student', label: 'Student' },
  { value: 'parent', label: 'Parent' },
  { value: 'librarian', label: 'Librarian' },
];

const ORG_TYPES = [
  { value: 'school', label: 'School' },
  { value: 'institute', label: 'Institute/College' },
];

export default function AuthPage() {
  const router = useRouter();
  const { login, signup, isAuthenticated } = useAuth();
  const [mode, setMode] = useState<AuthMode>('login');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Login form
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Signup form
  const [name, setName] = useState('');
  const [signupRole, setSignupRole] = useState<UserRole>('student');
  const [organizationType, setOrganizationType] = useState<'school' | 'institute'>('institute');
  const [organizationName, setOrganizationName] = useState('');
  const [organizationCode, setOrganizationCode] = useState('');
  const [department, setDepartment] = useState('');
  const [title, setTitle] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const isManagement = signupRole === 'management';

  useEffect(() => {
    if (isAuthenticated) {
      router.replace('/dashboard');
    }
  }, [isAuthenticated, router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    setError('');
    setIsLoading(true);

    if (!email || !password) {
      setError('Please fill in all fields');
      setIsLoading(false);
      return;
    }

    const success = await login({ email, password });
    if (success) {
      router.push('/dashboard');
    } else {
      setError('Invalid email or password');
    }
    setIsLoading(false);
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();

    setError('');
    setIsLoading(true);

    // Validation
    if (!email || !password || !name || !signupRole) {
      setError('Please fill in all required fields');
      setIsLoading(false);
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      setIsLoading(false);
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }

    if (!isManagement && !organizationCode) {
      setError('Organization code is required');
      setIsLoading(false);
      return;
    }

    if (isManagement && (!organizationName || !organizationType)) {
      setError('Organization name and type are required');
      setIsLoading(false);
      return;
    }

    const success = await signup({
      email,
      password,
      name,
      role: signupRole,
      organization_type: isManagement ? organizationType : undefined,
      organization_name: isManagement ? organizationName : undefined,
      organization_code: !isManagement ? organizationCode : undefined,
      department: !isManagement ? department : undefined,
      title: !isManagement ? title : undefined,
    });

    if (success) {
      alert('Account created successfully! Please login.');
      setMode('login');
      setEmail('');
      setPassword('');
    } else {
      setError('Signup failed. Please try again.');
    }
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">AIMS</h1>
          <p className="text-slate-400">Academic Institute Management System</p>
        </div>

        <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl border border-slate-700 p-8">
          {/* Tab Toggle */}
          <div className="flex mb-6 bg-slate-700/50 rounded-xl p-1">
            <button
              type="button"
              onClick={() => setMode('login')}
              className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all ${
                mode === 'login'
                  ? 'bg-slate-600 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Login
            </button>
            <button
              type="button"
              onClick={() => setMode('signup')}
              className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all ${
                mode === 'signup'
                  ? 'bg-slate-600 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Signup
            </button>
          </div>

          {mode === 'login' ? (
            <form
              onSubmit={handleLogin}
              className="space-y-4"
              data-auth-ready="true"
            >
              <div>
                <label className="block text-sm text-slate-400 mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  placeholder="you@example.com"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  placeholder="••••••••"
                />
              </div>

              {error && (
                <p className="text-red-400 text-sm">{error}</p>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50"
              >
                {isLoading ? 'Signing in...' : 'Sign In'}
              </button>
            </form>
          ) : (
            <form
              onSubmit={handleSignup}
              className="space-y-4"
              data-auth-ready="true"
            >
              <div>
                <label className="block text-sm text-slate-400 mb-1">Full Name *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  placeholder="Your full name"
                />
              </div>

              <div>
                <label className="block text-sm text-slate-400 mb-1">Email *</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  placeholder="you@example.com"
                />
              </div>

              <div>
                <label className="block text-sm text-slate-400 mb-1">Role *</label>
                <select
                  value={signupRole}
                  onChange={(e) => setSignupRole(e.target.value as UserRole)}
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  {ROLES.map(role => (
                    <option key={role.value} value={role.value}>
                      {role.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* DYNAMIC FIELDS */}
              {isManagement ? (
                <>
                  <div>
                    <label className="block text-sm text-slate-400 mb-1">Organization Type *</label>
                    <select
                      value={organizationType}
                      onChange={(e) => setOrganizationType(e.target.value as 'school' | 'institute')}
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    >
                      {ORG_TYPES.map(type => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm text-slate-400 mb-1">Organization Name *</label>
                    <input
                      type="text"
                      value={organizationName}
                      onChange={(e) => setOrganizationName(e.target.value)}
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                      placeholder="AIMS College"
                    />
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <label className="block text-sm text-slate-400 mb-1">Organization Code *</label>
                    <input
                      type="text"
                      value={organizationCode}
                      onChange={(e) => setOrganizationCode(e.target.value)}
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                      placeholder="AIMS2024"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-slate-400 mb-1">Department</label>
                    <input
                      type="text"
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                      placeholder="Computer Science"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-slate-400 mb-1">Title</label>
                    <input
                      type="text"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                      placeholder="Assistant Professor"
                    />
                  </div>
                </>
              )}

              <div>
                <label className="block text-sm text-slate-400 mb-1">Password *</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  placeholder="Min 6 characters"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Confirm Password *</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  placeholder="Confirm password"
                />
              </div>

              {error && (
                <p className="text-red-400 text-sm">{error}</p>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50"
              >
                {isLoading ? 'Creating account...' : 'Create Account'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
