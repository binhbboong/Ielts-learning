import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { AuthState } from './state/auth.state';
import { authInterceptor } from './auth.interceptor';

describe('authInterceptor', () => {
  let http: HttpClient;
  let httpTestingController: HttpTestingController;
  let authState: jasmine.SpyObj<AuthState>;
  let router: jasmine.SpyObj<Router>;

  beforeEach(() => {
    authState = jasmine.createSpyObj<AuthState>('AuthState', ['setAuthenticated']);
    router = jasmine.createSpyObj<Router>('Router', ['navigate']);
    router.navigate.and.resolveTo(true);

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: AuthState, useValue: authState },
        { provide: Router, useValue: router },
      ],
    });

    http = TestBed.inject(HttpClient);
    httpTestingController = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTestingController.verify();
  });

  it('sends credentials with every outgoing request', () => {
    http.get('/api/protected').subscribe();

    const request = httpTestingController.expectOne('/api/protected');
    expect(request.request.withCredentials).toBeTrue();
    request.flush({});
  });

  it('marks the learner unauthenticated and redirects with an expiry reason on expired 401', () => {
    http.get('/api/protected').subscribe({ error: () => undefined });

    const request = httpTestingController.expectOne('/api/protected');
    request.flush(
      { detail: { reason: 'expired' } },
      { status: 401, statusText: 'Unauthorized' },
    );

    expect(authState.setAuthenticated).toHaveBeenCalledOnceWith(false);
    expect(router.navigate).toHaveBeenCalledOnceWith(['/login'], {
      queryParams: { reason: 'expired' },
    });
  });

  ['missing', 'invalid'].forEach((reason) => {
    it(`redirects without an expiry flag on a ${reason} 401`, () => {
      http.get('/api/protected').subscribe({ error: () => undefined });

      const request = httpTestingController.expectOne('/api/protected');
      request.flush(
        { detail: { reason } },
        { status: 401, statusText: 'Unauthorized' },
      );

      expect(authState.setAuthenticated).toHaveBeenCalledOnceWith(false);
      expect(router.navigate).toHaveBeenCalledOnceWith(['/login']);
    });
  });
});
