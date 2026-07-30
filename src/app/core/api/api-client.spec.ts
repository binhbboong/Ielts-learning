import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ApiClient } from './api-client';

interface ExampleResponse {
  id: number;
}

describe('ApiClient', () => {
  let client: ApiClient;
  let httpTestingController: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ApiClient, provideHttpClient(), provideHttpClientTesting()],
    });
    client = TestBed.inject(ApiClient);
    httpTestingController = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpTestingController.verify());

  it('performs a typed GET request', () => {
    let actual: ExampleResponse | undefined;
    client.get<ExampleResponse>('/api/example/1').subscribe((value) => (actual = value));

    const request = httpTestingController.expectOne('/api/example/1');
    expect(request.request.method).toBe('GET');
    request.flush({ id: 1 });

    expect(actual).toEqual({ id: 1 });
  });

  it('performs typed POST and PATCH requests with their bodies', () => {
    client.post<ExampleResponse>('/api/example', { name: 'one' }).subscribe();
    const post = httpTestingController.expectOne('/api/example');
    expect(post.request.method).toBe('POST');
    expect(post.request.body).toEqual({ name: 'one' });
    post.flush({ id: 1 });

    client.patch<ExampleResponse>('/api/example/1', { name: 'updated' }).subscribe();
    const patch = httpTestingController.expectOne('/api/example/1');
    expect(patch.request.method).toBe('PATCH');
    expect(patch.request.body).toEqual({ name: 'updated' });
    patch.flush({ id: 1 });
  });

  it('performs a typed DELETE request', () => {
    client.delete<void>('/api/example/1').subscribe();

    const request = httpTestingController.expectOne('/api/example/1');
    expect(request.request.method).toBe('DELETE');
    request.flush(null);
  });
});
