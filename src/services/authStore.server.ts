import 'server-only';

import { mkdir, readFile, writeFile } from 'fs/promises';
import path from 'path';
import { pbkdf2Sync, randomBytes, randomUUID, timingSafeEqual } from 'crypto';

import type { SignupData, User } from '../types/auth';

type StoredUser = User & {
  passwordHash: string;
  passwordSalt: string;
  createdAt: number;
};

const AUTH_DATA_DIR = path.join(process.cwd(), 'backend', 'data', 'auth');
const AUTH_USERS_FILE = path.join(AUTH_DATA_DIR, 'users.json');
const PBKDF2_ITERATIONS = 310_000;
const PBKDF2_KEY_LENGTH = 32;
const PBKDF2_DIGEST = 'sha256';

const normalizeEmail = (email: string) => email.trim().toLowerCase();

const hashPassword = (password: string, salt?: string) => {
  const resolvedSalt = salt ?? randomBytes(16).toString('hex');
  const hash = pbkdf2Sync(
    password,
    resolvedSalt,
    PBKDF2_ITERATIONS,
    PBKDF2_KEY_LENGTH,
    PBKDF2_DIGEST
  ).toString('hex');

  return { salt: resolvedSalt, hash };
};

const toPublicUser = (user: StoredUser): User => ({
  id: user.id,
  email: user.email,
  name: user.name,
  role: user.role,
  organization_id: user.organization_id,
  organization_name: user.organization_name,
  department: user.department,
});

async function ensureAuthStore() {
  await mkdir(AUTH_DATA_DIR, { recursive: true });
}

async function readUsers(): Promise<StoredUser[]> {
  await ensureAuthStore();

  try {
    const raw = await readFile(AUTH_USERS_FILE, 'utf-8');
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

async function writeUsers(users: StoredUser[]) {
  await ensureAuthStore();
  await writeFile(AUTH_USERS_FILE, JSON.stringify(users, null, 2), 'utf-8');
}

export async function createUser(data: SignupData): Promise<User> {
  const users = await readUsers();
  const email = normalizeEmail(data.email);

  if (users.some((user) => normalizeEmail(user.email) === email)) {
    throw new Error('User already exists');
  }

  const { salt, hash } = hashPassword(data.password);

  const user: StoredUser = {
    id: randomUUID(),
    email,
    name: data.name.trim(),
    role: data.role,
    organization_id: data.organization_code?.trim() || undefined,
    organization_name: data.organization_name?.trim() || undefined,
    department: data.department?.trim() || undefined,
    passwordSalt: salt,
    passwordHash: hash,
    createdAt: Date.now(),
  };

  users.push(user);
  await writeUsers(users);

  return toPublicUser(user);
}

export async function authenticateUser(email: string, password: string): Promise<User | null> {
  const users = await readUsers();
  const normalizedEmail = normalizeEmail(email);
  const user = users.find((entry) => normalizeEmail(entry.email) === normalizedEmail);

  if (!user) {
    return null;
  }

  const { hash } = hashPassword(password, user.passwordSalt);
  const storedHash = Buffer.from(user.passwordHash, 'hex');
  const candidateHash = Buffer.from(hash, 'hex');

  if (
    storedHash.length !== candidateHash.length ||
    !timingSafeEqual(storedHash, candidateHash)
  ) {
    return null;
  }

  return toPublicUser(user);
}

export function issueAuthToken(user: User) {
  return `${user.id}.${randomUUID()}`;
}
