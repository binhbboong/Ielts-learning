import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { VocabularyFacade } from '../../state/vocabulary.facade';
import { VocabularyDueListComponent } from './vocabulary-due-list.component';

function setup(state: 'loading' | 'ready' | 'error', summary: any) {
  const facade = {
    dueLoadState: signal(state),
    dueSummary: signal(summary),
    loadDueSummary: jasmine.createSpy('loadDueSummary').and.resolveTo(undefined),
    addWord: jasmine.createSpy('addWord'),
    recommendations: signal<any>(null),
    recommendationsLoadState: signal('ready'),
    loadRecommendations: jasmine
      .createSpy('loadRecommendations')
      .and.resolveTo(undefined),
    addRecommendation: jasmine
      .createSpy('addRecommendation')
      .and.resolveTo(undefined),
  };
  TestBed.configureTestingModule({
    imports: [VocabularyDueListComponent],
    providers: [provideRouter([]), { provide: VocabularyFacade, useValue: facade }],
  });
  return TestBed.createComponent(VocabularyDueListComponent);
}

describe('VocabularyDueListComponent', () => {
  it('renders due count, breakdown and both actions when populated', () => {
    const fixture = setup('ready', {
      totalDue: 2,
      byInterval: { '1_day': 2 },
      byTopic: { Environment: 2 },
      dailyTarget: 20,
      backfillCount: 18,
      shortfall: false,
    });
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('2 words due');
    expect(text).toContain('Environment');
    expect(text).toContain('Start review');
    expect(text).toContain('Add a word');
    fixture.componentInstance.addPanelOpen.set(true);
    fixture.componentInstance.wordSaved();
    fixture.detectChanges();
    expect(fixture.componentInstance.addPanelOpen()).toBeFalse();
    expect(fixture.nativeElement.textContent).toContain(
      'Word added to your review schedule',
    );
  });

  it('links to the vocabulary history page', () => {
    const fixture = setup('ready', {
      totalDue: 0,
      byInterval: {},
      byTopic: {},
      dailyTarget: 20,
      backfillCount: 0,
      shortfall: false,
    });
    fixture.detectChanges();
    const link: HTMLAnchorElement | null =
      fixture.nativeElement.querySelector('a[href="/vocabulary/history"]');
    expect(link).not.toBeNull();
  });

  it('distinguishes positive empty from error and always offers add', () => {
    const empty = setup('ready', {
      totalDue: 0,
      byInterval: {},
      byTopic: {},
      dailyTarget: 20,
      backfillCount: 0,
      shortfall: false,
    });
    empty.detectChanges();
    expect(empty.nativeElement.textContent).toContain('You are on schedule');
    expect(empty.nativeElement.textContent).not.toContain('Start review');
    expect(empty.nativeElement.textContent).toContain('Add a word');

    TestBed.resetTestingModule();
    const failed = setup('error', null);
    failed.detectChanges();
    expect(failed.nativeElement.textContent).toContain('could not load');
    expect(failed.nativeElement.textContent).not.toContain('0 words due');
  });

  it('offers Start review when zero words are due but backfill words are available', () => {
    const fixture = setup('ready', {
      totalDue: 0,
      byInterval: {},
      byTopic: {},
      dailyTarget: 20,
      backfillCount: 20,
      shortfall: false,
    });
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent;
    expect(text).not.toContain('You are on schedule');
    expect(text).toContain('Start review');
    expect(text).toContain('20 new words');
    expect(text).toContain("today's target of 20");
  });

  it('shows a shortfall message when fewer backfill words remain than needed', () => {
    const fixture = setup('ready', {
      totalDue: 3,
      byInterval: { '1_day': 3 },
      byTopic: {},
      dailyTarget: 20,
      backfillCount: 5,
      shortfall: true,
    });
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('5 new words');
    expect(text).toContain('Not enough level-matched words remain');
  });

  it('shows level context and adds a recommended word', async () => {
    const fixture = setup('ready', {
      totalDue: 0,
      byInterval: {},
      byTopic: {},
      dailyTarget: 20,
      backfillCount: 20,
      shortfall: false,
    });
    const facade = fixture.componentInstance.facade as any;
    facade.recommendations.set({
      currentBand: 4.5,
      cefrLevel: 'B1',
      phase: 'foundation',
      week: 1,
      recommendations: [{
        key: '4.5:essential',
        word: 'essential',
        meaning: 'completely necessary',
        example: 'Reliable internet is essential.',
        topic: 'Education',
        targetBand: 4.5,
        cefrLevel: 'B1',
      }],
    });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('IELTS band 4.5');
    expect(fixture.nativeElement.textContent).toContain('CEFR B1');
    expect(fixture.nativeElement.textContent).toContain('essential');
    await fixture.componentInstance.addRecommendation('4.5:essential');
    expect(facade.addRecommendation).toHaveBeenCalledWith('4.5:essential');
  });
});
