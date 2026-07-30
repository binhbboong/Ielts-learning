import { Routes } from '@angular/router';
import { ReadingExerciseComponent } from './pages/reading-exercise/reading-exercise.component';

export const readingPracticeRoutes: Routes = [
  { path: '', component: ReadingExerciseComponent },
  { path: ':day', component: ReadingExerciseComponent },
];
