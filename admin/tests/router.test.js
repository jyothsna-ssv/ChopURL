import { beforeEach, describe, expect, it, vi } from 'vitest'

const { getSession, onAuthStateChange } = vi.hoisted(() => ({
  getSession: vi.fn().mockResolvedValue({ data: { session: null }, error: null }),
  onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
}))

vi.mock('../src/supabase', () => ({
  supabase: { auth: { getSession, onAuthStateChange } },
}))

import router from '../src/router'

describe('route guards', () => {
  beforeEach(() => {
    getSession.mockReset()
    onAuthStateChange.mockReset()
    onAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } })
  })

  it('redirects unauthenticated users from the dashboard to login', async () => {
    getSession.mockResolvedValue({ data: { session: null }, error: null })

    await router.push('/links')

    expect(router.currentRoute.value.name).toBe('Login')
    expect(router.currentRoute.value.query.redirect).toBe('/links')
  })
})
