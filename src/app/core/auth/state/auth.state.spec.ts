import { effect } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { Subject } from 'rxjs';
import { AuthStatusResponse } from '../models/auth-status.model';
import { AuthRepository } from '../data/auth.repository';
import { AuthState } from './auth.state';

describe('AuthState', () => {
  let statusResponse: Subject<AuthStatusResponse>;
  let repository: jasmine.SpyObj<AuthRepository>;

  beforeEach(() => {
    statusResponse = new Subject<AuthStatusResponse>();
    repository = jasmine.createSpyObj<AuthRepository>('AuthRepository', ['status']);
    repository.status.and.returnValue(statusResponse.asObservable());

    TestBed.configureTestingModule({
      providers: [AuthState, { provide: AuthRepository, useValue: repository }],
    });
  });

  it('initializes authentication state from the repository status response', () => {
    const state = TestBed.inject(AuthState);

    expect(repository.status).toHaveBeenCalledTimes(1);
    expect(state.authenticated()).toBeFalse();

    statusResponse.next({ authenticated: true });

    expect(state.authenticated()).toBeTrue();
  });

  it('updates the exposed signal synchronously for subscribers', () => {
    const state = TestBed.inject(AuthState);
    const observed: boolean[] = [];

    TestBed.runInInjectionContext(() => {
      effect(() => observed.push(state.authenticated()));
    });
    TestBed.flushEffects();

    state.setAuthenticated(true);
    TestBed.flushEffects();
    state.setAuthenticated(false);
    TestBed.flushEffects();

    expect(observed).toEqual([false, true, false]);
  });
});
