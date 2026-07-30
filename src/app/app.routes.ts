import { Routes } from '@angular/router';
import { authGuard } from './core/auth/auth.guard';
import { authRoutes } from './core/auth/auth.routes';
import { studyPlanRoutes } from './study-plan/study-plan.routes';
import { routes as mistakeRoutes } from './mistakes/mistakes.routes';
import { vocabularyRoutes } from './vocabulary/vocabulary.routes';
import { progressRoutes } from './progress/progress.routes';
import { writingCoachRoutes } from './writing-coach/writing-coach.routes';
import { speakingCoachRoutes } from './speaking-coach/speaking-coach.routes';
import { dataPortabilityRoutes } from './data-portability/data-portability.routes';
import { readingPracticeRoutes } from './reading-practice/reading-practice.routes';
import { listeningPracticeRoutes } from './listening-practice/listening-practice.routes';

const protectedStudyPlanRoutes: Routes = studyPlanRoutes.map((route) => ({
  ...route,
  canActivate: [authGuard, ...(route.canActivate ?? [])],
}));

export const routes: Routes = [
  ...authRoutes,
  ...protectedStudyPlanRoutes,
  {
    path: 'mistakes',
    canActivate: [authGuard],
    children: mistakeRoutes,
  },
  {
    path: 'vocabulary',
    canActivate: [authGuard],
    children: vocabularyRoutes,
  },
  {
    path: 'progress',
    canActivate: [authGuard],
    children: progressRoutes,
  },
  {
    path: 'writing',
    canActivate: [authGuard],
    children: writingCoachRoutes,
  },
  {
    path: 'speaking',
    canActivate: [authGuard],
    children: speakingCoachRoutes,
  },
  {
    path: 'export',
    canActivate: [authGuard],
    children: dataPortabilityRoutes,
  },
  {
    path: 'reading',
    canActivate: [authGuard],
    children: readingPracticeRoutes,
  },
  {
    path: 'listening',
    canActivate: [authGuard],
    children: listeningPracticeRoutes,
  },
];
