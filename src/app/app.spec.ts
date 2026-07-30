import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { App } from './app';
import { AuthRepository } from './core/auth/data/auth.repository';
import { AuthState } from './core/auth/state/auth.state';

describe('App authentication shell', () => {
  let fixture: ComponentFixture<App>;
  let authenticated: ReturnType<typeof signal<boolean>>;
  let authState: { authenticated: typeof authenticated; setAuthenticated: jasmine.Spy };
  let repository: jasmine.SpyObj<AuthRepository>;
  let router: Router;

  async function configure(isAuthenticated: boolean): Promise<void> {
    authenticated = signal(isAuthenticated);
    authState = {
      authenticated,
      setAuthenticated: jasmine
        .createSpy('setAuthenticated')
        .and.callFake((value: boolean) => authenticated.set(value)),
    };
    repository = jasmine.createSpyObj<AuthRepository>('AuthRepository', ['logout']);
    repository.logout.and.returnValue(of({ authenticated: false }));

    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideRouter([]),
        { provide: AuthState, useValue: authState },
        { provide: AuthRepository, useValue: repository },
      ],
    }).compileComponents();

    router = TestBed.inject(Router);
    fixture = TestBed.createComponent(App);
    fixture.detectChanges();
  }

  it('hides protected navigation and logout controls while unauthenticated', async () => {
    await configure(false);

    expect(fixture.nativeElement.querySelector('[data-testid="app-nav"]')).toBeNull();
    expect(fixture.nativeElement.querySelector('[data-testid="logout"]')).toBeNull();
  });

  it('shows protected navigation and the recognized learner indicator while authenticated', async () => {
    await configure(true);

    expect(fixture.nativeElement.querySelector('[data-testid="app-nav"]')).not.toBeNull();
    expect(
      fixture.nativeElement.querySelector('[data-testid="auth-indicator"]').textContent,
    ).toContain('Recognized as learner');
  });

  it('logs out, clears auth state, and returns to login', async () => {
    await configure(true);
    const navigate = spyOn(router, 'navigateByUrl').and.resolveTo(true);

    fixture.nativeElement.querySelector('[data-testid="logout"]').click();
    fixture.detectChanges();

    expect(repository.logout).toHaveBeenCalledTimes(1);
    expect(authState.setAuthenticated).toHaveBeenCalledOnceWith(false);
    expect(navigate).toHaveBeenCalledOnceWith('/login');
  });
});
