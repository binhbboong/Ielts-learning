import { of, throwError } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import { WritingCoachRepository } from './writing-coach.repository';

describe('WritingCoachRepository', () => {
  it('maps submit, list, and detail endpoints', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    api.post.and.returnValue(of({
      id: 'w1', created_at: '2026-07-29T10:00:00Z', task_type: 'task2',
      question_text: 'Prompt', response_text: 'Essay', status: 'failed',
      task_response: null, coherence_and_cohesion: null, lexical_resource: null,
      grammatical_range_and_accuracy: null, overall_band: null, corrections: null,
      error_message: 'offline',
    }));
    api.get.and.returnValues(
      of([{ id: 'w1', created_at: '2026-07-29T10:00:00Z', task_type: 'task2',
        status: 'failed', overall_band: null, task_response_score: null,
        question_excerpt: 'Prompt' }]),
      of({ id: 'w1', created_at: '2026-07-29T10:00:00Z', task_type: 'task2',
        question_text: 'Prompt', response_text: 'Essay', status: 'failed',
        task_response: null, coherence_and_cohesion: null, lexical_resource: null,
        grammatical_range_and_accuracy: null, overall_band: null, corrections: null,
        error_message: 'offline' }),
    );
    const repository = new WritingCoachRepository(api);
    expect((await repository.submit({
      taskType: 'task2', questionText: 'Prompt', responseText: 'Essay',
    })).responseText).toBe('Essay');
    expect((await repository.list())[0].questionExcerpt).toBe('Prompt');
    expect((await repository.get('w1')).errorMessage).toBe('offline');
  });

  it('propagates failures', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    api.get.and.returnValue(throwError(() => new Error('offline')));
    await expectAsync(new WritingCoachRepository(api).list()).toBeRejected();
  });
});
