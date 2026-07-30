import { TestBed } from '@angular/core/testing';
import { ReviewGroupedComponent } from './review-grouped.component';

describe('ReviewGroupedComponent', () => {
  it('ranks all categories and emits the selected category', () => {
    const fixture = TestBed.createComponent(ReviewGroupedComponent);
    fixture.componentRef.setInput('groups', [
      { reasonCategory: 'wrong_grammar', count: 1 },
      { reasonCategory: 'carelessness', count: 3 },
    ]);
    const selected = jasmine.createSpy('selected');
    fixture.componentInstance.selected.subscribe(selected);
    fixture.detectChanges();

    const buttons = fixture.nativeElement.querySelectorAll('button');
    expect(buttons[0].textContent).toContain('Carelessness');
    expect(buttons[0].textContent).toContain('3');
    expect(buttons[1].textContent).toContain('1');
    buttons[1].click();
    expect(selected).toHaveBeenCalledWith('wrong_grammar');
  });
});
