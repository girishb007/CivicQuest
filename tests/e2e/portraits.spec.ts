import {test, expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.beforeEach(async ({page}) => {
  await page.addInitScript(() => {
    localStorage.setItem('cq_onboarding_complete', '1');
    sessionStorage.setItem('cq_splash_seen', '1');
  });
});

test('guest can skip, save, reload and clear a character portrait', async ({page}) => {
  await page.goto('/capture');
  await expect(page.getByLabel('Report photo')).toBeAttached();
  await page.goto('/profile');
  const google = page.getByRole('button', {name: 'Continue with Google'});
  await expect(google).toBeVisible();
  await expect(google).toBeEnabled();
  await google.click();
  await expect(page.getByText('Google sign-in needs OAuth credentials.', {exact: false})).toBeVisible();
  const picker = page.locator('.portrait-strip');
  await expect(picker.getByRole('button', {name: 'Initials'})).toHaveAttribute('aria-pressed', 'true');
  await picker.getByRole('button', {name: 'Observer', exact: true}).click();
  await expect(picker.getByRole('button', {name: 'Observer', exact: true})).toHaveAttribute('aria-pressed', 'true');
  await page.reload();
  await expect(picker.getByRole('button', {name: 'Observer', exact: true})).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('.my-card-top img')).toHaveAttribute('src', '/portraits/observer.svg');
  const results = await new AxeBuilder({page}).include('.identity-panel').analyze();
  expect(results.violations.filter(v => ['critical', 'serious'].includes(v.impact || ''))).toEqual([]);
  await picker.getByRole('button', {name: 'Initials'}).click();
  await expect(picker.getByRole('button', {name: 'Initials'})).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('.my-card-top img')).toHaveCount(0);
});

test('registered demo identity still sees the Google connection option', async ({page}) => {
  await page.goto('/profile');
  const reload=page.waitForEvent('load');
  await page.getByRole('button',{name:'Maya',exact:true}).click();
  await reload;
  await page.goto('/profile');
  await expect(page.getByRole('button',{name:'Connect Google',exact:true})).toBeVisible();
  await expect(page.getByText('Google OAuth is not configured on this local server.')).toBeVisible();
});
