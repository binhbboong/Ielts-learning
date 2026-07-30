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
      },
    };
    const second = {
      status: 'item' as const,
      item: { ...first.item, itemId: 'i2', word: 'second', position: 1 },
    };
    repository.startOrResumeReview.and.resolveTo(first);
    repository.assessCurrentItem.and.resolveTo(second);
    repository.addWord.and.resolveTo({} as never);
    const facade = new VocabularyFacade(repository);

    await facade.startOrResumeReview();
    expect(facade.reviewState()).toEqual(first);
    await facade.assessCurrentItem('remembered');
    expect(facade.reviewState()).toEqual(second);
    await facade.addWord({ word: 'new', meaning: 'meaning' });
    expect(facade.reviewState()).toEqual(second);
  });
});
