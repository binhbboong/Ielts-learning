import { TestBed } from '@angular/core/testing';
import { ReviewCategoryDetailComponent } from './review-category-detail.component';

describe('ReviewCategoryDetailComponent', () => {
  it('renders concrete answers including a missing correct answer', () => {
    const fixture = TestBed.createComponent(ReviewCategoryDetailComponent);
    fixture.componentRef.setInput('items', [
      {
        ownAnswer: 'A',
        correctAnswer: null,
        explanation: 'I guessed.',
      },
    ]);
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('A');
    expect(fixture.nativeElement.textContent).toContain('Not known yet');
    expect(fixture.nativeElement.textContent).toContain('I guessed.');
  });
});
