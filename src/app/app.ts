import { Component, inject } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { Router } from '@angular/router';
import { finalize } from 'rxjs';
import { AuthRepository } from './core/auth/data/auth.repository';
import { AuthState } from './core/auth/state/auth.state';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  readonly authState = inject(AuthState);
  private readonly authRepository = inject(AuthRepository);
  private readonly router = inject(Router);

  loggingOut = false;

  logout(): void {
    if (this.loggingOut) {
      return;
    }

    this.loggingOut = true;
    this.authRepository
      .logout()
      .pipe(finalize(() => (this.loggingOut = false)))
      .subscribe({
        next: () => {
          this.authState.setAuthenticated(false);
          void this.router.navigateByUrl('/login');
        },
      });
  }
}
