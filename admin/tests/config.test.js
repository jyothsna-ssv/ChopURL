import { describe, expect, it, vi } from 'vitest'

describe('API configuration', () => {
  it('uses the deployment API URL when provided', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.com/api/v1')
    vi.resetModules()

    const { apiBaseUrl } = await import('../src/config.js')

    expect(apiBaseUrl).toBe('https://api.example.com/api/v1')
  })
})
