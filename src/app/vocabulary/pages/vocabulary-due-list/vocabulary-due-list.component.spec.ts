import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { VocabularyFacade } from '../../state/vocabulary.facade';
import { VocabularyDueListComponent } from './vocabulary-due-list.component';

function setup(state: 'loading' | 'ready' | 'error', summary: any) {
  const facade = {
    dueLoadState: signal(state),
    dueSummary: signal(summary),
    loadDueSummary: jasmine.createSpy('loadDueSummary').and.resolveTo(undefined),
    addWord: jasmine.createSpy('addWord'),
  };
  TestBed.configureTestingModule({
    imports: [VocabularyDueListComponent],
    providers: [{ provide: VocabularyFacade, useValue: facade }],
  });
  return TestBed.createComponent(VocabularyDueListComponent);
}

describe('VocabularyDueListComponent', () => {
  it('renders due count, breakdown and both actions when populated', () => {
    const fixture = setup('ready', {
      totalDue: 2,
      byInterval: { '1_day': 2 },
      byTopic: { Environment: 2 },
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

  it('distinguishes positive empty from error and always offers add', () => {
    const empty = setup('ready', { totalDue: 0, byInterval: {}, byTopic: {} });
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
});
