import { of, throwError } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import { DailyLessonRepository } from './daily-lesson.repository';

describe('DailyLessonRepository', () => {
  it('maps the overview and retry endpoints', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    api.get.and.returnValue(of({
      skills: [
        { day: '2026-07-30', skill: 'reading', status: 'ready', focus_reference: "the word 'nevertheless'" },
        { day: '2026-07-30', skill: 'listening', status: 'generating', focus_reference: null },
      ],
    }));
    api.post.and.returnValue(of({
      day: '2026-07-30', skill: 'reading', status: 'ready', focus_reference: null,
    }));
    const repository = new DailyLessonRepository(api);

    const overview = await repository.getOverview();
    expect(overview.skills.length).toBe(2);
    expect(overview.skills[0].focusReference).toBe("the word 'nevertheless'");

    const retried = await repository.retry('reading', '2026-07-30');
    expect(retried.status).toBe('ready');

    expect(api.get).toHaveBeenCalledWith('/api/daily-lesson/overview');
    expect(api.post).toHaveBeenCalledWith(
      '/api/daily-lesson/reading/retry?day=2026-07-30', {},
    );
  });

  it('propagates failures', async () => {
    const api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'post']);
    api.get.and.returnValue(throwError(() => new Error('offline')));
    await expectAsync(new DailyLessonRepository(api).getOverview()).toBeRejected();
  });
});
