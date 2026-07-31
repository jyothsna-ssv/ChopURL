import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const auth = vi.hoisted(() => ({
  signInWithEmail: vi.fn(),
  signUpWithEmail: vi.fn(),
  sendPasswordResetEmail: vi.fn(),
  updatePassword: vi.fn(),
}))

vi.mock('../src/auth', () => ({
  useAuth: () => auth,
}))

import Login from '../src/views/Login.vue'

const createTestRouter = () => createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } },
    { path: '/links', component: { template: '<div>Links</div>' } },
    { path: '/login', component: Login },
  ],
})

const mountLogin = async (path = '/login') => {
  const router = createTestRouter()
  await router.push(path)
  await router.isReady()
  return { router, wrapper: mount(Login, { global: { plugins: [router] } }) }
}

describe('Login view', () => {
  beforeEach(() => {
    Object.values(auth).forEach((mock) => mock.mockReset())
    Object.values(auth).forEach((mock) => mock.mockResolvedValue(undefined))
  })

  it('shows an inline error and does not submit when signup passwords differ', async () => {
    const { wrapper } = await mountLogin()
    await wrapper.get('.toggle-btn').trigger('click')
    await wrapper.get('input[placeholder="Your username"]').setValue('Ada')
    await wrapper.get('input[type="email"]').setValue('ada@example.com')
    const passwords = wrapper.findAll('input[type="password"]')
    await passwords[0].setValue('password-one')
    await passwords[1].setValue('password-two')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.get('[role="alert"]').text()).toContain('Passwords do not match')
    expect(auth.signUpWithEmail).not.toHaveBeenCalled()
  })

  it('requires a username before submitting signup', async () => {
    const { wrapper } = await mountLogin()
    await wrapper.get('.toggle-btn').trigger('click')
    await wrapper.get('input[type="email"]').setValue('ada@example.com')
    const passwords = wrapper.findAll('input[type="password"]')
    await passwords[0].setValue('password')
    await passwords[1].setValue('password')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.get('[role="alert"]').text()).toContain('Username is required')
    expect(auth.signUpWithEmail).not.toHaveBeenCalled()
  })

  it('submits login and returns to the requested route', async () => {
    const { router, wrapper } = await mountLogin('/login?redirect=/links')
    await wrapper.get('input[type="email"]').setValue('ada@example.com')
    await wrapper.get('input[type="password"]').setValue('password')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(auth.signInWithEmail).toHaveBeenCalledWith('ada@example.com', 'password')
    expect(router.currentRoute.value.fullPath).toBe('/links')
  })

  it('shows forgot-password and password-reset success states', async () => {
    const { wrapper } = await mountLogin()
    await wrapper.get('.forgot-btn').trigger('click')
    await wrapper.get('input[type="email"]').setValue('ada@example.com')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(auth.sendPasswordResetEmail).toHaveBeenCalledWith(
      'ada@example.com',
      `${window.location.origin}/login?mode=reset`,
    )
    expect(wrapper.get('[role="status"]').text()).toContain('Password reset link sent')

    const reset = await mountLogin('/login?mode=reset')
    const passwords = reset.wrapper.findAll('input[type="password"]')
    await passwords[0].setValue('new-password')
    await passwords[1].setValue('new-password')
    await reset.wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(auth.updatePassword).toHaveBeenCalledWith('new-password')
    expect(reset.wrapper.get('[role="status"]').text()).toContain('Password updated')
  })
})
