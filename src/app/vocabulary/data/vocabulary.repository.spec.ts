import { of, throwError } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import { VocabularyRepository } from './vocabulary.repository';

describe('VocabularyRepository', () => {
  it('calls every vocabulary endpoint with mapped payloads', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    const repository = new VocabularyRepository(api);
    api.post.and.returnValues(
      of({
        saved: true,
        word: {
          id: 'word-1',
          word: 'ubiquitous',
          meaning: 'everywhere',
          example: null,
          topic: null,
          interval_index: 0,
          next_due_date: '2026-07-30',
          created_at: '2026-07-29T00:00:00Z',
          last_reviewed_at: null,
        },
      }),
      of({ status: 'nothing_due' }),
      of({
        status: 'item',
        item: {
          session_id: 'session-1',
          item_id: 'item-1',
          word_id: 'word-1',
          word: 'ubiquitous',
          meaning: 'everywhere',
          example: null,
          position: 0,
          total: 1,
          is_new: false,
        },
      }),
    );
    api.get.and.returnValues(
      of({
        total_due: 2,
        by_interval: { '1_day': 2 },
        by_topic: { Environment: 2 },
        daily_target: 20,
        backfill_count: 18,
        shortfall: false,
      }),
      of({ status: 'nothing_due' }),
    );

    const added = await repository.addWord({
      word: 'ubiquitous',
      meaning: 'everywhere',
    });
    expect(added.word.intervalIndex).toBe(0);
    expect(await repository.getDueSummary()).toEqual({
      totalDue: 2,
      byInterval: { '1_day': 2 },
      byTopic: { Environment: 2 },
      dailyTarget: 20,
      backfillCount: 18,
      shortfall: false,
    });
    expect(await repository.startOrResumeReview()).toEqual({
      status: 'nothing_due',
    });
    expect(await repository.getCurrentItem()).toEqual({
      status: 'nothing_due',
    });
    expect(
      await repository.assessCurrentItem('remembered'),
    ).toEqual(jasmine.objectContaining({ status: 'item' }));
    expect(api.post).toHaveBeenCalledWith('/api/vocabulary/words', {
      word: 'ubiquitous',
      meaning: 'everywhere',
    });
    expect(api.post).toHaveBeenCalledWith(
      '/api/vocabulary/review/current/assess',
      { outcome: 'remembered' },
    );
  });

  it('propagates request failures', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    api.get.and.returnValue(throwError(() => new Error('offline')));
    const repository = new VocabularyRepository(api);
    await expectAsync(repository.getDueSummary()).toBeRejected();
  });

  it('keeps the selected make-up day on review and quiz requests', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    api.post.and.returnValues(
      of({ status: 'nothing_due' }),
      of({ status: 'nothing_due' }),
      of({ status: 'not_ready' }),
      of({ status: 'not_ready' }),
    );
    const repository = new VocabularyRepository(api);
    const day = '2026-07-29';

    await repository.startOrResumeReview(day);
    await repository.assessCurrentItem('remembered', day);
    await repository.startQuiz(day);
    await repository.answerQuizItem(1, day);

    expect(api.post).toHaveBeenCalledWith(
      '/api/vocabulary/review/start?day=2026-07-29', {},
    );
    expect(api.post).toHaveBeenCalledWith(
      '/api/vocabulary/review/current/assess?day=2026-07-29',
      { outcome: 'remembered' },
    );
    expect(api.post).toHaveBeenCalledWith(
      '/api/vocabulary/quiz/start?day=2026-07-29', {},
    );
    expect(api.post).toHaveBeenCalledWith(
      '/api/vocabulary/quiz/current/answer?day=2026-07-29',
      { selected_option_index: 1 },
    );
  });

  it('maps the history endpoint', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    api.get.and.returnValue(of({
      days: [
        {
          day: '2026-07-30',
          words_added: [{ word: 'mitigate', meaning: 'make less severe' }],
          words_reviewed: [
            { word: 'mitigate', outcome: 'remembered', assessed_at: '2026-07-30T10:00:00Z' },
          ],
        },
      ],
    }));
    const repository = new VocabularyRepository(api);

    const history = await repository.getHistory();

    expect(api.get).toHaveBeenCalledWith('/api/vocabulary/history');
    expect(history.days.length).toBe(1);
    expect(history.days[0].wordsAdded[0].word).toBe('mitigate');
    expect(history.days[0].wordsReviewed[0].outcome).toBe('remembered');
  });
});
