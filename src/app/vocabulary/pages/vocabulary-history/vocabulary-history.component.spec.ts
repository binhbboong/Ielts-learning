import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { VocabularyRepository } from '../../data/vocabulary.repository';
import { VocabularyHistoryComponent } from './vocabulary-history.component';

async function setUp(
  repositoryOverrides: Partial<jasmine.SpyObj<VocabularyRepository>> = {},
) {
  const repository = jasmine.createSpyObj<VocabularyRepository>(
    'VocabularyRepository', ['getHistory'],
  );
  repository.getHistory.and.resolveTo({ days: [] });
  Object.assign(repository, repositoryOverrides);

  await TestBed.configureTestingModule({
    imports: [VocabularyHistoryComponent],
    providers: [
      provideRouter([]),
      { provide: VocabularyRepository, useValue: repository },
    ],
  }).compileComponents();
  const fixture = TestBed.createComponent(VocabularyHistoryComponent);
  return { fixture, component: fixture.componentInstance, repository };
}

describe('VocabularyHistoryComponent', () => {
  it('loads history on init', async () => {
    const { fixture, repository } = await setUp();
    await fixture.componentInstance.ngOnInit();
    expect(repository.getHistory).toHaveBeenCalled();
  });

  it('exposes days with added and reviewed words', async () => {
    const { component } = await setUp({
      getHistory: jasmine.createSpy().and.resolveTo({
        days: [
          {
            day: '2026-07-30',
            wordsAdded: [{ word: 'mitigate', meaning: 'make less severe' }],
            wordsReviewed: [
              { word: 'mitigate', outcome: 'remembered', assessedAt: '2026-07-30T10:00:00Z' },
            ],
          },
        ],
      }) as any,
    });
    await component.ngOnInit();

    expect(component.facade.history()?.days.length).toBe(1);
  });

  it('shows an empty state when there is no history yet', async () => {
    const { component } = await setUp();
    await component.ngOnInit();

    expect(component.facade.history()?.days.length).toBe(0);
  });
});
