const API_BASE = '/backend-api/api/v1';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function fetchClient<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = endpoint.startsWith('/') ? `/backend-api${endpoint}` : `${API_BASE}/${endpoint}`;
  
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const fetchOptions: RequestInit = {
    cache: 'no-store',
    ...options,
    headers,
  };

  const res = await fetch(url, fetchOptions);

  if (!res.ok) {
    let errorMessage = 'An error occurred';
    try {
      const data = await res.json();
      errorMessage = data.detail || errorMessage;
    } catch {
      // Ignore
    }
    throw new Error(errorMessage);
  }

  if (res.status === 204) {
    return undefined as unknown as T;
  }

  return res.json();
}
