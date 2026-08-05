import { DailyLessonRepository } from '../data/daily-lesson.repository';
import { DailyLessonFacade } from './daily-lesson.facade';
import { SkillOverviewEntry } from '../models/daily-focus.model';

const overviewContext = {
  examType: 'ielts_academic',
  week: 1,
  phase: 'foundation',
  targetBand: 4.5,
  totalMinutes: 60,
  reviewMinutes: 10,
  effectiveDay: '2026-07-30',
  checkpoint: {
    day: '2026-07-30',
    skills: { reading: false, listening: false, writing: false, speaking: false },
    vocabularyQuiz: false,
    passedCount: 0,
    requiredCount: 5,
    allPassed: false,
  },
};

function skill(
  name: SkillOverviewEntry['skill'],
  status: SkillOverviewEntry['status'],
): SkillOverviewEntry {
  return {
    day: '2026-07-30',
    skill: name,
    status,
    focusReference: null,
    targetBand: 4.5,
    estimatedMinutes: 25,
    priority: 'primary',
    phase: 'foundation',
    rationale: 'Scheduled rotation',
    generatedPromptText: null,
    taskType: null,
  };
}

describe('DailyLessonFacade', () => {
  function repo() {
    return jasmine.createSpyObj<DailyLessonRepository>(
      'DailyLessonRepository', ['getOverview', 'retry'],
    );
  }

  it('loads the overview', async () => {
    const repository = repo();
    repository.getOverview.and.resolveTo({
      ...overviewContext,
      skills: [skill('reading', 'ready')],
    });
    const facade = new DailyLessonFacade(repository);

    await facade.load();

    expect(facade.state()).toBe('ready');
    expect(facade.overview()?.skills.length).toBe(1);
  });

  it('sets error state when loading fails', async () => {
    const repository = repo();
    repository.getOverview.and.rejectWith(new Error('offline'));
    const facade = new DailyLessonFacade(repository);

    await facade.load();

    expect(facade.state()).toBe('error');
  });

  it('retries a skill and refreshes just that entry in place', async () => {
    const repository = repo();
    repository.getOverview.and.resolveTo({
      ...overviewContext,
      skills: [
        skill('reading', 'failed'),
        skill('listening', 'ready'),
      ],
    });
    repository.retry.and.resolveTo(skill('reading', 'ready'));
    const facade = new DailyLessonFacade(repository);
    await facade.load();

    await facade.retry('reading', '2026-07-30');

    expect(repository.retry).toHaveBeenCalledWith('reading', '2026-07-30');
    const reading = facade.overview()?.skills.find((s) => s.skill === 'reading');
    expect(reading?.status).toBe('ready');
    const listening = facade.overview()?.skills.find((s) => s.skill === 'listening');
    expect(listening?.status).toBe('ready');
  });
});
