import { PracticeResultRepository } from '../data/practice-result.repository';
import { PracticeResultCreate } from '../models/practice-result.model';
import { PracticeLogFacade } from './practice-log.facade';

describe('PracticeLogFacade', () => {
  const payload: PracticeResultCreate = {
    skill: 'Reading',
    source: 'Cambridge 18',
    score: 32,
    total: 40,
    timeTakenSeconds: 3600,
    missedQuestionTypes: ['matching_headings'],
    note: 'Review this type',
  };

  it('moves from filled to saving to confirmed and retains the saved result', async () => {
    const repository = jasmine.createSpyObj<PracticeResultRepository>(
      'PracticeResultRepository', ['create'],
    );
    repository.create.and.resolveTo({
      ...payload,
      id: 'result-1',
      loggedAt: '2026-07-29T10:00:00Z',
    });
    const facade = new PracticeLogFacade(repository);

    facade.fill(payload);
    const saving = facade.submit();
    expect(facade.submissionState()).toBe('saving');
    await saving;

    expect(facade.submissionState()).toBe('confirmed');
    expect(facade.savedResult()?.score).toBe(32);
  });

  it('retains every field after failure and retries the same payload', async () => {
    const repository = jasmine.createSpyObj<PracticeResultRepository>(
      'PracticeResultRepository', ['create'],
    );
    repository.create.and.rejectWith(new Error('offline'));
    const facade = new PracticeLogFacade(repository);

    facade.fill(payload);
    await expectAsync(facade.submit()).toBeRejected();
    expect(facade.submissionState()).toBe('error');
    expect(facade.draft()).toEqual(payload);

    repository.create.and.resolveTo({
      ...payload,
      id: 'result-1',
      loggedAt: '2026-07-29T10:00:00Z',
    });
    await facade.retry();
    expect(repository.create.calls.allArgs()).toEqual([[payload], [payload]]);
    expect(facade.submissionState()).toBe('confirmed');
  });
});
