import { Page, request, expect } from '@playwright/test';

/**
 * פונקציה להתחברות משתמש בדיקה המבוססת על ה-API הקיים בפרויקט
 */
export async function loginAs(
  page: Page, 
  options: { uid: string; role?: 'student' | 'teacher'; createProfile?: boolean }
) {
  const { uid, role, createProfile = true } = options;
  const baseUrl = 'http://localhost:9002'; // לפי ה-baseURL ב-playwright.config.ts

  // בניית הפרמטרים לפנייה ל-API
  const queryParams = new URLSearchParams({
    uid,
    createProfile: String(createProfile),
  });
  if (role) queryParams.append('role', role);

  // 1. קבלת טוקן מה-Backend
  const apiContext = await request.newContext();
  const res = await apiContext.get(`${baseUrl}/api/test-token?${queryParams.toString()}`);

  if (!res.ok()) {
  console.error('Auth API Failure:', res.status(), await res.text());
}
  expect(res.ok()).toBeTruthy();
  const { token } = await res.json();

  // 2. ביצוע ה-Sign-in דרך דף הבדיקה הייעודי
  await page.goto(`${baseUrl}/test/signin?token=${encodeURIComponent(token)}`);
}