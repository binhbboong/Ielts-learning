import { routes } from './mistakes.routes';
import { LoggingFormComponent } from './pages/logging-form/logging-form.component';
import { ReviewShellComponent } from './pages/review-shell/review-shell.component';

describe('mistake routes', () => {
  it('wires logging and review pages', () => {
    expect(routes.find((route) => route.path === 'log')?.component).toBe(
      LoggingFormComponent,
    );
    expect(routes.find((route) => route.path === '')?.component).toBe(
      ReviewShellComponent,
    );
  });
});
