import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.beforeEach(async ({page}) => {
  await page.addInitScript(() => {
    localStorage.setItem('cq_onboarding_complete', '1');
    sessionStorage.setItem('cq_splash_seen', '1');
  });
});

test('guest can use all five navigation areas', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Explore your area' })).toBeVisible();
  for (const path of ['/feed', '/capture', '/quests', '/profile']) {
    await page.goto(path);
    await expect(page.locator('main h1')).toBeVisible({timeout: 15000});
    await expect(page.locator('main').getByRole('alert')).toHaveCount(0);
  }
  expect(errors).toEqual([]);
});

test('capture form has no serious accessibility violations', async ({ page }) => {
  await page.goto('/capture');
  await expect(page.locator('input[type=file]')).toBeAttached();
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations.filter(v => ['critical', 'serious'].includes(v.impact || ''))).toEqual([]);
});

test('guest submits a photo and sees pending XP', async ({ page }) => {
  await page.goto('/capture');
  await page.getByLabel('Report photo').setInputFiles('data/samples/garbage_dump.jpg');
  await page.getByLabel('Short title').fill('Synthetic browser capture test');
  await page.getByLabel('Latitude', {exact: true}).fill('19.11');
  await page.getByLabel('Longitude', {exact: true}).fill('72.89');
  await page.getByRole('button', {name: 'Submit Place report'}).click();
  await expect(page.getByRole('heading', {name: 'Your civic quest has started.'})).toBeVisible();
  await expect(page.getByText('25 XP is pending')).toBeVisible();
  await page.getByRole('link', {name: 'Track this report'}).click();
  await expect(page.getByRole('heading', {name: 'Synthetic browser capture test'})).toBeVisible();
  await expect(page.getByText('25 XP pending')).toBeVisible();
});

test('guest can persist inbox preferences while browser push stays linked-only', async ({page}) => {
  await page.goto('/notifications');
  await expect(page.getByRole('heading', {name: 'Your city updates'})).toBeVisible();
  const reportUpdates = page.getByRole('checkbox').nth(0);
  await expect(page.getByRole('checkbox').nth(2)).toBeDisabled();
  await reportUpdates.uncheck();
  await page.getByRole('button', {name: 'Save choices'}).click();
  await page.reload();
  await expect(reportUpdates).not.toBeChecked();
});
