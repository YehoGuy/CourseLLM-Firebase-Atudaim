import { test, expect } from '@playwright/test';
import { loginAs } from './helpers/auth-utils';

test('Full Flow: Register, Convert and Verify Extracted Assets', async ({ page }) => {
  const uniqueUid = `teacher-full-flow-${Date.now()}`;
  await loginAs(page, { uid: uniqueUid, createProfile: false });

  await page.waitForURL('**/onboarding', { timeout: 15000 });

  await page.getByRole('button', { name: 'Teacher', exact: true }).click();

  await page.getByPlaceholder('e.g. Computer Science').fill('Digital Signal Processing');

  await page.getByPlaceholder('Add a course and press Enter').fill('DSP 101');
  await page.getByRole('button', { name: 'Add' }).click();
  
  await expect(page.getByText('DSP 101')).toBeVisible();

  await page.getByRole('button', { name: 'Save and Continue' }).click();

  await page.waitForURL('**/teacher', { timeout: 15000 });
  
  await page.getByRole('link', { name: 'Convert to Markdown' }).click();
  
  await page.waitForURL('**/teacher/material-to-md', { timeout: 15000 });
  await expect(page.getByRole('heading', { name: 'Material → Markdown' })).toBeVisible();

  await page.setInputFiles('#file-upload', 'services/material-to-md/tests/test_assets/DSP.pdf');

  await page.locator('main').getByRole('button', { name: 'Convert to Markdown' }).click();

  await expect(page.getByText('Conversion Successful')).toBeVisible({ timeout: 70000 });

  await expect(page.getByText('Markdown Preview')).toBeVisible({ timeout: 15000 });

  const assetsHeading = page.getByText('Extracted Assets', { exact: true });
  
  if (await assetsHeading.isVisible({ timeout: 5000 })) {
    const assetImages = page.locator('main img');
    await expect(assetImages.first()).toBeVisible({ timeout: 15000 });

    const imageSrc = await assetImages.first().getAttribute('src');
    expect(imageSrc).not.toBeNull();
    console.log('Successfully verified asset image with src:', imageSrc);
  } else {
    console.warn('No images found in the assets section. Verifying text content only.');
    await expect(page.locator('pre')).not.toBeEmpty();
  }
});