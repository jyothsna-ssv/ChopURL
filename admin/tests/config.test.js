import { afterEach, describe, expect, it, vi } from 'vitest'

afterEach(() => {
  vi.unstubAllEnvs()
})

describe('API configuration', () => {
  it('uses the deployment API URL when provided', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.com/api/v1')
    vi.resetModules()

    const { apiBaseUrl } = await import('../src/config.js')

    expect(apiBaseUrl).toBe('https://api.example.com/api/v1')
  })

  it('uses a same-origin API path for production builds without an API URL', async () => {
    vi.stubEnv('VITE_API_BASE_URL', '')
    vi.stubEnv('DEV', false)
    vi.resetModules()

    const { apiBaseUrl } = await import('../src/config.js')

    expect(apiBaseUrl).toBe('/api/v1')
  })
})
