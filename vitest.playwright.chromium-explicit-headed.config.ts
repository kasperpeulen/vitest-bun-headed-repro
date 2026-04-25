import { playwright } from '@vitest/browser-playwright'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    browser: {
      enabled: true,
      headless: false,
      screenshotFailures: false,
      provider: playwright(),
      instances: [{ browser: 'chromium' }],
    },
  },
})
