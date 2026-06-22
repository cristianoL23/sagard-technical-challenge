import { NextResponse } from "next/server";

import { acceptPendingRecord } from "@/lib/reviewStore";

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as { id?: string };
    if (!body.id) {
      return NextResponse.json({ error: "Missing record id" }, { status: 400 });
    }

    const counts = acceptPendingRecord(body.id);
    return NextResponse.json(counts);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Accept failed";
    const status = message.includes("not found") ? 404 : 400;
    return NextResponse.json({ error: message }, { status });
  }
}
