import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { AuthStatusResponse } from '../models/auth-status.model';

const AUTH_API_URL = '/api/auth';

@Injectable({ providedIn: 'root' })
export class AuthRepository {
  constructor(private readonly http: HttpClient) {}

  login(email: string, password: string): Observable<AuthStatusResponse> {
    return this.http.post<AuthStatusResponse>(`${AUTH_API_URL}/login`, { email, password });
  }

  register(email: string, password: string, displayName: string): Observable<AuthStatusResponse> {
    return this.http.post<AuthStatusResponse>(`${AUTH_API_URL}/register`, {
      email,
      password,
      display_name: displayName,
    });
  }

  logout(): Observable<AuthStatusResponse> {
    return this.http.post<AuthStatusResponse>(`${AUTH_API_URL}/logout`, null);
  }

  status(): Observable<AuthStatusResponse> {
    return this.http.get<AuthStatusResponse>(`${AUTH_API_URL}/status`);
  }
}
