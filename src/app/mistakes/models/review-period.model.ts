export type ReviewPeriod = 'this_week' | 'last_week' | 'last_30_days';

export const REVIEW_PERIOD_OPTIONS: ReadonlyArray<{
  value: ReviewPeriod;
  label: string;
}> = [
  { value: 'this_week', label: 'This week' },
  { value: 'last_week', label: 'Last week' },
  { value: 'last_30_days', label: 'Last 30 days' },
];

export interface DateRange {
  start: Date;
  end: Date;
}
