import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { of } from 'rxjs';
import { routes } from '../../app.routes';
import { DailyOverviewComponent } from '../../daily-lesson/pages/daily-overview/daily-overview.component';
import { DailyLessonFacade } from '../../daily-lesson/state/daily-lesson.facade';
import { VocabularyFacade } from '../../vocabulary/state/vocabulary.facade';
import { AuthRepository } from './data/auth.repository';
import { LoginComponent } from './pages/login/login.component';
import { AuthState } from './state/auth.state';

describe('Authentication routing', () => {
  function configure(authenticated: boolean): void {
    const facadeStub = {
      state: signal('ready'),
      overview: signal({
        day: '2026-07-30',
        examType: 'IELTS Academic',
        week: 1,
        phase: 'foundation',
        targetBand: 4.5,
        totalMinutes: 60,
        reviewMinutes: 10,
        skills: [],
      }),
      load: jasmine.createSpy('load').and.resolveTo(undefined),
    };
    const authStateStub = {
      authenticated: signal(authenticated),
      initialized: signal(true),
      setAuthenticated: jasmine.createSpy('setAuthenticated'),
    };
    const authRepositoryStub = {
      login: jasmine.createSpy('login').and.returnValue(of({ authenticated: true })),
    };
    const vocabularyFacadeStub = {
      reviewLoadState: signal('ready'),
      reviewState: signal({ status: 'nothing_due' }),
      recommendationsLoadState: signal('ready'),
      recommendations: signal({ recommendations: [] }),
      startOrResumeReview: jasmine.createSpy('startOrResumeReview').and.resolveTo(undefined),
      loadRecommendations: jasmine.createSpy('loadRecommendations').and.resolveTo(undefined),
    };

    TestBed.configureTestingModule({
      providers: [
        provideRouter(routes, withComponentInputBinding()),
        { provide: DailyLessonFacade, useValue: facadeStub },
        { provide: VocabularyFacade, useValue: vocabularyFacadeStub },
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

    const component = await harness.navigateByUrl('/', DailyOverviewComponent);

    expect(component).toBeInstanceOf(DailyOverviewComponent);
  });
});
