import { of, throwError } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import { ReadingPracticeRepository } from './reading-practice.repository';

describe('ReadingPracticeRepository', () => {
  it('maps get, submit, and retry endpoints', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    api.get.and.returnValue(of({
      day: '2026-07-30', status: 'ready', focus_reference: "the word 'nevertheless'",
      passages: [
        {
          id: 'p1', title: null, passage_text: 'A passage.', order: 1,
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
        day: '2026-07-30', score: 1, total: 1, answers: [
          {
            question_text: 'What is discussed?', question_type: 'multiple_choice',
            options: ['A', 'B', 'C', 'D'], learner_answer: 1, correct_answer: 1, correct: true,
          },
        ],
      }),
      of({
        day: '2026-07-30', status: 'ready', focus_reference: "the word 'nevertheless'",
        passages: [
          {
            id: 'p1', title: null, passage_text: 'A new passage.', order: 1, questions: [],
          },
        ],
      }),
    );
    const repository = new ReadingPracticeRepository(api);

    const exercise = await repository.get('2026-07-30');
    expect(exercise.passages[0].passageText).toBe('A passage.');
    expect(exercise.passages[0].questions[0].questionText).toBe('What is discussed?');

    const result = await repository.submit('2026-07-30', [1]);
    expect(result.score).toBe(1);
    expect(result.answers[0].correct).toBeTrue();

    const retried = await repository.retry('2026-07-30');
    expect(retried.passages[0].passageText).toBe('A new passage.');

    expect(api.get).toHaveBeenCalledWith('/api/reading-practice/2026-07-30');
    expect(api.post).toHaveBeenCalledWith(
      '/api/reading-practice/2026-07-30/submit', { answers: [1] },
    );
    expect(api.post).toHaveBeenCalledWith(
      '/api/reading-practice/2026-07-30/retry', {},
    );
  });

  it('propagates failures', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    api.get.and.returnValue(throwError(() => new Error('offline')));
    await expectAsync(
      new ReadingPracticeRepository(api).get('2026-07-30'),
    ).toBeRejected();
  });
});
