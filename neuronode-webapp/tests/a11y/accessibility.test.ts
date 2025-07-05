import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test.describe('Accessibility Tests', () => {
  test('Homepage should be accessible', async ({ page }) => {
    await page.goto('/')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('body')
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })
  
  test('Chat page should be accessible', async ({ page }) => {
    await page.goto('/chat')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('body')
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('Graph page should be accessible', async ({ page }) => {
    await page.goto('/graph')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('body')
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('Upload page should be accessible', async ({ page }) => {
    await page.goto('/upload')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('body')
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('Settings page should be accessible', async ({ page }) => {
    await page.goto('/settings')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('body')
      .analyze()
    
    expect(accessibilityScanResults.violations).toEqual([])
  })
  
  test('Keyboard navigation should work', async ({ page }) => {
    await page.goto('/')
    
    // Test Tab navigation
    await page.keyboard.press('Tab')
    let focusedElement = await page.locator(':focus')
    await expect(focusedElement).toBeVisible()
    
    // Test Skip Link
    await page.keyboard.press('Tab')
    await page.keyboard.press('Enter')
    const mainContent = page.locator('#main-content')
    await expect(mainContent).toBeFocused()
  })

  test('Navigation should be keyboard accessible', async ({ page }) => {
    await page.goto('/')
    
    // Focus on the first navigation item
    await page.keyboard.press('Tab') // Skip link
    await page.keyboard.press('Tab') // Mobile menu button (if visible)
    await page.keyboard.press('Tab') // First nav item or notification button
    
    // Check if we can navigate with arrow keys in mobile menu
    await page.setViewportSize({ width: 500, height: 800 }) // Mobile viewport
    await page.goto('/')
    
    // Open mobile menu
    const menuButton = page.getByRole('button', { name: 'Hauptnavigation öffnen' })
    await menuButton.click()
    
    // Navigate menu items with keyboard
    await page.keyboard.press('ArrowDown')
    await page.keyboard.press('Enter')
    
    // Verify navigation worked
    await expect(page).toHaveURL('/')
  })

  test('User menu should be keyboard accessible', async ({ page }) => {
    await page.goto('/')
    
    // Focus on user menu button
    const userMenuButton = page.getByRole('button', { name: 'Benutzermenü öffnen' })
    await userMenuButton.focus()
    await userMenuButton.press('Enter')
    
    // Check if menu is open
    const userMenu = page.locator('#user-menu')
    await expect(userMenu).toBeVisible()
    
    // Navigate with arrow keys
    await page.keyboard.press('ArrowDown')
    await page.keyboard.press('ArrowDown')
    
    // Close with Escape
    await page.keyboard.press('Escape')
    await expect(userMenu).not.toBeVisible()
  })

  test('Color contrast should meet WCAG standards', async ({ page }) => {
    await page.goto('/')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze()
    
    // Check specifically for color contrast violations
    const colorContrastViolations = accessibilityScanResults.violations.filter(
      violation => violation.id === 'color-contrast'
    )
    
    expect(colorContrastViolations).toEqual([])
  })

  test('All images should have alt text', async ({ page }) => {
    await page.goto('/')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a'])
      .analyze()
    
    // Check for image alt text violations
    const imageAltViolations = accessibilityScanResults.violations.filter(
      violation => violation.id === 'image-alt'
    )
    
    expect(imageAltViolations).toEqual([])
  })

  test('Page should have proper heading structure', async ({ page }) => {
    await page.goto('/')
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a'])
      .analyze()
    
    // Check for heading violations
    const headingViolations = accessibilityScanResults.violations.filter(
      violation => violation.id.includes('heading')
    )
    
    expect(headingViolations).toEqual([])
  })
}) 