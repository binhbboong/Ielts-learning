import { Injectable, signal } from '@angular/core';
import { AuthRepository } from '../data/auth.repository';

@Injectable({ providedIn: 'root' })
export class AuthState {
  private readonly authenticatedState = signal(false);
  private readonly initializedState = signal(false);

  readonly authenticated = this.authenticatedState.asReadonly();
  readonly initialized = this.initializedState.asReadonly();

  constructor(repository: AuthRepository) {
    repository.status().subscribe({
      next: ({ authenticated }) => {
        this.authenticatedState.set(authenticated);
        this.initializedState.set(true);
      },
      error: () => {
        this.authenticatedState.set(false);
        this.initializedState.set(true);
      },
    });
  }

  setAuthenticated(authenticated: boolean): void {
    this.authenticatedState.set(authenticated);
    this.initializedState.set(true);
  }
}
