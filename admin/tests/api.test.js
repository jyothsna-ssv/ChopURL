import { AxiosHeaders } from 'axios'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { getSession, signOut } = vi.hoisted(() => ({
  getSession: vi.fn(),
  signOut: vi.fn(),
}))

vi.mock('../src/supabase', () => ({
  supabase: {
    auth: { getSession, signOut },
  },
}))

describe('API authentication', () => {
  beforeEach(() => {
    getSession.mockReset()
    signOut.mockReset()
    signOut.mockResolvedValue({ error: null })
    vi.resetModules()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('attaches the current Supabase access token', async () => {
    getSession.mockResolvedValue({ data: { session: { access_token: 'fresh-token' } } })
    const { api } = await import('../src/api.ts')
    const interceptor = api.interceptors.request.handlers[0].fulfilled
    const headers = new AxiosHeaders()

    await interceptor({ headers })

    expect(headers.get('Authorization')).toBe('Bearer fresh-token')
  })

  it('leaves public requests anonymous when no session exists', async () => {
    getSession.mockResolvedValue({ data: { session: null } })
    const { api } = await import('../src/api.ts')
    const interceptor = api.interceptors.request.handlers[0].fulfilled
    const headers = new AxiosHeaders()

    await interceptor({ headers })

    expect(headers.has('Authorization')).toBe(false)
  })

  it('clears an expired session after an authenticated 401 response', async () => {
    const expired = vi.fn()
    window.addEventListener('chopurl:session-expired', expired)
    const { api } = await import('../src/api.ts')
    const interceptor = api.interceptors.response.handlers[0].rejected
    const error = { response: { status: 401 }, config: { headers: { Authorization: 'Bearer stale-token' } } }

    await expect(interceptor(error)).rejects.toBe(error)

    expect(signOut).toHaveBeenCalledOnce()
    expect(expired).toHaveBeenCalledOnce()
    window.removeEventListener('chopurl:session-expired', expired)
  })
})
