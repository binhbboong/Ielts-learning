import { Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import {
  ExportDocument,
  ExportResult,
} from '../models/export-result.model';

@Injectable({ providedIn: 'root' })
export class DataPortabilityRepository {
  constructor(private readonly api: ApiClient) {}

  async exportAll(): Promise<ExportResult> {
    try {
      const document = await firstValueFrom(
        this.api.post<ExportDocument>('/api/data-portability/export', {}),
      );
      const timestamp = document.produced_at.replace(/[:.]/g, '-');
      const filename = `ielts-learning-export-${timestamp}.json`;
      const blob = new Blob([JSON.stringify(document, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const link = window.document.createElement('a');
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
      return {
        status: 'success',
        producedAt: document.produced_at,
        categoryCount: document.category_count,
        filename,
      };
    } catch {
      return {
        status: 'error',
        message: 'The complete export could not be produced.',
        retryable: true,
      };
    }
  }
}
