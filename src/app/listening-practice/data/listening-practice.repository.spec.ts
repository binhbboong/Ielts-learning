import { of, throwError } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import { ListeningPracticeRepository } from './listening-practice.repository';

describe('ListeningPracticeRepository', () => {
  it('maps get, submit, retryScript, and retryAudio endpoints', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    api.get.and.returnValue(of({
      day: '2026-07-30', status: 'ready', focus_reference: "the word 'nevertheless'",
      phase: 'development', target_minutes: 38,
      sections: [
        {
          id: 's1', context_type: 'monologue', script_text: null, order: 1,
          questions: [
            {
              id: 'q1', question_text: 'What is discussed?', question_type: 'multiple_choice',
              options: ['A', 'B', 'C', 'D'], group_instructions: null, order: 1,
            },
          ],
        },
      ],
    }));
    api.post.and.returnValues(
      of({
        day: '2026-07-30', score: 1, total: 1,
        sections: [
          { id: 's1', context_type: 'monologue', script_text: 'A script.', order: 1, questions: [] },
        ],
        answers: [
          {
            question_text: 'What is discussed?', question_type: 'multiple_choice',
            options: ['A', 'B', 'C', 'D'], learner_answer: 1, correct_answer: 1, correct: true,
          },
        ],
      }),
      of({
        day: '2026-07-30', status: 'script_generated', focus_reference: "the word 'nevertheless'",
        sections: [],
      }),
      of({
        day: '2026-07-30', status: 'ready', focus_reference: "the word 'nevertheless'",
        sections: [],
      }),
    );
    const repository = new ListeningPracticeRepository(api);

    const exercise = await repository.get('2026-07-30');
    expect(exercise.sections[0].questions[0].questionText).toBe('What is discussed?');
    expect(exercise.phase).toBe('development');
    expect(exercise.targetMinutes).toBe(38);

    const result = await repository.submit('2026-07-30', [1]);
    expect(result.score).toBe(1);
    expect(result.sections[0].scriptText).toBe('A script.');

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

  it('builds the audio URL for a given day and section order', () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    const repository = new ListeningPracticeRepository(api);

    expect(repository.audioUrl('2026-07-30', 2)).toBe(
      '/api/listening-practice/2026-07-30/audio/2',
    );
  });

  it('defaults phase and targetMinutes to null when absent', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    api.get.and.returnValue(of({
      day: '2026-07-30', status: 'ready', focus_reference: null, sections: [],
    }));
    const repository = new ListeningPracticeRepository(api);

    const exercise = await repository.get('2026-07-30');

    expect(exercise.phase).toBeNull();
    expect(exercise.targetMinutes).toBeNull();
  });

  it('propagates failures', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    api.get.and.returnValue(throwError(() => new Error('offline')));
    await expectAsync(
      new ListeningPracticeRepository(api).get('2026-07-30'),
    ).toBeRejected();
  });
});
