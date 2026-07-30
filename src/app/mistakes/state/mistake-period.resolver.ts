import { DateRange, ReviewPeriod } from '../models/review-period.model';

function startOfDay(value: Date): Date {
  const result = new Date(value);
  result.setHours(0, 0, 0, 0);
  return result;
}

function endOfDay(value: Date): Date {
  const result = new Date(value);
  result.setHours(23, 59, 59, 999);
  return result;
}

function addDays(value: Date, days: number): Date {
  const result = new Date(value);
  result.setDate(result.getDate() + days);
  return result;
}

function mondayOfWeek(value: Date): Date {
  const date = startOfDay(value);
  const daysSinceMonday = (date.getDay() + 6) % 7;
  return addDays(date, -daysSinceMonday);
}

export function resolveReviewPeriod(
  period: ReviewPeriod = 'this_week',
  now = new Date(),
): DateRange {
  const thisMonday = mondayOfWeek(now);
  if (period === 'last_week') {
    const start = addDays(thisMonday, -7);
    return { start, end: endOfDay(addDays(start, 6)) };
  }
  if (period === 'last_30_days') {
    return { start: startOfDay(addDays(now, -29)), end: new Date(now) };
  }
  return { start: thisMonday, end: endOfDay(addDays(thisMonday, 6)) };
}
