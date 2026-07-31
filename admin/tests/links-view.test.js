import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const api = vi.hoisted(() => ({ get: vi.fn(), delete: vi.fn() }))

vi.mock('../src/api', () => ({ api }))

import Links from '../src/views/Links.vue'

const stubs = {
  LinksTable: { props: ['links', 'loading', 'error'], template: '<div>{{ links.length }} {{ error }}</div>' },
  StatsModal: { template: '<div />' },
  RouterLink: { template: '<a><slot /></a>' },
}

describe('Links view', () => {
  beforeEach(() => {
    api.get.mockReset()
    api.delete.mockReset()
  })

  it('uses server pagination metadata and account-wide totals', async () => {
    api.get.mockResolvedValue({
      data: {
        items: [{ short_code: 'abc123' }],
        total: 17,
        skip: 0,
        limit: 8,
        total_clicks: 34,
        average_clicks: 2,
      },
    })
    const wrapper = mount(Links, { global: { stubs } })
    await flushPromises()

    expect(api.get).toHaveBeenCalledWith('/admin/links', { params: { skip: 0, limit: 8 } })
    expect(wrapper.text()).toContain('17')
    expect(wrapper.text()).toContain('34')
    expect(wrapper.text()).toContain('2')
    expect(wrapper.text()).toContain('1 of 3')
  })

  it('renders an API error instead of silently showing an empty dashboard', async () => {
    api.get.mockRejectedValue({ response: { data: { detail: 'Unable to load links' } } })
    const wrapper = mount(Links, { global: { stubs } })
    await flushPromises()

    expect(wrapper.text()).toContain('Unable to load links')
  })
})
