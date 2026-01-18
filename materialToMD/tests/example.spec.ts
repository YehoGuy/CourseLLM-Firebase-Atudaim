// example.spec.ts
import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Material Conversion Flow', () => {
  
  test('User can log in and convert a file to Markdown', async ({ page }) => {
    await page.goto('http://localhost:3000/login');

    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');
    
    await page.click('button:has-text("Sign In")', { force: true });

    await expect(page.locator('h1')).toContainText('Material to Markdown', { timeout: 60000 });

    const filePath = path.join(__dirname, 'test_assets', 'PR Checklist.pdf');

    await page.setInputFiles('input[type="file"]', filePath);


    await page.click('button:has-text("Convert")', { force: true });

    const resultsHeader = page.locator('h3', { hasText: 'Raw Markdown' });
    await expect(resultsHeader).toBeVisible({ timeout: 20000 });

    const textArea = page.locator('textarea');
    const content = await textArea.inputValue();
    expect(content.length).toBeGreaterThan(0);

    await expect(page.locator('h3', { hasText: 'Preview' })).toBeVisible();
  });
});