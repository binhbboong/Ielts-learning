export type AuthReason = 'missing' | 'invalid' | 'expired';

export interface AuthStatusResponse {
  authenticated: boolean;
  reason?: AuthReason;
}
