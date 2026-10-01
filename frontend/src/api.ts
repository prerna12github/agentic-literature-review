import type { ReviewOut, PendingResponse, DecisionPayload } from './types';

export const API_BASE_URL =
  (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const data = await res.json();
      if (data && data.detail) {
        errorDetail = data.detail;
      }
    } catch {
      try {
        const text = await res.text();
        if (text) errorDetail = text;
      } catch {
        // use default errorDetail
      }
    }
    const error = new Error(errorDetail) as Error & { status?: number };
    error.status = res.status;
    throw error;
  }
  return res.json() as Promise<T>;
}

export async function createReview(query: string): Promise<ReviewOut> {
  const res = await fetch(`${API_BASE_URL}/reviews`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({ query }),
  });
  return handleResponse<ReviewOut>(res);
}

export async function listReviews(): Promise<ReviewOut[]> {
  const res = await fetch(`${API_BASE_URL}/reviews`, {
    headers: {
      Accept: 'application/json',
    },
  });
  return handleResponse<ReviewOut[]>(res);
}

export async function getReview(id: string): Promise<ReviewOut> {
  const res = await fetch(`${API_BASE_URL}/reviews/${encodeURIComponent(id)}`, {
    headers: {
      Accept: 'application/json',
    },
  });
  return handleResponse<ReviewOut>(res);
}

export async function getPending(id: string): Promise<PendingResponse> {
  const res = await fetch(
    `${API_BASE_URL}/reviews/${encodeURIComponent(id)}/pending`,
    {
      headers: {
        Accept: 'application/json',
      },
    }
  );
  return handleResponse<PendingResponse>(res);
}

export async function submitDecision(
  id: string,
  payload: DecisionPayload
): Promise<ReviewOut> {
  const res = await fetch(
    `${API_BASE_URL}/reviews/${encodeURIComponent(id)}/decision`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
    }
  );
  return handleResponse<ReviewOut>(res);
}

export async function retryReview(id: string): Promise<ReviewOut> {
  const res = await fetch(
    `${API_BASE_URL}/reviews/${encodeURIComponent(id)}/retry`,
    {
      method: 'POST',
      headers: {
        Accept: 'application/json',
      },
    }
  );
  return handleResponse<ReviewOut>(res);
}

export async function getReport(id: string): Promise<string> {
  const res = await fetch(
    `${API_BASE_URL}/reviews/${encodeURIComponent(id)}/report`
  );
  if (!res.ok) {
    let errorDetail = `Failed to get report (${res.status})`;
    try {
      const data = await res.json();
      if (data?.detail) errorDetail = data.detail;
    } catch {
      // ignore
    }
    const error = new Error(errorDetail) as Error & { status?: number };
    error.status = res.status;
    throw error;
  }
  return res.text();
}
