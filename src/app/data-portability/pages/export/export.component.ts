import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { DataPortabilityRepository } from '../../data/data-portability.repository';
import { ExportResult } from '../../models/export-result.model';

@Component({
  selector: 'app-export-data',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './export.component.html',
  styleUrl: './export.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ExportDataComponent {
  private readonly repository = inject(DataPortabilityRepository);
  readonly state = signal<'idle' | 'exporting' | 'done'>('idle');
  readonly result = signal<ExportResult | null>(null);

  async exportData(): Promise<void> {
    this.state.set('exporting');
    this.result.set(null);
    this.result.set(await this.repository.exportAll());
    this.state.set('done');
  }
}
