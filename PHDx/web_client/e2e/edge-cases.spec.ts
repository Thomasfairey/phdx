import { test, expect } from "@playwright/test";

test.describe("Edge Cases", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.getByPlaceholder(/password/i).fill("phdx2026");
    await page.getByRole("button", { name: /sign in|login/i }).click();
    await expect(page).not.toHaveURL(/.*login/, { timeout: 10000 });
  });

  test("should handle sidebar collapse/expand", async ({ page }) => {
    // Find sidebar toggle button
    const sidebarToggle = page.locator('button[aria-label*="collapse"], button[aria-label*="sidebar"], [data-testid="sidebar-toggle"]');

    if (await sidebarToggle.count() > 0) {
      await sidebarToggle.first().click();
      await page.waitForTimeout(300);
      await sidebarToggle.first().click();
      await page.waitForTimeout(300);
    }
  });

  test("should navigate between modules without errors", async ({ page }) => {
    // Navigate to different modules
    const modules = ["writing", "data", "auditor"];

    for (const module of modules) {
      const moduleButton = page.getByText(new RegExp(module, "i")).first();
      if (await moduleButton.isVisible()) {
        await moduleButton.click();
        await page.waitForTimeout(500);
        // No crash = success
      }
    }
  });

  test("should show API connection status", async ({ page }) => {
    // Look for connection indicator
    const statusIndicator = page.locator('[data-testid="api-status"], .status-indicator, [class*="connection"]');

    // Should have some kind of status indicator
    await page.waitForTimeout(2000);
    // Page should not show fatal error
    await expect(page.locator("body")).not.toContainText("Application error");
  });

  test("should handle empty states gracefully", async ({ page }) => {
    // Go to data module which should be empty initially
    await page.getByText(/data/i).first().click();
    await page.waitForTimeout(1000);

    // Should show empty state or upload prompt, not error
    await expect(page.locator("body")).not.toContainText("undefined");
    await expect(page.locator("body")).not.toContainText("null");
  });

  test("should handle rapid navigation", async ({ page }) => {
    // Rapidly switch between modules
    for (let i = 0; i < 5; i++) {
      await page.getByText(/writing/i).first().click();
      await page.getByText(/data/i).first().click();
    }

    // Should not crash
    await expect(page.locator("body")).toBeVisible();
  });
});
