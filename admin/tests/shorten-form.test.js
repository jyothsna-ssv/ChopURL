import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const api = vi.hoisted(() => ({ post: vi.fn() }))

vi.mock('../src/api', () => ({ api }))

import ShortenForm from '../src/components/ShortenForm.vue'

describe('ShortenForm', () => {
  beforeEach(() => {
    api.post.mockReset()
  })

  it('shortens a public URL without requiring an authenticated user', async () => {
    api.post.mockResolvedValue({ data: { short_url: 'https://chop.test/abc123' } })
    const wrapper = mount(ShortenForm)
    await wrapper.get('#url').setValue('https://example.com')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(api.post).toHaveBeenCalledWith('/shorten', {
      url: 'https://example.com',
      custom_code: undefined,
    })
    expect(wrapper.text()).toContain('https://chop.test/abc123')
  })

  it('displays a controlled API error inline', async () => {
    api.post.mockRejectedValue({ response: { data: { detail: 'Destination is not allowed' } } })
    const wrapper = mount(ShortenForm)
    await wrapper.get('#url').setValue('https://example.com')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(wrapper.get('[role="alert"]').text()).toContain('Destination is not allowed')
  })
})
