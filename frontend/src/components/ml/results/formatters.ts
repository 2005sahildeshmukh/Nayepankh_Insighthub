export function formatPercentage(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) return '—';
  return `${(value * 100).toFixed(1)}%`;
}

export function formatMetric(value: number | null | undefined, decimals = 4): string {
  if (value === null || value === undefined || isNaN(value)) return '—';
  return value.toFixed(decimals);
}

export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || isNaN(seconds)) return '—';
  if (seconds < 1) return '< 1s';
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m ${s}s`;
}
