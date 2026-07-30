import { Routes } from '@angular/router';
import { ListeningExerciseComponent } from './pages/listening-exercise/listening-exercise.component';

export const listeningPracticeRoutes: Routes = [
  { path: '', component: ListeningExerciseComponent },
  { path: ':day', component: ListeningExerciseComponent },
];
