import { HttpErrorResponse } from '@angular/common/http';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router, convertToParamMap, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { AuthRepository } from '../../data/auth.repository';
import { AuthState } from '../../state/auth.state';
import { LoginComponent } from './login.component';

describe('LoginComponent', () => {
  let fixture: ComponentFixture<LoginComponent>;
  let repository: jasmine.SpyObj<AuthRepository>;
  let authState: jasmine.SpyObj<AuthState>;
  let router: Router;

  function configure(reason?: string): void {
    repository = jasmine.createSpyObj<AuthRepository>('AuthRepository', ['login']);
    authState = jasmine.createSpyObj<AuthState>('AuthState', ['setAuthenticated']);
    TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [
        provideRouter([]),
        { provide: AuthRepository, useValue: repository },
        { provide: AuthState, useValue: authState },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              queryParamMap: convertToParamMap(reason ? { reason } : {}),
            },
          },
        },
      ],
    });

    router = TestBed.inject(Router);
    spyOn(router, 'navigateByUrl').and.resolveTo(true);
    fixture = TestBed.createComponent(LoginComponent);
    fixture.detectChanges();
  }

  function submitPassword(password: string): void {
    const email: HTMLInputElement = fixture.nativeElement.querySelector(
      '[data-testid="email-input"]',
    );
    email.value = 'developer@example.com';
    email.dispatchEvent(new Event('input'));
    const input: HTMLInputElement = fixture.nativeElement.querySelector(
      '[data-testid="password-input"]',
    );
    input.value = password;
    input.dispatchEvent(new Event('input'));
    fixture.nativeElement.querySelector('form').dispatchEvent(new Event('submit'));
    fixture.detectChanges();
  }

  it('logs in with the entered password and updates auth state on success', () => {
    configure();
    repository.login.and.returnValue(of({ authenticated: true }));

    submitPassword('correct password');

    expect(repository.login).toHaveBeenCalledOnceWith(
      'developer@example.com',
      'correct password',
    );
    expect(authState.setAuthenticated).toHaveBeenCalledOnceWith(true);
    expect(router.navigateByUrl).toHaveBeenCalledOnceWith('/');
  });

  it('shows only the backend generic rejection message for an incorrect password', () => {
    configure();
    repository.login.and.returnValue(
      throwError(
        () =>
          new HttpErrorResponse({
            status: 401,
            error: { detail: 'Authentication failed' },
          }),
      ),
    );

    submitPassword('wrong password');

    const error = fixture.nativeElement.querySelector('[data-testid="login-error"]');
    expect(error.textContent.trim()).toBe('Authentication failed');
    expect(fixture.nativeElement.textContent).not.toContain('does not exist');
    expect(fixture.nativeElement.textContent).not.toContain('does not exist');
  });

  it('explains that the session expired when redirected with the expiry reason', () => {
    configure('expired');

    const banner = fixture.nativeElement.querySelector('[data-testid="session-expired"]');
    expect(banner.textContent).toContain('Your session expired');
    expect(fixture.nativeElement.querySelector('[data-testid="login-error"]')).toBeNull();
  });
});
