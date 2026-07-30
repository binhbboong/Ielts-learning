export interface ExportDocument {
  export_format_version: number;
  export_id: string;
  produced_at: string;
  complete: boolean;
  category_count: number;
  categories: string[];
  data: Record<string, unknown>;
}

export type ExportResult =
  | {
      status: 'success';
      producedAt: string;
      categoryCount: number;
      filename: string;
    }
  | {
      status: 'error';
      message: string;
      retryable: boolean;
    };
