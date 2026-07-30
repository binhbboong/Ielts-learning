import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { MistakeFacade } from '../../state/mistake.facade';
import { ReviewShellComponent } from './review-shell.component';

describe('ReviewShellComponent', () => {
  it('loads default period and refetches active view when controls change', () => {
    const facade = {
      selectedPeriod: signal('this_week'),
      viewMode: signal('list'),
      entries: signal([]),
      grouped: signal([]),
      categoryDetail: signal([]),
      load: jasmine.createSpy('load').and.resolveTo(undefined),
      selectPeriod: jasmine.createSpy('selectPeriod').and.resolveTo(undefined),
      setViewMode: jasmine.createSpy('setViewMode').and.resolveTo(undefined),
      loadCategory: jasmine.createSpy('loadCategory').and.resolveTo(undefined),
    };
    TestBed.configureTestingModule({
      imports: [ReviewShellComponent],
      providers: [{ provide: MistakeFacade, useValue: facade }],
    });
    const fixture = TestBed.createComponent(ReviewShellComponent);
    fixture.detectChanges();

    expect(facade.load).toHaveBeenCalled();
    const options = fixture.nativeElement.querySelectorAll('select option');
    expect(Array.from(options).map((item: any) => item.textContent.trim())).toEqual([
      'This week',
      'Last week',
      'Last 30 days',
    ]);

    fixture.componentInstance.changePeriod('last_week');
    fixture.componentInstance.changeView('grouped');
    expect(facade.selectPeriod).toHaveBeenCalledWith('last_week');
    expect(facade.setViewMode).toHaveBeenCalledWith('grouped');
  });
});
