/**
 * Search Service
 *
 * Provides full-text search across all story entities:
 * characters, locations, scenes, fragments, research, etc.
 */

import { apiClient } from '@/lib/api-client';

export interface SearchResult {
  id: string;
  name: string;
  type: 'character' | 'location' | 'scene' | 'fragment' | 'research' | 'decision';
  preview: string;
  score: number;
  filePath?: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  totalCount: number;
  executionTimeMs: number;
}

/**
 * Search across all entities
 */
export async function searchAll(
  query: string,
  options?: {
    types?: string[];
    limit?: number;
    offset?: number;
  }
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    q: query,
    ...(options?.types && { types: options.types.join(',') }),
    ...(options?.limit && { limit: options.limit.toString() }),
    ...(options?.offset && { offset: options.offset.toString() }),
  });

  const response = await apiClient.get(`/api/v1/search?${params}`);
  return response.json();
}

/**
 * Search characters
 */
export async function searchCharacters(query: string): Promise<SearchResult[]> {
  const response = await searchAll(query, { types: ['character'] });
  return response.results;
}

/**
 * Search locations
 */
export async function searchLocations(query: string): Promise<SearchResult[]> {
  const response = await searchAll(query, { types: ['location'] });
  return response.results;
}

/**
 * Search scenes
 */
export async function searchScenes(query: string): Promise<SearchResult[]> {
  const response = await searchAll(query, { types: ['scene', 'fragment'] });
  return response.results;
}

/**
 * Search research/knowledge
 */
export async function searchResearch(query: string): Promise<SearchResult[]> {
  const response = await searchAll(query, { types: ['research'] });
  return response.results;
}

/**
 * Get search suggestions (autocomplete)
 */
export async function getSearchSuggestions(query: string): Promise<string[]> {
  if (query.length < 2) return [];

  try {
    const response = await apiClient.get(
      `/api/v1/search/suggestions?q=${encodeURIComponent(query)}&limit=10`
    );
    const data = await response.json();
    return data.suggestions || [];
  } catch {
    return [];
  }
}

/**
 * Get search history from localStorage
 */
export function getSearchHistory(): string[] {
  if (typeof window === 'undefined') return [];

  const history = localStorage.getItem('searchHistory');
  if (!history) return [];

  try {
    return JSON.parse(history).slice(0, 10);
  } catch {
    return [];
  }
}

/**
 * Save search to history
 */
export function saveSearchToHistory(query: string) {
  if (typeof window === 'undefined' || !query.trim()) return;

  const history = getSearchHistory();
  const updated = [query, ...history.filter(q => q !== query)].slice(0, 10);
  localStorage.setItem('searchHistory', JSON.stringify(updated));
}

/**
 * Clear search history
 */
export function clearSearchHistory() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('searchHistory');
  }
}
