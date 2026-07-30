import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ApiClient {
  constructor(private readonly http: HttpClient) {}

  get<T>(url: string): Observable<T> {
    return this.http.get<T>(url);
  }

  post<T>(url: string, body: unknown): Observable<T> {
    return this.http.post<T>(url, body);
  }

  patch<T>(url: string, body: unknown): Observable<T> {
    return this.http.patch<T>(url, body);
  }

  delete<T>(url: string): Observable<T> {
    return this.http.delete<T>(url);
  }
}
