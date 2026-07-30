import { HttpErrorResponse } from '@angular/common/http';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router, convertToParamMap } from '@angular/router';
import { of, throwError } from 'rxjs';
import { AuthRepository } from '../../data/auth.repository';
import { AuthState } from '../../state/auth.state';
import { LoginComponent } from './login.component';

describe('LoginComponent', () => {
  let fixture: ComponentFixture<LoginComponent>;
  let repository: jasmine.SpyObj<AuthRepository>;
  let authState: jasmine.SpyObj<AuthState>;
  let router: jasmine.SpyObj<Router>;

  function configure(reason?: string): void {
    repository = jasmine.createSpyObj<AuthRepository>('AuthRepository', ['login']);
    authState = jasmine.createSpyObj<AuthState>('AuthState', ['setAuthenticated']);
    router = jasmine.createSpyObj<Router>('Router', ['navigateByUrl']);
    router.navigateByUrl.and.resolveTo(true);

    TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [
        { provide: AuthRepository, useValue: repository },
        { provide: AuthState, useValue: authState },
        { provide: Router, useValue: router },
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

    fixture = TestBed.createComponent(LoginComponent);
    fixture.detectChanges();
  }

  function submitPassword(password: string): void {
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

    expect(repository.login).toHaveBeenCalledOnceWith('correct password');
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
    expect(fixture.nativeElement.textContent).not.toContain('username');
    expect(fixture.nativeElement.textContent).not.toContain('does not exist');
  });

  it('explains that the session expired when redirected with the expiry reason', () => {
    configure('expired');

    const banner = fixture.nativeElement.querySelector('[data-testid="session-expired"]');
    expect(banner.textContent).toContain('Your session expired');
    expect(fixture.nativeElement.querySelector('[data-testid="login-error"]')).toBeNull();
  });
});
