import { HttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { appConfig } from './app.config';

describe('appConfig HTTP integration', () => {
  it('provides HttpClient with the auth interceptor enabled', () => {
    TestBed.configureTestingModule({
      providers: [...appConfig.providers, provideHttpClientTesting()],
    });

    const http = TestBed.inject(HttpClient);
    const httpTestingController = TestBed.inject(HttpTestingController);

    http.get('/api/protected').subscribe();

    const request = httpTestingController.expectOne('/api/protected');
    expect(request.request.withCredentials).toBeTrue();
    request.flush({});
    httpTestingController.verify();
  });
});
