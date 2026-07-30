import { of } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import { MistakeRepository } from './mistake.repository';

describe('MistakeRepository', () => {
  it('maps create/list/group/detail API contracts', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['post', 'get']);
    const repository = new MistakeRepository(api);
    const apiEntry = {
      id: '7cccf99f-f331-4d56-b553-bf73d20c868c',
      skill: 'reading',
      question_type: 'matching',
      source: 'Book',
      own_answer: 'A',
      correct_answer: 'B',
      explanation: 'Missed synonym',
      reason_category: 'missed_paraphrase',
      logged_at: '2026-07-29T00:00:00Z',
      is_incomplete: false,
    };
    api.post.and.returnValue(of(apiEntry));
    api.get.and.returnValues(
      of([apiEntry]),
      of([{ reason_category: 'missed_paraphrase', count: 1 }]),
      of([
        {
          own_answer: 'A',
          correct_answer: 'B',
          explanation: 'Missed synonym',
        },
      ]),
    );
    const range = {
      start: new Date('2026-07-28T00:00:00Z'),
      end: new Date('2026-07-30T00:00:00Z'),
    };

    expect(
      await repository.create({
        skill: 'reading',
        source: 'Book',
        reasonCategory: 'missed_paraphrase',
      }),
    ).toEqual(jasmine.objectContaining({ questionType: 'matching', isIncomplete: false }));
    expect((await repository.listChronological(range))[0].loggedAt).toBe(
      '2026-07-29T00:00:00Z',
    );
    expect(await repository.listGrouped(range)).toEqual([
      { reasonCategory: 'missed_paraphrase', count: 1 },
    ]);
    expect(
      await repository.getCategoryDetail('missed_paraphrase', range),
    ).toEqual([
      { ownAnswer: 'A', correctAnswer: 'B', explanation: 'Missed synonym' },
    ]);
    expect(api.post).toHaveBeenCalledWith('/api/mistakes', {
      skill: 'reading',
      source: 'Book',
      reason_category: 'missed_paraphrase',
    });
    expect(api.get.calls.allArgs()[0][0]).toContain('/api/mistakes?start=');
    expect(api.get.calls.allArgs()[1][0]).toContain('/api/mistakes/grouped?start=');
    expect(api.get.calls.allArgs()[2][0]).toContain(
      '/api/mistakes/grouped/missed_paraphrase?start=',
    );
  });
});
