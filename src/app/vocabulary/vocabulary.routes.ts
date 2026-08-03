import { Routes } from '@angular/router';
import { VocabularyDueListComponent } from './pages/vocabulary-due-list/vocabulary-due-list.component';
import { VocabularyHistoryComponent } from './pages/vocabulary-history/vocabulary-history.component';
import { VocabularyQuizComponent } from './pages/vocabulary-quiz/vocabulary-quiz.component';
import { VocabularyReviewSessionComponent } from './pages/vocabulary-review-session/vocabulary-review-session.component';

export const vocabularyRoutes: Routes = [
  { path: '', component: VocabularyDueListComponent },
  { path: 'review', component: VocabularyReviewSessionComponent },
  { path: 'quiz', component: VocabularyQuizComponent },
  { path: 'history', component: VocabularyHistoryComponent },
];
