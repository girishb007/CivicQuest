import { test, expect } from '@playwright/test';

test('local moderator can open the protected review workspace', async ({ browser }) => {
  const context = await browser.newContext({baseURL:'http://localhost:3000'});
  await context.addInitScript(() => {
    localStorage.setItem('cq_onboarding_complete', '1');
    sessionStorage.setItem('cq_splash_seen', '1');
  });
  const page = await context.newPage();
  await page.goto('/profile');
  await expect(page.getByRole('button', {name:'Moderator', exact:true})).toBeVisible();
  const login = page.waitForResponse(r => r.url().endsWith('/auth/demo/moderator') && r.request().method() === 'POST');
  const profileReload = page.waitForEvent('load');
  await page.getByRole('button', {name:'Moderator', exact:true}).click();
  expect((await login).ok()).toBeTruthy();
  await profileReload;
  await page.goto('/admin');
  await expect(page.locator('main h1')).toBeVisible();
  await expect(page.locator('main').getByRole('alert')).toHaveCount(0);
  await context.close();
});
