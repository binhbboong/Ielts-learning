import { VocabularyRepository } from '../data/vocabulary.repository';
import { VocabularyFacade } from './vocabulary.facade';

describe('VocabularyFacade', () => {
  it('resumes, auto-advances, and adds without changing review state', async () => {
    const repository = jasmine.createSpyObj<VocabularyRepository>(
      'VocabularyRepository',
      [
        'addWord',
        'getDueSummary',
        'startOrResumeReview',
        'getCurrentItem',
        'assessCurrentItem',
        'getRecommendations',
        'addRecommendation',
      ],
    );
    const first = {
      status: 'item' as const,
      item: {
        sessionId: 's',
        itemId: 'i1',
        wordId: 'w1',
        word: 'first',
        meaning: 'one',
        example: null,
        position: 0,
        total: 2,
        isNew: false,
      },
    };
    const second = {
      status: 'item' as const,
      item: { ...first.item, itemId: 'i2', word: 'second', position: 1 },
    };
    repository.startOrResumeReview.and.resolveTo(first);
    repository.assessCurrentItem.and.resolveTo(second);
    repository.addWord.and.resolveTo({} as never);
    repository.getRecommendations.and.resolveTo({
      currentBand: 4.5,
      cefrLevel: 'B1',
      phase: 'foundation',
      week: 1,
      recommendations: [],
    });
    repository.getDueSummary.and.resolveTo({
      totalDue: 0,
      byInterval: {},
      byTopic: {},
      dailyTarget: 20,
      backfillCount: 20,
      shortfall: false,
    });
    repository.addRecommendation.and.resolveTo({} as never);
    const facade = new VocabularyFacade(repository);

    await facade.startOrResumeReview();
    expect(facade.reviewState()).toEqual(first);
    await facade.assessCurrentItem('remembered');
    expect(facade.reviewState()).toEqual(second);
    await facade.addWord({ word: 'new', meaning: 'meaning' });
    expect(facade.reviewState()).toEqual(second);
    await facade.loadRecommendations();
    expect(facade.recommendations()?.cefrLevel).toBe('B1');
  });

  it('loads history', async () => {
    const repository = jasmine.createSpyObj<VocabularyRepository>(
      'VocabularyRepository', ['getHistory'],
    );
    repository.getHistory.and.resolveTo({
      days: [
        {
          day: '2026-07-30',
          wordsAdded: [{ word: 'mitigate', meaning: 'make less severe' }],
          wordsReviewed: [],
        },
      ],
    });
    const facade = new VocabularyFacade(repository);

    await facade.loadHistory();

    expect(facade.historyLoadState()).toBe('ready');
    expect(facade.history()?.days.length).toBe(1);
  });

  it('sets error state when history fails to load', async () => {
    const repository = jasmine.createSpyObj<VocabularyRepository>(
      'VocabularyRepository', ['getHistory'],
    );
    repository.getHistory.and.rejectWith(new Error('offline'));
    const facade = new VocabularyFacade(repository);

    await expectAsync(facade.loadHistory()).toBeRejected();

    expect(facade.historyLoadState()).toBe('error');
  });
});
