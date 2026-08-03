import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject } from '@angular/core';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { AuthRepository } from '../../data/auth.repository';
import { AuthState } from '../../state/auth.state';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './register.component.html',
  styles: `
    .register-page { display:grid; min-height:80vh; place-items:center; }
    .register-panel { width:min(100%,28rem); padding:2rem; border:1px solid #cdd7cf;
      border-radius:.875rem; background:#fbfcfa; }
    label { display:block; margin:1rem 0 .4rem; font-weight:700; }
    input, button { box-sizing:border-box; width:100%; min-height:3rem; padding:.75rem;
      border-radius:.625rem; font:inherit; }
    button { margin-top:1rem; border:0; color:white; background:#285d38; font-weight:750; }
  `,
})
export class RegisterComponent {
  private readonly repository = inject(AuthRepository);
  private readonly authState = inject(AuthState);
  private readonly router = inject(Router);

  readonly displayName = new FormControl('', {
    nonNullable: true,
    validators: [Validators.required],
  });
  readonly email = new FormControl('', {
    nonNullable: true,
    validators: [Validators.required, Validators.email],
  });
  readonly password = new FormControl('', {
    nonNullable: true,
    validators: [Validators.required, Validators.minLength(8)],
  });
  submitting = false;
  errorMessage = '';

  submit(): void {
    if (this.displayName.invalid || this.email.invalid || this.password.invalid || this.submitting) {
      this.displayName.markAsTouched();
      this.email.markAsTouched();
      this.password.markAsTouched();
      return;
    }
    this.submitting = true;
    this.errorMessage = '';
    this.repository
      .register(this.email.value, this.password.value, this.displayName.value)
      .pipe(finalize(() => (this.submitting = false)))
      .subscribe({
        next: () => {
          this.authState.setAuthenticated(true);
          void this.router.navigateByUrl('/');
        },
        error: (error: HttpErrorResponse) => {
          this.errorMessage =
            typeof error.error?.detail === 'string'
              ? error.error.detail
              : 'Could not create account';
        },
      });
  }
}
