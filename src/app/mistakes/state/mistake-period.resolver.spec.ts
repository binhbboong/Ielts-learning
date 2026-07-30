import { resolveReviewPeriod } from './mistake-period.resolver';

describe('resolveReviewPeriod', () => {
  const wednesday = new Date('2026-07-29T12:00:00');

  it('resolves this week to Monday through Sunday and uses it by default', () => {
    const explicit = resolveReviewPeriod('this_week', wednesday);
    const defaulted = resolveReviewPeriod(undefined, wednesday);

    expect(explicit.start.getDay()).toBe(1);
    expect(explicit.end.getDay()).toBe(0);
    expect(explicit.start.getDate()).toBe(27);
    expect(explicit.end.getDate()).toBe(2);
    expect(defaulted).toEqual(explicit);
  });

  it('resolves last week and last 30 days', () => {
    const lastWeek = resolveReviewPeriod('last_week', wednesday);
    const last30 = resolveReviewPeriod('last_30_days', wednesday);

    expect(lastWeek.start.getDate()).toBe(20);
    expect(lastWeek.end.getDate()).toBe(26);
    expect(last30.end.getTime()).toBe(wednesday.getTime());
    expect(last30.start.getDate()).toBe(30);
  });
});
