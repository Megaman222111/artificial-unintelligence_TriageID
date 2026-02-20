const API_BASE_URL =
  process.env.NEXT_PUBLIC_DJANGO_API_BASE_URL ||
  process.env.DJANGO_API_BASE_URL ||
  "http://127.0.0.1:8000"

const TOKEN_KEY = "medlink_access_token"

export interface AuthUser {
  id: number
  email: string
  firstName: string
  lastName: string
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem(TOKEN_KEY)
}

export function setAccessToken(token: string): void {
  if (typeof window === "undefined") return
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearAccessToken(): void {
  if (typeof window === "undefined") return
  localStorage.removeItem(TOKEN_KEY)
}

export async function login(email: string, password: string): Promise<{ user: AuthUser }> {
  let res: Response
  try {
    res = await fetch(`${API_BASE_URL}/api/auth/login/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    })
  } catch {
    throw new Error("Cannot reach server. Is the Django backend running on port 8000?")
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const message =
      typeof data.detail === "string"
        ? data.detail
        : Array.isArray(data.detail)
          ? data.detail.join(" ")
          : `Login failed (${res.status})`
    throw new Error(message)
  }
  const token =
    data.accessToken != null && typeof data.accessToken === "string"
      ? data.accessToken.trim()
      : ""
  const user = data.user as AuthUser
  if (token) setAccessToken(token)
  return { user }
}

export async function getMe(): Promise<AuthUser | null> {
  const token = getAccessToken()
  if (!token) return null
  const res = await fetch(`${API_BASE_URL}/api/auth/me/`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) return null
  const data = await res.json().catch(() => ({}))
  return (data.user as AuthUser) ?? null
}

export function logout(): void {
  clearAccessToken()
}
