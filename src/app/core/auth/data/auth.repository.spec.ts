import { HttpErrorResponse, provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { AuthStatusResponse } from '../models/auth-status.model';
import { AuthRepository } from './auth.repository';

describe('AuthRepository', () => {
  let repository: AuthRepository;
  let httpTestingController: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [AuthRepository, provideHttpClient(), provideHttpClientTesting()],
    });

    repository = TestBed.inject(AuthRepository);
    httpTestingController = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTestingController.verify();
  });

  it('posts the password to the login endpoint and returns the authenticated response', () => {
    const response: AuthStatusResponse = { authenticated: true };
    let actual: AuthStatusResponse | undefined;

    repository.login('correct horse battery staple').subscribe((value) => (actual = value));

    const request = httpTestingController.expectOne('/api/auth/login');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ password: 'correct horse battery staple' });
    request.flush(response);

    expect(actual).toEqual(response);
  });

  [401, 429].forEach((status) => {
    it(`propagates a ${status} login rejection`, () => {
      let actualError: HttpErrorResponse | undefined;

      repository.login('wrong password').subscribe({
        error: (error: HttpErrorResponse) => (actualError = error),
      });

      const request = httpTestingController.expectOne('/api/auth/login');
      request.flush(
        { detail: status === 401 ? 'Authentication failed' : 'Too many attempts' },
        { status, statusText: status === 401 ? 'Unauthorized' : 'Too Many Requests' },
      );

      expect(actualError?.status).toBe(status);
    });
  });

  it('posts to the logout endpoint and returns the unauthenticated response', () => {
    const response: AuthStatusResponse = { authenticated: false };
    let actual: AuthStatusResponse | undefined;

    repository.logout().subscribe((value) => (actual = value));

    const request = httpTestingController.expectOne('/api/auth/logout');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toBeNull();
    request.flush(response);

    expect(actual).toEqual(response);
  });

  it('gets the current authentication status as an AuthStatusResponse', () => {
    const response: AuthStatusResponse = { authenticated: false, reason: 'expired' };
    let actual: AuthStatusResponse | undefined;

    repository.status().subscribe((value) => (actual = value));

    const request = httpTestingController.expectOne('/api/auth/status');
    expect(request.request.method).toBe('GET');
    request.flush(response);

    expect(actual).toEqual(response);
  });
});
