import { ReadingPracticeRepository } from '../data/reading-practice.repository';
import { ReadingPracticeFacade } from './reading-practice.facade';

describe('ReadingPracticeFacade', () => {
  const exercise = {
    day: '2026-07-30', status: 'ready' as const,
    focusReference: "the word 'nevertheless'", passageText: 'A passage.',
    questions: [{
      id: 'q1', questionText: 'What is discussed?', questionType: 'multiple_choice',
      options: ['A', 'B'], order: 1,
    }],
  };
  const result = {
    day: '2026-07-30', score: 1, total: 1,
    answers: [{
      questionText: 'What is discussed?', questionType: 'multiple_choice',
      options: ['A', 'B'], learnerAnswer: 1, correctAnswer: 1, correct: true,
    }],
  };

  it('loads an exercise for a day', async () => {
    const repository = jasmine.createSpyObj<ReadingPracticeRepository>(
      'ReadingPracticeRepository', ['get', 'submit', 'retry'],
    );
    repository.get.and.resolveTo(exercise);
    const facade = new ReadingPracticeFacade(repository);

    await facade.load('2026-07-30');

    expect(facade.exerciseState()).toBe('ready');
    expect(facade.exercise()?.passageText).toBe('A passage.');
  });

  it('submits answers for the loaded day', async () => {
    const repository = jasmine.createSpyObj<ReadingPracticeRepository>(
      'ReadingPracticeRepository', ['get', 'submit', 'retry'],
    );
    repository.get.and.resolveTo(exercise);
    repository.submit.and.resolveTo(result);
    const facade = new ReadingPracticeFacade(repository);
    await facade.load('2026-07-30');

    await facade.submit([1]);

    expect(repository.submit).toHaveBeenCalledWith('2026-07-30', [1]);
    expect(facade.submitState()).toBe('ready');
    expect(facade.result()?.score).toBe(1);
  });

  it('retries generation for the loaded day', async () => {
    const repository = jasmine.createSpyObj<ReadingPracticeRepository>(
      'ReadingPracticeRepository', ['get', 'submit', 'retry'],
    );
    repository.get.and.resolveTo({ ...exercise, status: 'failed', passageText: null });
    repository.retry.and.resolveTo(exercise);
    const facade = new ReadingPracticeFacade(repository);
    await facade.load('2026-07-30');

    await facade.retry();

    expect(repository.retry).toHaveBeenCalledWith('2026-07-30');
    expect(facade.exercise()?.status).toBe('ready');
  });

  it('sets error state when loading fails', async () => {
    const repository = jasmine.createSpyObj<ReadingPracticeRepository>(
      'ReadingPracticeRepository', ['get', 'submit', 'retry'],
    );
    repository.get.and.rejectWith(new Error('offline'));
    const facade = new ReadingPracticeFacade(repository);

    await facade.load('2026-07-30');

    expect(facade.exerciseState()).toBe('error');
  });
});
