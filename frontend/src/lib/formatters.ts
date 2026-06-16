export function formatNumber(value: number | null | undefined, decimals: number = 0): string {
  if (value === null || value === undefined) return '—';
  const num = Number(value);
  if (!Number.isFinite(num)) return '—';
  return num.toFixed(decimals);
}

export function formatOptionalNumber(value: number | null | undefined, decimals: number = 0): string {
  return formatNumber(value, decimals);
}

export function formatPercentage(value: number | null | undefined, decimals: number = 1): string {
  if (value === null || value === undefined) return '—';
  const num = Number(value);
  if (!Number.isFinite(num)) return '—';
  return `${num.toFixed(decimals)}%`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '—';
  try {
    const date = new Date(value);
    if (isNaN(date.getTime())) return '—';
    // If it strictly contains 00:00:00 or is just a date string, format as Date only without timezone shift
    if (value.includes('00:00:00') || !value.includes('T') && !value.includes(':')) {
      const parts = value.split(' ')[0].split('-');
      if (parts.length === 3) {
        const d = new Date(Date.UTC(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2])));
        return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' });
      }
    }
    // Otherwise it has meaningful time
    return date.toLocaleString('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  } catch {
    return '—';
  }
}

export function formatFileSize(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined || bytes === 0) return '—';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}
