import { PracticeResultRepository } from '../data/practice-result.repository';
import { ProgressTrendFacade } from './progress-trend.facade';

describe('ProgressTrendFacade', () => {
  it('loads on filter changes and manual refresh only', async () => {
    const repository = jasmine.createSpyObj<PracticeResultRepository>(
      'PracticeResultRepository', ['getTrend'],
    );
    repository.getTrend.and.resolveTo({
      sessionCount: 4,
      averageScorePercentage: 80,
      direction: 'up',
      threshold: { sufficient: true, count: 4, remaining: 0 },
      breakdown: [],
    });
    const facade = new ProgressTrendFacade(repository);

    await facade.load();
    await facade.setSkill('Reading');
    await facade.setPeriod('4_weeks');
    expect(repository.getTrend.calls.allArgs()).toEqual([
      ['Both', '8_weeks'],
      ['Reading', '8_weeks'],
      ['Reading', '4_weeks'],
    ]);

    await Promise.resolve();
    expect(repository.getTrend).toHaveBeenCalledTimes(3);
    await facade.refresh();
    expect(repository.getTrend).toHaveBeenCalledTimes(4);
  });
});
