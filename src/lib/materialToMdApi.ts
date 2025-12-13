export type AssetResponse = {
  path: string;
  content_type: string;
  data_base64: string; // base64 bytes
};

export type ConvertResponse = {
  markdown: string;
  assets: AssetResponse[];
};

export async function convertFile(file: File): Promise<ConvertResponse> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch("/api/material-to-md/convert", {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || "Conversion failed");
  }

  return res.json();
}
