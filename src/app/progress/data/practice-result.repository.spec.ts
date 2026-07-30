import { of, throwError } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import { PracticeResultRepository } from './practice-result.repository';

describe('PracticeResultRepository', () => {
  it('maps create, taxonomy, trend, and history responses', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    api.post.and.returnValue(of({
      id: 'result-1',
      skill: 'Reading',
      source: 'Cambridge 18',
      score: 32,
      total: 40,
      time_taken_seconds: 3600,
      missed_question_types: ['matching_headings'],
      note: null,
      logged_at: '2026-07-29T10:00:00Z',
    }));
    api.get.and.returnValues(
      of({
        Reading: [{ key: 'matching_headings', label: 'Matching Headings' }],
        Listening: [{ key: 'multiple_choice', label: 'Multiple Choice' }],
      }),
      of({
        session_count: 4,
        average_score_percentage: 80,
        direction: 'up',
        threshold: { sufficient: true, count: 4, remaining: 0 },
        breakdown: [{ key: 'matching_headings', count: 2 }],
      }),
      of([{
        id: 'result-1',
        skill: 'Reading',
        source: 'Cambridge 18',
        score: 32,
        total: 40,
        time_taken_seconds: 3600,
        missed_question_types: [],
        note: null,
        logged_at: '2026-07-29T10:00:00Z',
      }]),
    );
    const repository = new PracticeResultRepository(api);

    const created = await repository.create({
      skill: 'Reading',
      source: 'Cambridge 18',
      score: 32,
      total: 40,
      timeTakenSeconds: 3600,
      missedQuestionTypes: ['matching_headings'],
    });
    expect(created.timeTakenSeconds).toBe(3600);
    expect((await repository.getTaxonomy()).Reading[0].key).toBe('matching_headings');
    expect((await repository.getTrend('Reading', '4_weeks')).sessionCount).toBe(4);
    expect((await repository.getHistory('Reading', 'oldest'))[0].loggedAt)
      .toBe('2026-07-29T10:00:00Z');
    expect(api.post).toHaveBeenCalledWith('/api/practice-results', {
      skill: 'Reading',
      source: 'Cambridge 18',
      score: 32,
      total: 40,
      time_taken_seconds: 3600,
      missed_question_types: ['matching_headings'],
    });
    expect(api.get).toHaveBeenCalledWith(
      '/api/practice-results/trend?skill=Reading&period=4_weeks',
    );
    expect(api.get).toHaveBeenCalledWith(
      '/api/practice-results?skill=Reading&sort=oldest',
    );
  });

  it('propagates API failures', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    api.get.and.returnValue(throwError(() => new Error('offline')));
    const repository = new PracticeResultRepository(api);
    await expectAsync(repository.getTrend('Both', '8_weeks')).toBeRejected();
  });
});
