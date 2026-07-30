import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject, Injector } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthState } from './state/auth.state';

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const injector = inject(Injector);

  return next(request.clone({ withCredentials: true })).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401) {
        const authState = injector.get(AuthState);
        const router = injector.get(Router);
        authState.setAuthenticated(false);
        const reason = error.error?.detail?.reason;

        if (reason === 'expired') {
          void router.navigate(['/login'], { queryParams: { reason: 'expired' } });
        } else {
          void router.navigate(['/login']);
        }
      }

      return throwError(() => error);
    }),
  );
};
