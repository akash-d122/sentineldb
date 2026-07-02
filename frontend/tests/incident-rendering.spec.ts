import { test, expect } from '@playwright/test';

// To run this test with real data:
// 1. Ensure Docker Compose (db, redis, app, worker) is running.
// 2. Ensure Next.js is running (npm run dev).
// 3. Provide E2E_TEST_EMAIL and E2E_TEST_PASSWORD in your .env.

test.describe('Incident Rendering Pipeline', () => {
  test('User can log in and view a rendered RCA report', async ({ page }) => {
    test.skip(!process.env.E2E_TEST_EMAIL || !process.env.E2E_TEST_PASSWORD, 'Requires real test credentials to run against live DB/Auth');

    // 1. Log in
    await page.goto('/login');
    await page.fill('input[type="email"]', process.env.E2E_TEST_EMAIL!);
    await page.fill('input[type="password"]', process.env.E2E_TEST_PASSWORD!);
    await page.click('button[type="submit"]');

    // 2. Wait for redirect to dashboard
    await page.waitForURL('**/t/*/incidents');
    await expect(page.locator('h1:has-text("Live Incidents")')).toBeVisible();

    // 3. Find the first completed report and click it
    // Wait for the table to load
    await page.waitForSelector('table');
    await page.waitForTimeout(1000);
    
    // Look for a row with 'report ready' or similar status
    const reportLink = page.locator('tr:has-text("report_ready") >> a:has-text("View Report")').first();
    
    // If there is a report, navigate to it
    if (await reportLink.isVisible()) {
      await reportLink.click();
      
      // 4. Verify RCA rendering
      await expect(page.locator('h1:has-text("Incident RCA")')).toBeVisible();
      
      // Verify strength indicator
      await expect(page.locator('text=RCA Strength')).toBeVisible();
      
      // Verify root cause summary
      await expect(page.locator('h3:has-text("Root Cause Summary")')).toBeVisible();
      
      // Verify evidence bullets
      await expect(page.locator('h3:has-text("Supporting Evidence")')).toBeVisible();
      const evidenceItems = page.locator('.evidence-item');
      expect(await evidenceItems.count()).toBeGreaterThan(0);
      
      // Verify runbook integration
      await expect(page.locator('h3:has-text("Runbook & Next Steps")')).toBeVisible();
    } else {
      console.log('No ready reports found in live database to test rendering.');
    }
  });
});
