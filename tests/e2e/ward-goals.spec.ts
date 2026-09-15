import {test,expect} from '@playwright/test';

test.beforeEach(async ({page}) => {
  await page.addInitScript(() => {
    localStorage.setItem('cq_onboarding_complete', '1');
    sessionStorage.setItem('cq_splash_seen', '1');
  });
});

test('admin publishes and cancels a ward goal while citizen progress stays separate',async({page,browser})=>{
  await page.goto('/profile');
  const reload=page.waitForEvent('load');
  await page.getByRole('button',{name:'Admin',exact:true}).click();await reload;
  await page.goto('/admin');
  await page.getByRole('tab',{name:'Ward Goals',exact:true}).click();
  await page.getByRole('button',{name:'Create ward goal',exact:true}).click();
  const title='Mumbai ward goal '+Date.now();
  await page.getByLabel('Goal title',{exact:true}).fill(title);
  await page.getByLabel('Administrative ward',{exact:true}).selectOption({index:1});
  await page.getByLabel('Target verified outcomes').fill('4');
  await page.getByLabel('Start date (Mumbai)').fill('2026-01-01');
  await page.getByLabel('End date, exclusive (Mumbai)').fill('2027-01-01');
  await page.getByLabel('Goal visibility').selectOption('published');
  await page.getByRole('button',{name:'Save ward goal'}).click();
  await expect(page.getByRole('heading',{name:title,exact:true})).toBeVisible();
  const citizen=await browser.newContext();
  await citizen.addInitScript(() => {
    localStorage.setItem('cq_onboarding_complete', '1');
    sessionStorage.setItem('cq_splash_seen', '1');
  });
  const visitor=await citizen.newPage();
  await visitor.goto('http://localhost:3000/quests');
  await expect(visitor.getByRole('heading',{name:title,exact:true})).toBeVisible();
  const me=await visitor.request.get('http://localhost:3000/api/v1/me').then(r=>r.json());
  expect(me.xp).toBe(0);
  await page.getByRole('button',{name:'Edit '+title,exact:true}).click();
  await page.getByLabel('Goal visibility').selectOption('cancelled');
  await page.getByRole('button',{name:'Save ward goal'}).click();
  await expect(page.locator('.goal-editor')).toHaveCount(0);
  await visitor.reload();
  await expect(visitor.getByRole('heading',{name:title,exact:true})).toHaveCount(0);
  await citizen.close();
});
