import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { DataPortabilityRepository } from '../../data/data-portability.repository';
import { ExportDataComponent } from './export.component';

describe('ExportDataComponent', () => {
  it('confirms a complete current export and allows another immediately', async () => {
    const repository = jasmine.createSpyObj<DataPortabilityRepository>(
      'DataPortabilityRepository', ['exportAll'],
    );
    repository.exportAll.and.resolveTo({
      status: 'success',
      producedAt: '2026-07-29T10:00:00Z',
      categoryCount: 6,
      filename: 'ielts-learning-export.json',
    });
    await TestBed.configureTestingModule({
      imports: [ExportDataComponent],
      providers: [
        provideRouter([]),
        { provide: DataPortabilityRepository, useValue: repository },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(ExportDataComponent);
    await fixture.componentInstance.exportData();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="export-success"]')
      .textContent).toContain('6 complete categories');
    await fixture.componentInstance.exportData();
    expect(repository.exportAll).toHaveBeenCalledTimes(2);
  });

  it('shows a distinct retryable failure', async () => {
    const repository = jasmine.createSpyObj<DataPortabilityRepository>(
      'DataPortabilityRepository', ['exportAll'],
    );
    repository.exportAll.and.resolveTo({
      status: 'error', message: 'Could not export', retryable: true,
    });
    await TestBed.configureTestingModule({
      imports: [ExportDataComponent],
      providers: [
        provideRouter([]),
        { provide: DataPortabilityRepository, useValue: repository },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(ExportDataComponent);
    await fixture.componentInstance.exportData();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="export-error"]'))
      .not.toBeNull();
  });
});
