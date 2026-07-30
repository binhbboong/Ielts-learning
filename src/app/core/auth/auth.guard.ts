import { inject } from '@angular/core';
import { toObservable } from '@angular/core/rxjs-interop';
import { CanActivateFn, Router } from '@angular/router';
import { filter, map, take } from 'rxjs';
import { AuthState } from './state/auth.state';

export const authGuard: CanActivateFn = () => {
  const authState = inject(AuthState);
  const router = inject(Router);
  const resolveAccess = () =>
    authState.authenticated() ? true : router.createUrlTree(['/login']);

  if (authState.initialized()) {
    return resolveAccess();
  }

  return toObservable(authState.initialized).pipe(
    filter((initialized) => initialized),
    take(1),
    map(resolveAccess),
  );
};
