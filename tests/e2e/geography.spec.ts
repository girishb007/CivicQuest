import {test, expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.beforeEach(async ({page}) => {
  await page.addInitScript(() => {
    localStorage.setItem('cq_onboarding_complete', '1');
    sessionStorage.setItem('cq_splash_seen', '1');
  });
});

test('ward and constituency pages count their own geography and preserve Explore filters', async ({page}) => {
  await page.goto('/');
  await page.getByRole('button', {name:'List view'}).click();
  await page.getByLabel('Map issue type').selectOption('waste');
  await expect(page.locator('.map-list')).toContainText('This bin could use a fresh start');
  const explore=await page.request.get('/api/v1/explore?radius_m=60000&family=waste').then(r=>r.json());
  const target=explore.reports.find((report:any)=>report.title==='This bin could use a fresh start');
  const lookup=await page.request.get(`/api/v1/administrative-areas/lookup?lat=${target.lat}&lng=${target.lng}`).then(r=>r.json());
  const ward=lookup.areas.find((area:any)=>area.type==='ward');
  const coveringConstituency=lookup.areas.find((area:any)=>area.type==='assembly_constituency');
  expect(ward).toBeTruthy();
  await page.goto(`/areas/${ward.id}`);
  await expect(page.getByRole('heading',{name:ward.name,exact:true})).toBeVisible();
  const constituency=page.locator('section').filter({has:page.getByRole('heading',{name:'Constituency context'})}).getByRole('link',{name:new RegExp(coveringConstituency.name,'i')});
  await constituency.click();
  await expect(page.locator('.area-mobile-head .kicker')).toContainText('Assembly Constituency');
  await expect(page.getByRole('heading',{name:'Overlapping wards'})).toBeVisible();
  await expect(page.locator('.elected-row').filter({hasText:'MLA'}).first()).toBeVisible();
  const id=page.url().split('/').pop();
  const data=await page.request.get(`/api/v1/areas/${id}`).then(r=>r.json());
  expect(data.statistics.total_reports).toBeGreaterThan(0);
  expect(data.synthetic).toBe(false);
  expect(data.representatives.some((person:any)=>person.role==='MLA'&&person.source_name.includes('Maharashtra CEO'))).toBe(true);
  await expect(page.locator('.area-mobile-stats span').nth(2).locator('strong')).toHaveText(String(data.statistics.total_reports));
  expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)).toBe(false);
  const result=await new AxeBuilder({page}).include('main').analyze();
  expect(result.violations.filter(v=>['critical','serious'].includes(v.impact||''))).toEqual([]);
  await page.getByRole('link',{name:'Back to Explore'}).click();
  await expect(page.getByLabel('Map issue type')).toHaveValue('waste');
  await expect(page.locator('.map-list')).toBeVisible();
});

test('cluster zoom survives a map/list round trip', async ({page}) => {
  await page.goto('/');
  await page.locator('.map-cluster-count').first().click();
  await expect.poll(async()=>page.evaluate(()=>JSON.parse(sessionStorage.getItem('civicquest-explore-v2')||'{}').viewport?.zoom||0)).toBeGreaterThan(10.5);
  const before=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('civicquest-explore-v2')!).viewport);
  await page.getByRole('button',{name:'List view'}).click();
  await page.getByRole('button',{name:'Map view'}).click();
  await expect(page.locator('.maplibregl-canvas')).toBeVisible();
  const after=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('civicquest-explore-v2')!).viewport);
  expect(after.zoom).toBeCloseTo(before.zoom,1);
  expect(after.lng).toBeCloseTo(before.lng,3);
});

test('pincode search presents sourced post-office choices without assigning a ward', async ({page}) => {
  await page.goto('/');
  const search=page.getByLabel('Search Mumbai area');
  await search.fill('400001');
  await search.press('Enter');
  const choices=page.locator('.search-results button');
  await expect(choices).toHaveCount(6);
  await expect(choices.filter({hasText:'400001 · Mumbai GPO'})).toBeVisible();
  await choices.filter({hasText:'400001 · Mumbai GPO'}).click();
  await expect(search).toHaveValue('400001 · Mumbai GPO');
  await expect(page.locator('.postal-context')).toContainText('Resolved from this India Post office point.');
  await expect(page.locator('.postal-context')).toContainText(/Ward/);
  await expect(page.locator('.postal-context').getByRole('link',{name:'Department of Posts source'})).toBeVisible();
  const selected=await page.request.get('/api/v1/places/search?q=400001').then(r=>r.json());
  expect(selected.items.every((item:any)=>item.area_type==='postal_place'&&item.demo===false)).toBe(true);
});

test('map rendering distinguishes resolved and mixed clusters with textual status', async ({page}) => {
  // Rendering fixture only: real resolution moderation is tested separately.
  await page.goto('/profile');
  const original=await page.request.get('/api/v1/explore?radius_m=60000').then(r=>r.json());
  const records=original.reports.slice(0,2).map((r:any,i:number)=>({...r,lat:19.076+i*0.00001,lng:72.878,status:i?'resolved':'open'}));
  expect(records).toHaveLength(2);
  await page.route('**/api/v1/explore?**',async route=>{
    const status=new URL(route.request().url()).searchParams.get('status');
    const reports=status==='resolved'?records.map((r:any)=>({...r,status:'resolved'})):records;
    const resolved=reports.filter((r:any)=>r.status==='resolved').length;
    await route.fulfill({json:{reports,hotspots:[],summary:{total:2,active:2-resolved,resolved,limit:200,truncated:false}}});
  });
  await page.goto('/');
  await page.getByLabel('Map report status').selectOption('all');
  await expect(page.locator('.map-cluster-count[data-status="mixed"]')).toHaveAttribute('aria-label',/1 unresolved, 1 resolved/);
  await page.getByLabel('Map report status').selectOption('resolved');
  await expect(page.locator('.map-cluster-count[data-status="resolved"]')).toHaveAttribute('aria-label',/0 unresolved, 2 resolved/);
  await expect(page.locator('.map-top-counts')).toContainText('2resolved');
});
