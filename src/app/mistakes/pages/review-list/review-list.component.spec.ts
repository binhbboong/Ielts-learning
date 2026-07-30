import { TestBed } from '@angular/core/testing';
import { ReviewListComponent } from './review-list.component';

describe('ReviewListComponent', () => {
  it('renders newest first and distinguishes incomplete entries', () => {
    const fixture = TestBed.createComponent(ReviewListComponent);
    fixture.componentRef.setInput('entries', [
      {
        id: '1',
        skill: 'reading',
        questionType: null,
        source: 'Old',
        ownAnswer: null,
        correctAnswer: null,
        explanation: null,
        reasonCategory: 'not_sure_other',
        loggedAt: '2026-07-20T00:00:00Z',
        isIncomplete: true,
      },
      {
        id: '2',
        skill: 'writing',
        questionType: null,
        source: 'New',
        ownAnswer: 'A',
        correctAnswer: 'B',
        explanation: null,
        reasonCategory: 'wrong_grammar',
        loggedAt: '2026-07-29T00:00:00Z',
        isIncomplete: false,
      },
    ]);
    fixture.detectChanges();

    const rows = fixture.nativeElement.querySelectorAll('li');
    expect(rows[0].textContent).toContain('Writing');
    expect(rows[1].textContent).toContain('Incomplete');
    expect(rows[1].textContent).toContain('Not sure yet / other');
  });
});
