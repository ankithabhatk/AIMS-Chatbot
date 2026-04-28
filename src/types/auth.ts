export type UserRole = 'management' | 'teacher' | 'hod' | 'student' | 'parent' | 'librarian';

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  organization_id?: string;
  organization_name?: string;
  department?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupData {
  email: string;
  password: string;
  name: string;
  role: UserRole;
  organization_type?: 'school' | 'institute';
  organization_name?: string;
  organization_code?: string;
  department?: string;
  title?: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  user?: User;
  token?: string;
}