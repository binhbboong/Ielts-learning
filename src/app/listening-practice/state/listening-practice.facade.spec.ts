import { ListeningPracticeRepository } from '../data/listening-practice.repository';
import { ListeningPracticeFacade } from './listening-practice.facade';

describe('ListeningPracticeFacade', () => {
  const exercise = {
    day: '2026-07-30', status: 'ready',
    focusReference: "the word 'nevertheless'", scriptText: null,
    questions: [{ id: 'q1', questionText: 'What is discussed?', options: ['A', 'B'], order: 1 }],
  };
  const result = {
    day: '2026-07-30', score: 1, total: 1, scriptText: 'A script.',
    answers: [{
      questionText: 'What is discussed?', options: ['A', 'B'],
      learnerAnswerIndex: 1, correctOptionIndex: 1, correct: true,
    }],
  };

  function repo() {
    return jasmine.createSpyObj<ListeningPracticeRepository>(
      'ListeningPracticeRepository',
      ['get', 'submit', 'retryScript', 'retryAudio', 'audioUrl'],
    );
  }

  it('loads an exercise for a day', async () => {
    const repository = repo();
    repository.get.and.resolveTo(exercise);
    const facade = new ListeningPracticeFacade(repository);

    await facade.load('2026-07-30');

    expect(facade.exerciseState()).toBe('ready');
    expect(facade.exercise()?.status).toBe('ready');
  });

  it('submits answers for the loaded day', async () => {
    const repository = repo();
    repository.get.and.resolveTo(exercise);
    repository.submit.and.resolveTo(result);
    const facade = new ListeningPracticeFacade(repository);
    await facade.load('2026-07-30');

    await facade.submit([1]);

    expect(repository.submit).toHaveBeenCalledWith('2026-07-30', [1]);
    expect(facade.result()?.scriptText).toBe('A script.');
  });

  it('retries the script for the loaded day', async () => {
    const repository = repo();
    repository.get.and.resolveTo({ ...exercise, status: 'script_failed' });
    repository.retryScript.and.resolveTo(exercise);
    const facade = new ListeningPracticeFacade(repository);
    await facade.load('2026-07-30');

    await facade.retryScript();

    expect(repository.retryScript).toHaveBeenCalledWith('2026-07-30');
    expect(facade.exercise()?.status).toBe('ready');
  });

  it('retries the audio for the loaded day without touching the script', async () => {
    const repository = repo();
    repository.get.and.resolveTo({ ...exercise, status: 'audio_failed' });
    repository.retryAudio.and.resolveTo(exercise);
    const facade = new ListeningPracticeFacade(repository);
    await facade.load('2026-07-30');

    await facade.retryAudio();

    expect(repository.retryAudio).toHaveBeenCalledWith('2026-07-30');
    expect(repository.retryScript).not.toHaveBeenCalled();
  });

  it('sets error state when loading fails', async () => {
    const repository = repo();
    repository.get.and.rejectWith(new Error('offline'));
    const facade = new ListeningPracticeFacade(repository);

    await facade.load('2026-07-30');

    expect(facade.exerciseState()).toBe('error');
  });
});
