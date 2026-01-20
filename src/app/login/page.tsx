"use client"

import React, { useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/components/AuthProviderClient"
import { auth } from "@/lib/firebase"
import { getRedirectResult } from "firebase/auth"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LogIn, Loader2 } from "lucide-react"

export default function LoginPage() {
  const { signInWithGoogle, loading, firebaseUser, refreshProfile, profile } = useAuth()
  const [navigating, setNavigating] = useState(false)
  const router = useRouter()

  React.useEffect(() => {
    getRedirectResult(auth)
      .then((result) => {
        if (result) {
          console.log("Redirect result user:", result.user);
        } else {
          console.log("No redirect result found.");
        }
      })
      .catch((error) => {
        console.error("Redirect login error:", error);
      });
  }, []);

  // Handle post-redirect state or existing session
  React.useEffect(() => {
    if (firebaseUser && !navigating) {
      // Avoid double-redirects or conflicts
      setNavigating(true)

      // Check if new user
      const isNew = !!(firebaseUser.metadata && firebaseUser.metadata.creationTime === firebaseUser.metadata.lastSignInTime)
      if (isNew) {
        router.replace("/onboarding")
      } else {
        // Determine where to go (teacher/student)
        // Since 'gotoAfterAuth' is inside the component, we can replicate its logic or extract it.
        // For simplicity, let's look at the profile directly if loaded, or just default to student if taking too long.
        if (profile?.role) {
          router.replace(profile.role === "teacher" ? "/teacher" : "/student")
        } else {
          // If profile not loaded yet, we might want to wait, but AuthProvider loads it.
          // If we rely on AuthProvider's loading state:
          if (!loading) {
            // Profile loaded (or failed), default to onboarding or student
            // If profile is null but user exists -> Onboarding (AuthProvider sets onboardingRequired)
            router.replace("/onboarding")
          }
        }
      }
    }
  }, [firebaseUser, profile, loading, router, navigating]) // Added dependencies


  const gotoAfterAuth = async () => {
    // Fast path: if profile already in memory use it
    if (profile && profile.role) return router.replace(profile.role === "teacher" ? "/teacher" : "/student")

    // Otherwise try to refresh but don't wait long — race against a short timeout
    const refreshPromise = refreshProfile()
    const res = await Promise.race([
      refreshPromise,
      new Promise<null>((r) => setTimeout(() => r(null), 700)),
    ])

    if (res && (res as any).role) return router.replace((res as any).role === "teacher" ? "/teacher" : "/student")

    // Fallback: optimistic default. RoleGuard will correct if needed.
    return router.replace("/student")
  }

  const handleGoogle = async () => {
    try {
      setNavigating(true)
      await signInWithGoogle()
      // If this is the user's first sign-in, send them to onboarding immediately.
      const user = auth.currentUser
      const isNew = !!(user && user.metadata && user.metadata.creationTime === user.metadata.lastSignInTime)
      if (isNew) return router.replace("/onboarding")

      await gotoAfterAuth()
    } catch (err) {
      setNavigating(false)
      console.error(err)
    }
  }

  // Note: GitHub sign-in removed — only Google sign-in is supported.

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-xl">
        <Card>
          <CardHeader>
            <CardTitle>Sign in to CourseLLM</CardTitle>
            <CardDescription>Sign in with Google to continue — we'll only store the info needed for your profile.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col space-y-3">
              <Button onClick={handleGoogle} disabled={loading} size="lg">
                <LogIn className="mr-2" /> Sign in with Google
              </Button>
              {firebaseUser && (
                <div className="text-sm text-muted-foreground">Signed in as {firebaseUser.email}</div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
      {navigating && (
        <div className="fixed inset-0 z-50 bg-background/75 flex items-center justify-center">
          <div className="w-full max-w-sm px-6">
            <div className="rounded-lg bg-card p-6 shadow-lg text-center">
              <Loader2 className="mx-auto mb-4 animate-spin" />
              <div className="text-lg font-medium">Signing you in…</div>
              <div className="text-sm text-muted-foreground mt-1">We&apos;re taking you to your dashboard.</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
