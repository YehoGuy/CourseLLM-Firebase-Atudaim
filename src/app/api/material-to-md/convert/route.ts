import { NextResponse } from "next/server";

const BASE = process.env.MATERIAL_TO_MD_BASE_URL; 

export async function POST(req: Request) {
  if (!BASE) return new NextResponse("Missing MATERIAL_TO_MD_BASE_URL", { status: 500 });

  const form = await req.formData();

  const res = await fetch(`${BASE}/convert`, {
    method: "POST",
    body: form,
  });

  const text = await res.text();
  return new NextResponse(text, {
    status: res.status,
    headers: { "content-type": res.headers.get("content-type") ?? "application/json" },
  });
}
