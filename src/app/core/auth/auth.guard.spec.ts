import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  Router,
  RouterStateSnapshot,
  provideRouter,
} from '@angular/router';
import { AuthState } from './state/auth.state';
import { authGuard } from './auth.guard';

describe('authGuard', () => {
  const route = {} as ActivatedRouteSnapshot;
  const routerState = {} as RouterStateSnapshot;

  function configure(authenticated: boolean): Router {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        {
          provide: AuthState,
          useValue: {
            authenticated: signal(authenticated),
            initialized: signal(true),
          },
        },
      ],
    });

    return TestBed.inject(Router);
  }

  it('allows navigation when the learner is authenticated', () => {
    configure(true);

    const result = TestBed.runInInjectionContext(() => authGuard(route, routerState));

    expect(result).toBeTrue();
  });

  it('blocks navigation and redirects to login when the learner is unauthenticated', () => {
    const router = configure(false);

    const result = TestBed.runInInjectionContext(() => authGuard(route, routerState));

    expect(router.serializeUrl(result as ReturnType<Router['createUrlTree']>)).toBe('/login');
  });
});
