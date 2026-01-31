// User types
export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  role_name: string | null;
  role?: Role;
  created_at: string;
  updated_at: string;
}

export interface UserListItem {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  role_name: string | null;
  role?: Role;
  created_at: string;
}

// Auth types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginResponse {
  message: string;
  user: User;
  tokens: AuthTokens;
}

export interface RegisterResponse {
  message: string;
  user: User;
  tokens: AuthTokens;
}

// File types
export interface FileItem {
  id: number;
  filename: string;
  original_filename: string;
  content_type: string;
  size: number;
  file_size?: number; // alias for size
  description: string | null;
  owner_id: number;
  download_count?: number;
  created_at: string;
  updated_at: string;
}

export interface FileUploadResponse {
  id: number;
  filename: string;
  original_filename: string;
  content_type: string;
  size: number;
  message: string;
}

// Share link types
export interface ShareLink {
  id: number;
  token: string;
  share_token?: string; // alias for token
  file_id: number;
  filename: string;
  file?: { filename: string }; // nested file info
  expires_at: string;
  is_active: boolean;
  download_count: number;
  max_downloads: number | null;
  password?: boolean; // has password protection
  created_at: string;
}

export interface ShareLinkCreate {
  file_id: number;
  expiry_minutes?: number;
  expires_in_days?: number;
  max_downloads?: number;
  password?: string;
  requires_auth?: boolean;
  allowed_email?: string;
}

export interface ShareLinkResponse {
  token: string;
  share_url: string;
  share_token?: string;
  file_id: number;
  filename: string;
  expires_at: string;
  expires_in_minutes: number;
  max_downloads: number | null;
  requires_auth: boolean;
  created_at: string;
}

// Audit log types
export interface AuditLog {
  id: number;
  user_id: number | null;
  user_email: string | null;
  action: string;
  resource_type: string | null;
  resource_id: number | null;
  details: string | null;
  ip_address: string | null;
  user_agent: string | null;
  status: string;
  created_at: string;
}

// Role types
export interface Role {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

// Health check
export interface HealthCheck {
  status: string;
  timestamp: string;
  version: string;
}

export interface DetailedHealthCheck {
  status: string;
  database: string;
  redis: string;
  s3: string;
  timestamp: string;
  version: string;
}

// API error
export interface ApiError {
  detail: string;
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}
