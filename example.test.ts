import { expect, test } from 'vitest'

test('runs in chromium browser mode', () => {
  expect(globalThis.window.location.protocol).toMatch(/^https?:$/)
  expect(document.createElement('button').tagName).toBe('BUTTON')
})
