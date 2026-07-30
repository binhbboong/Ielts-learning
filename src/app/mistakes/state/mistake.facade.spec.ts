import { MistakeRepository } from '../data/mistake.repository';
import { MistakeFacade } from './mistake.facade';

describe('MistakeFacade', () => {
  it('loads the default list and refetches when period or view changes', async () => {
    const repository = jasmine.createSpyObj<MistakeRepository>('MistakeRepository', [
      'create',
      'listChronological',
      'listGrouped',
      'getCategoryDetail',
    ]);
    repository.listChronological.and.resolveTo([]);
    repository.listGrouped.and.resolveTo([
      { reasonCategory: 'carelessness', count: 2 },
    ]);
    const facade = new MistakeFacade(repository);

    await facade.load();
    expect(facade.selectedPeriod()).toBe('this_week');
    expect(repository.listChronological).toHaveBeenCalled();

    await facade.selectPeriod('last_week');
    expect(repository.listChronological).toHaveBeenCalledTimes(2);

    await facade.setViewMode('grouped');
    expect(repository.listGrouped).toHaveBeenCalled();
    expect(facade.grouped()).toEqual([
      { reasonCategory: 'carelessness', count: 2 },
    ]);
  });
});
