import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { VocabularyFacade } from '../../state/vocabulary.facade';
import { VocabularyReviewSessionComponent } from './vocabulary-review-session.component';

function itemState(word = 'ubiquitous', position = 0, isNew = false) {
  return {
    status: 'item' as const,
    item: {
      sessionId: 's',
      itemId: `i${position}`,
      wordId: `w${position}`,
      word,
      meaning: 'found everywhere',
      example: 'A ubiquitous device.',
      position,
      total: 2,
      isNew,
    },
  };
}

describe('VocabularyReviewSessionComponent', () => {
  it('hides answer until reveal then assesses and auto-advances', async () => {
    const reviewState = signal<any>(itemState());
    const facade = {
      reviewState,
      reviewLoadState: signal('ready'),
      startOrResumeReview: jasmine.createSpy('start').and.resolveTo(undefined),
      assessCurrentItem: jasmine
        .createSpy('assess')
        .and.callFake(async () => reviewState.set(itemState('second', 1))),
      addWord: jasmine.createSpy('addWord'),
    };
    TestBed.configureTestingModule({
      imports: [VocabularyReviewSessionComponent],
      providers: [{ provide: VocabularyFacade, useValue: facade }],
    });
    const fixture = TestBed.createComponent(VocabularyReviewSessionComponent);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).not.toContain('found everywhere');
    expect(fixture.nativeElement.textContent).not.toContain('Remembered');

    fixture.componentInstance.reveal();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('found everywhere');
    expect(fixture.nativeElement.textContent).toContain('Remembered');
    await fixture.componentInstance.assess('remembered');
    fixture.detectChanges();
    expect(facade.assessCurrentItem).toHaveBeenCalledWith('remembered');
    expect(fixture.nativeElement.textContent).toContain('second');
    expect(fixture.nativeElement.textContent).not.toContain('found everywhere');
  });

  it('renders nothing-due, error and complete as distinct states', () => {
    const reviewState = signal<any>({
      status: 'complete',
      summary: {
        totalReviewed: 3,
        remembered: 2,
        forgot: 1,
        newWordsIncluded: 0,
        reviewDatesUpdated: true,
      },
    });
    const loadState = signal('ready');
    const facade = {
      reviewState,
      reviewLoadState: loadState,
      startOrResumeReview: jasmine.createSpy('start').and.resolveTo(undefined),
      assessCurrentItem: jasmine.createSpy('assess'),
      addWord: jasmine.createSpy('addWord'),
    };
    TestBed.configureTestingModule({
      imports: [VocabularyReviewSessionComponent],
      providers: [{ provide: VocabularyFacade, useValue: facade }],
    });
    const fixture = TestBed.createComponent(VocabularyReviewSessionComponent);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('3 reviewed');
    expect(fixture.nativeElement.textContent).toContain('Review dates were updated');
    fixture.componentInstance.addPanelOpen.set(true);
    fixture.componentInstance.wordSaved();
    fixture.detectChanges();
    expect(fixture.componentInstance.addPanelOpen()).toBeFalse();
    expect(fixture.nativeElement.textContent).toContain(
      'Word added to your review schedule',
    );

    reviewState.set({ status: 'nothing_due' });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Nothing due');

    loadState.set('error');
    reviewState.set(null);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('could not load');
    expect(fixture.nativeElement.querySelector('[data-testid="recall-card"]')).toBeNull();
  });

  it('tags the recall card New word vs Review based on isNew', () => {
    const reviewState = signal<any>(itemState('ubiquitous', 0, true));
    const facade = {
      reviewState,
      reviewLoadState: signal('ready'),
      startOrResumeReview: jasmine.createSpy('start').and.resolveTo(undefined),
      assessCurrentItem: jasmine.createSpy('assess'),
      addWord: jasmine.createSpy('addWord'),
    };
    TestBed.configureTestingModule({
      imports: [VocabularyReviewSessionComponent],
      providers: [{ provide: VocabularyFacade, useValue: facade }],
    });
    const fixture = TestBed.createComponent(VocabularyReviewSessionComponent);
    fixture.detectChanges();
    const badge = fixture.nativeElement.querySelector(
      '[data-testid="recall-card-badge"]',
    ) as HTMLElement;
    expect(badge.textContent).toContain('New word');

    reviewState.set(itemState('mitigate', 0, false));
    fixture.detectChanges();
    expect(badge.textContent).toContain('Review');
    expect(badge.textContent).not.toContain('New word');
  });

  it('reports new words included when the review-complete summary has backfilled words', () => {
    const reviewState = signal<any>({
      status: 'complete',
      summary: {
        totalReviewed: 20,
        remembered: 18,
        forgot: 2,
        newWordsIncluded: 17,
        reviewDatesUpdated: true,
      },
    });
    const facade = {
      reviewState,
      reviewLoadState: signal('ready'),
      startOrResumeReview: jasmine.createSpy('start').and.resolveTo(undefined),
      assessCurrentItem: jasmine.createSpy('assess'),
      addWord: jasmine.createSpy('addWord'),
    };
    TestBed.configureTestingModule({
      imports: [VocabularyReviewSessionComponent],
      providers: [{ provide: VocabularyFacade, useValue: facade }],
    });
    const fixture = TestBed.createComponent(VocabularyReviewSessionComponent);
    fixture.detectChanges();
    expect(
      fixture.nativeElement.querySelector('[data-testid="new-words-included"]').textContent,
    ).toContain('17 of these were new words added today');
  });
});
