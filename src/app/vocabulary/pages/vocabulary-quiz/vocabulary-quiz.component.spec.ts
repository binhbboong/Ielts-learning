import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { VocabularyFacade } from '../../state/vocabulary.facade';
import { VocabularyQuizComponent } from './vocabulary-quiz.component';

function setup(state: any, loadState: 'loading' | 'ready' | 'error' = 'ready') {
  const facade = {
    quizState: signal(state),
    quizLoadState: signal(loadState),
    startQuiz: jasmine.createSpy('startQuiz').and.resolveTo(undefined),
    answerQuizItem: jasmine.createSpy('answerQuizItem').and.resolveTo(undefined),
  };
  TestBed.configureTestingModule({
    imports: [VocabularyQuizComponent],
    providers: [provideRouter([]), { provide: VocabularyFacade, useValue: facade }],
  });
  const fixture = TestBed.createComponent(VocabularyQuizComponent);
  return { fixture, facade };
}

describe('VocabularyQuizComponent', () => {
  it('starts the quiz on init', () => {
    const { fixture, facade } = setup({ status: 'not_ready' });
    fixture.detectChanges();
    expect(facade.startQuiz).toHaveBeenCalled();
  });

  it('renders a question with shuffled options and answers on click', async () => {
    const { fixture, facade } = setup({
      status: 'item',
      item: {
        quizId: 'q1',
        itemId: 'i1',
        word: 'mitigate',
        options: ['make worse', 'make less severe', 'ignore', 'delay'],
        position: 0,
        total: 3,
      },
    });
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('mitigate');
    expect(text).toContain('make less severe');

    const buttons = fixture.nativeElement.querySelectorAll(
      '[data-testid="quiz-card"] button',
    );
    expect(buttons.length).toBe(4);
    buttons[1].click();

    expect(facade.answerQuizItem).toHaveBeenCalledWith(1);
  });

  it('shows pass/fail messaging on the complete state', () => {
    const { fixture } = setup({
      status: 'complete',
      summary: { quizId: 'q1', correct: 4, total: 5, passed: true },
    });
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('4 / 5 correct');
    expect(text).toContain('Checkpoint passed');
  });

  it('lets the learner retry a failed checkpoint', () => {
    const { fixture, facade } = setup({
      status: 'complete',
      summary: { quizId: 'q1', correct: 2, total: 5, passed: false },
    });
    fixture.detectChanges();

    const retry = Array.from(
      fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>,
    ).find((button) => button.textContent?.includes('Try the checkpoint again'));
    retry?.click();

    expect(retry).toBeDefined();
    expect(facade.startQuiz).toHaveBeenCalledTimes(2);
  });

  it('shows a not-ready state distinct from complete', () => {
    const { fixture } = setup({ status: 'not_ready' });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Finish today');
    expect(fixture.nativeElement.querySelector('[data-testid="quiz-complete"]')).toBeNull();
  });
});
