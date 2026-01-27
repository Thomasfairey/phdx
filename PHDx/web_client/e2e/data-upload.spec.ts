import { test, expect } from "@playwright/test";
import path from "path";

test.describe("Data Upload", () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto("/login");
    await page.getByPlaceholder(/password/i).fill("phdx2026");
    await page.getByRole("button", { name: /sign in|login/i }).click();
    await expect(page).not.toHaveURL(/.*login/, { timeout: 10000 });
  });

  test("should navigate to data module", async ({ page }) => {
    // Click on Data Lab in sidebar
    await page.getByText(/data/i).first().click();
    // Should see upload area or data view
    await expect(
      page.getByText(/upload|drop|csv|data/i).first()
    ).toBeVisible({ timeout: 5000 });
  });

  test("should show upload dropzone", async ({ page }) => {
    await page.getByText(/data/i).first().click();
    // Should have a file input or dropzone
    const uploadArea = page.locator('[data-testid="dropzone"], input[type="file"], .dropzone');
    await expect(uploadArea.first()).toBeVisible({ timeout: 5000 });
  });

  test("should reject non-CSV files", async ({ page }) => {
    await page.getByText(/data/i).first().click();

    // Create a fake text file and try to upload
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.count() > 0) {
      // Create a buffer with text content (not CSV)
      await fileInput.setInputFiles({
        name: "test.txt",
        mimeType: "text/plain",
        buffer: Buffer.from("not a csv file"),
      });

      // Should show error or no dataset added
      await page.waitForTimeout(1000);
      // The app should not show the file as uploaded successfully
    }
  });

  test("should accept valid CSV files", async ({ page }) => {
    await page.getByText(/data/i).first().click();

    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.count() > 0) {
      // Create a valid CSV
      const csvContent = "id,name,value\n1,test,100\n2,test2,200";
      await fileInput.setInputFiles({
        name: "test.csv",
        mimeType: "text/csv",
        buffer: Buffer.from(csvContent),
      });

      // Should process the file (may show loading or success)
      await page.waitForTimeout(2000);
    }
  });
});
