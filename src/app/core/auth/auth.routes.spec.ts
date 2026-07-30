import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { of } from 'rxjs';
import { routes } from '../../app.routes';
import { DailyChecklistComponent } from '../../study-plan/pages/daily-checklist/daily-checklist.component';
import { StudyPlanFacade } from '../../study-plan/state/study-plan.facade';
import { AuthRepository } from './data/auth.repository';
import { LoginComponent } from './pages/login/login.component';
import { AuthState } from './state/auth.state';

describe('Authentication routing', () => {
  function configure(authenticated: boolean): void {
    const facadeStub = {
      tasks: signal([]),
      currentDayNumber: signal(1),
      loadCurrentDay: jasmine.createSpy('loadCurrentDay').and.resolveTo(undefined),
    };
    const authStateStub = {
      authenticated: signal(authenticated),
      initialized: signal(true),
      setAuthenticated: jasmine.createSpy('setAuthenticated'),
    };
    const authRepositoryStub = {
      login: jasmine.createSpy('login').and.returnValue(of({ authenticated: true })),
    };

    TestBed.configureTestingModule({
      providers: [
        provideRouter(routes, withComponentInputBinding()),
        { provide: StudyPlanFacade, useValue: facadeStub },
        { provide: AuthState, useValue: authStateStub },
        { provide: AuthRepository, useValue: authRepositoryStub },
      ],
    });
  }

  it('resolves the login route to LoginComponent', async () => {
    configure(false);
    const harness = await RouterTestingHarness.create();

    const component = await harness.navigateByUrl('/login', LoginComponent);

    expect(component).toBeInstanceOf(LoginComponent);
  });

  it('redirects direct protected navigation to login when unauthenticated', async () => {
    configure(false);
    const harness = await RouterTestingHarness.create();

    const component = await harness.navigateByUrl('/', LoginComponent);

    expect(component).toBeInstanceOf(LoginComponent);
  });

  it('allows the protected default route when authenticated', async () => {
    configure(true);
    const harness = await RouterTestingHarness.create();

    const component = await harness.navigateByUrl('/', DailyChecklistComponent);

    expect(component).toBeInstanceOf(DailyChecklistComponent);
  });
});
