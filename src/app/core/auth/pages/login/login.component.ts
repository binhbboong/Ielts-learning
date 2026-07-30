import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject } from '@angular/core';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { finalize } from 'rxjs';
import { AuthRepository } from '../../data/auth.repository';
import { AuthState } from '../../state/auth.state';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule],
  templateUrl: './login.component.html',
  styles: `
    :host {
      display: block;
    }

    .login-page {
      box-sizing: border-box;
      display: grid;
      min-height: 100dvh;
      grid-template-rows: auto 1fr;
      margin: -1.5rem;
      color: #18211d;
      background: #f2f5f1;
    }

    .login-header {
      padding: 1.25rem clamp(1.25rem, 4vw, 3rem);
      border-bottom: 1px solid #d7ded8;
      font-weight: 750;
      letter-spacing: -0.02em;
    }

    .login-main {
      display: grid;
      place-items: center;
      padding: 2rem 1.25rem;
    }

    .login-panel {
      width: min(100%, 26rem);
      padding: clamp(1.5rem, 4vw, 2.5rem);
      border: 1px solid #cdd7cf;
      border-radius: 0.875rem;
      background: #fbfcfa;
      box-shadow: 0 1.25rem 3rem rgb(40 70 50 / 10%);
    }

    h1 {
      margin: 0 0 0.5rem;
      font-size: clamp(2rem, 7vw, 2.75rem);
      line-height: 1.05;
      letter-spacing: -0.045em;
    }

    .login-intro {
      margin: 0 0 1.75rem;
      color: #4b5b51;
      line-height: 1.55;
    }

    .login-expired,
    .login-error {
      margin: 0 0 1rem;
      padding: 0.875rem 1rem;
      border-radius: 0.625rem;
      line-height: 1.45;
    }

    .login-expired {
      border: 1px solid #a9bbaa;
      background: #edf4ed;
      color: #294b31;
    }

    .login-error {
      border: 1px solid #d8aaa7;
      background: #fff1f0;
      color: #782e29;
    }

    label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 700;
    }

    input {
      box-sizing: border-box;
      width: 100%;
      min-height: 3rem;
      padding: 0.75rem 0.875rem;
      border: 1px solid #8b9a90;
      border-radius: 0.625rem;
      color: #18211d;
      background: #ffffff;
      font: inherit;
    }

    input:focus-visible {
      outline: 3px solid #bad5c0;
      outline-offset: 2px;
      border-color: #356b43;
    }

    button {
      width: 100%;
      min-height: 3rem;
      margin-top: 1rem;
      border: 0;
      border-radius: 0.625rem;
      color: #f8fbf8;
      background: #285d38;
      font: inherit;
      font-weight: 750;
      cursor: pointer;
      transition:
        transform 120ms ease,
        background-color 120ms ease;
    }

    button:hover:not(:disabled) {
      background: #1f4b2d;
    }

    button:active:not(:disabled) {
      transform: translateY(1px);
    }

    button:focus-visible {
      outline: 3px solid #bad5c0;
      outline-offset: 3px;
    }

    button:disabled,
    input:disabled {
      cursor: not-allowed;
      opacity: 0.68;
    }

    @media (prefers-color-scheme: dark) {
      .login-page {
        color: #edf4ee;
        background: #101713;
      }

      .login-header {
        border-color: #334139;
      }

      .login-panel {
        border-color: #3a4a40;
        background: #17201b;
        box-shadow: 0 1.25rem 3rem rgb(0 0 0 / 22%);
      }

      .login-intro {
        color: #b8c5bc;
      }

      .login-expired {
        border-color: #58705e;
        background: #203127;
        color: #d7eadb;
      }

      .login-error {
        border-color: #895b58;
        background: #342120;
        color: #ffd9d5;
      }

      input {
        border-color: #718078;
        color: #edf4ee;
        background: #101713;
      }

      button {
        color: #102016;
        background: #8fc49c;
      }

      button:hover:not(:disabled) {
        background: #a6d5b1;
      }
    }

    @media (prefers-reduced-motion: reduce) {
      button {
        transition: none;
      }
    }
  `,
})
export class LoginComponent {
  private readonly repository = inject(AuthRepository);
  private readonly authState = inject(AuthState);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  readonly password = new FormControl('', {
    nonNullable: true,
    validators: [Validators.required],
  });
  readonly sessionExpired = this.route.snapshot.queryParamMap.get('reason') === 'expired';

  submitting = false;
  errorMessage = '';

  submit(): void {
    if (this.password.invalid || this.submitting) {
      this.password.markAsTouched();
      return;
    }

    this.submitting = true;
    this.errorMessage = '';
    this.password.disable();

    this.repository
      .login(this.password.value)
      .pipe(
        finalize(() => {
          this.submitting = false;
          this.password.enable();
        }),
      )
      .subscribe({
        next: () => {
          this.authState.setAuthenticated(true);
          void this.router.navigateByUrl('/');
        },
        error: (error: HttpErrorResponse) => {
          const backendMessage = error.error?.detail;
          this.errorMessage =
            typeof backendMessage === 'string' ? backendMessage : 'Authentication failed';
          this.password.setValue('');
        },
      });
  }
}
