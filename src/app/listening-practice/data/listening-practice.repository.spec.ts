import { of, throwError } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import { ListeningPracticeRepository } from './listening-practice.repository';

describe('ListeningPracticeRepository', () => {
  it('maps get, submit, retryScript, and retryAudio endpoints', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    api.get.and.returnValue(of({
      day: '2026-07-30', status: 'ready', focus_reference: "the word 'nevertheless'",
      script_text: null, questions: [
        { id: 'q1', question_text: 'What is discussed?', options: ['A', 'B', 'C', 'D'], order: 1 },
      ],
    }));
    api.post.and.returnValues(
      of({
        day: '2026-07-30', score: 1, total: 1, script_text: 'A script.', answers: [
          {
            question_text: 'What is discussed?', options: ['A', 'B', 'C', 'D'],
            learner_answer_index: 1, correct_option_index: 1, correct: true,
          },
        ],
      }),
      of({
        day: '2026-07-30', status: 'script_generated', focus_reference: "the word 'nevertheless'",
        script_text: null, questions: [],
      }),
      of({
        day: '2026-07-30', status: 'ready', focus_reference: "the word 'nevertheless'",
        script_text: null, questions: [],
      }),
    );
    const repository = new ListeningPracticeRepository(api);

    const exercise = await repository.get('2026-07-30');
    expect(exercise.questions[0].questionText).toBe('What is discussed?');

    const result = await repository.submit('2026-07-30', [1]);
    expect(result.score).toBe(1);
    expect(result.scriptText).toBe('A script.');

    const retriedScript = await repository.retryScript('2026-07-30');
    expect(retriedScript.status).toBe('script_generated');

    const retriedAudio = await repository.retryAudio('2026-07-30');
    expect(retriedAudio.status).toBe('ready');

    expect(api.get).toHaveBeenCalledWith('/api/listening-practice/2026-07-30');
    expect(api.post).toHaveBeenCalledWith(
      '/api/listening-practice/2026-07-30/submit', { answers: [1] },
    );
    expect(api.post).toHaveBeenCalledWith(
      '/api/listening-practice/2026-07-30/retry-script', {},
    );
    expect(api.post).toHaveBeenCalledWith(
      '/api/listening-practice/2026-07-30/retry-audio', {},
    );
  });

  it('builds the audio URL for a given day', () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    const repository = new ListeningPracticeRepository(api);

    expect(repository.audioUrl('2026-07-30')).toBe(
      '/api/listening-practice/2026-07-30/audio',
    );
  });

  it('propagates failures', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    api.get.and.returnValue(throwError(() => new Error('offline')));
    await expectAsync(
      new ListeningPracticeRepository(api).get('2026-07-30'),
    ).toBeRejected();
  });
});
