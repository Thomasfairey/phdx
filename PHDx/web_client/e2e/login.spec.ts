import { test, expect } from "@playwright/test";

test.describe("Login Flow", () => {
  test("should show login page when not authenticated", async ({ page }) => {
    await page.goto("/");
    // Should redirect to login
    await expect(page).toHaveURL(/.*login/);
  });

  test("should show password input on login page", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByPlaceholder(/password/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /sign in|login/i })).toBeVisible();
  });

  test("should show error on invalid password", async ({ page }) => {
    await page.goto("/login");
    await page.getByPlaceholder(/password/i).fill("wrongpassword");
    await page.getByRole("button", { name: /sign in|login/i }).click();
    // Should show error message
    await expect(page.getByText(/invalid|incorrect|wrong/i)).toBeVisible({ timeout: 5000 });
  });

  test("should redirect to dashboard on valid password", async ({ page }) => {
    await page.goto("/login");
    await page.getByPlaceholder(/password/i).fill("phdx2026");
    await page.getByRole("button", { name: /sign in|login/i }).click();
    // Should redirect to main app
    await expect(page).not.toHaveURL(/.*login/, { timeout: 10000 });
  });

  test("should persist authentication after login", async ({ page }) => {
    // Login first
    await page.goto("/login");
    await page.getByPlaceholder(/password/i).fill("phdx2026");
    await page.getByRole("button", { name: /sign in|login/i }).click();
    await expect(page).not.toHaveURL(/.*login/, { timeout: 10000 });

    // Reload and check still authenticated
    await page.reload();
    await expect(page).not.toHaveURL(/.*login/, { timeout: 5000 });
  });
});
