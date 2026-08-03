export type AuthReason = 'missing' | 'invalid' | 'expired';

export interface AuthStatusResponse {
  authenticated: boolean;
  reason?: AuthReason;
  user_id?: string;
  email?: string;
  display_name?: string;
}
