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

test('local admin can manage sourced operational ownership separately from elected context', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('cq_onboarding_complete', '1');
    sessionStorage.setItem('cq_splash_seen', '1');
  });
  await page.goto('/profile');
  const reload = page.waitForEvent('load');
  await page.getByRole('button', {name:'Admin', exact:true}).click();
  await reload;
  await page.goto('/admin');
  await page.getByRole('tab', {name:'Ownership', exact:true}).click();
  await expect(page.getByRole('heading', {name:'Operational ownership', exact:true})).toBeVisible();
  await expect(page.getByText('MLA and MP records remain separate electoral context.')).toBeVisible();
  await page.getByRole('button', {name:'Add ownership rule', exact:true}).click();
  await expect(page.getByRole('heading', {name:'Reviewed responsibility rule'})).toBeVisible({timeout:15000});
  await expect(page.getByRole('combobox', {name:'BMC ward', exact:true})).toBeVisible();
  await expect(page.getByRole('combobox', {name:'Issue family', exact:true})).toBeVisible();
  await expect(page.getByLabel('Official source URL', {exact:true})).toBeVisible();
  await page.getByRole('tab', {name:'Groups', exact:true}).click();
  await expect(page.getByRole('button', {name:'Add reviewed group', exact:true})).toBeVisible();
  await expect(page.getByRole('button', {name:'Edit', exact:true}).first()).toBeVisible();
  await expect(page.getByRole('button', {name:'Deactivate', exact:true}).first()).toBeVisible();
});

test('citizen flags a comment and moderator removes it from public discussion', async ({browser}) => {
  test.setTimeout(90000);
  async function open(role?:'Maya'|'Moderator') {
    const context=await browser.newContext({baseURL:'http://localhost:3000'});
    await context.addInitScript(()=>{localStorage.setItem('cq_onboarding_complete','1');sessionStorage.setItem('cq_splash_seen','1')});
    const page=await context.newPage();
    await page.goto('/profile');
    if(role){const loaded=page.waitForEvent('load');await page.getByRole('button',{name:role,exact:true}).click();await loaded;}
    return {context,page};
  }
  const author=await open('Maya');
  const report=(await author.page.request.get('/api/v1/feed/places').then(response=>response.json())).items[0];
  const text=`Factual test context ${Date.now()}`;
  await author.page.goto(`/reports/${report.id}`);
  await author.page.getByPlaceholder('Add factual context…').fill(text);
  await author.page.getByRole('button',{name:'Post comment'}).click();
  await expect(author.page.getByText(text,{exact:true})).toBeVisible();

  const visitor=await open();
  await visitor.page.goto(`/reports/${report.id}`);
  const comment=visitor.page.locator('.discussion article',{hasText:text});
  await comment.getByRole('button',{name:/Report comment by/}).click();
  await comment.getByLabel('Why should moderators review this comment?').fill('This comment needs a moderator review.');
  await comment.getByRole('button',{name:'Submit comment concern'}).click();

  const reviewer=await open('Moderator');
  await reviewer.page.goto('/admin');
  await reviewer.page.getByRole('tab',{name:'Reports'}).click();
  const caseCard=reviewer.page.locator('.review-card',{hasText:text});
  await expect(caseCard).toBeVisible();
  await caseCard.getByRole('button',{name:'Remove comment'}).click();
  await expect(caseCard).toHaveCount(0);
  await visitor.page.reload();
  await expect(visitor.page.getByText(text,{exact:true})).toHaveCount(0);
  await author.context.close();await visitor.context.close();await reviewer.context.close();
});
