import { chromium } from 'playwright'

const browser = await chromium.launch({ headless: false, timeout: 10_000 })
const page = await browser.newPage()
await page.setContent('<h1>playwright smoke</h1>')
console.log(await page.textContent('h1'))
await browser.close()
