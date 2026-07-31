import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import LinksTable from '../src/components/LinksTable.vue'

describe('LinksTable', () => {
  it('renders links and emits actions for a row', async () => {
    const wrapper = mount(LinksTable, {
      props: {
        links: [{
          short_code: 'abc123',
          original_url: 'https://example.com',
          short_url: 'http://localhost:8000/abc123',
          clicks: 3,
          created_at: '2026-01-01T00:00:00+00:00',
        }],
      },
    })

    expect(wrapper.text()).toContain('abc123')
    expect(wrapper.text()).toContain('https://example.com')

    await wrapper.get('.delete-btn').trigger('click')

    expect(wrapper.emitted('deleteLink')).toEqual([['abc123']])
  })
})
