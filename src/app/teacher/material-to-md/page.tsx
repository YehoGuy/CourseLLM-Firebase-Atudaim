"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { convertFile, type ConvertResponse } from "@/lib/materialToMdApi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { FileText, Upload, Loader2, ImageIcon, Download, FileJson } from "lucide-react";

function base64ToDataUrl(contentType: string, b64: string) {
  return `data:${contentType};base64,${b64}`;
}

// --- SMART FORMATTER FUNCTION ---
function cleanMarkdown(rawText: string): string {
  if (!rawText) return "";
  
  let cleaned = rawText;

  // 1. Remove HTML tags
  cleaned = cleaned.replace(/<[^>]+>/g, "");

  // 2. Fix PowerPoint "Vertical Tabs"
  cleaned = cleaned.replace(/\u000b/g, "\n");

  // 3. Remove artifacts like "‹#›"
  cleaned = cleaned.replace(/‹#›/g, "");

  // 4. Apply Smart Formatting
  const lines = cleaned.split('\n');
  const formattedLines = lines.map((line, index) => {
    const trimmed = line.trim();
    if (!trimmed) return ""; 

    if (trimmed.match(/^Slide \d+$/i)) {
      return `\n## ${trimmed}\n`;
    }

    const prevLine = lines[index - 1]?.trim();
    if (prevLine && prevLine.match(/^Slide \d+$/i)) {
      return `### ${trimmed}\n`;
    }

    return `* ${trimmed}`;
  });

  return formattedLines.join('\n');
}
// --------------------------------

export default function MaterialToMdPage() {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ConvertResponse | null>(null);
  const { toast } = useToast();

  async function onConvert() {
    if (!file) return;
    setBusy(true);
    setResult(null);

    try {
      const r = await convertFile(file);
      setResult(r);
      toast({
        title: "Conversion Successful",
        description: `Successfully extracted ${r.assets.length} assets from ${file.name}.`,
      });
    } catch (e: any) {
      console.error(e);
      toast({
        variant: "destructive",
        title: "Conversion Failed",
        description: e?.message ?? "An error occurred while processing the file.",
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold font-headline">Material → Markdown</h1>
        <p className="text-muted-foreground">
          Convert your educational materials (PPTX, DOCX, PDF) into clean Markdown with extracted assets.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column: Upload & Controls */}
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Upload File</CardTitle>
              <CardDescription>Select a file to begin conversion.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid w-full max-w-sm items-center gap-1.5">
                <Label htmlFor="file-upload">Document</Label>
                <Input
                  id="file-upload"
                  type="file"
                  accept=".pptx,.docx,.pdf,.txt,.html"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  disabled={busy}
                />
              </div>

              <Button 
                onClick={onConvert} 
                disabled={busy || !file} 
                className="w-full"
              >
                {busy ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Convert to Markdown
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Asset List */}
          {result && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ImageIcon className="h-5 w-5" />
                  Extracted Assets
                </CardTitle>
                <CardDescription>
                  {result.assets.length} assets found
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="h-[300px]">
                  {result.assets.length === 0 ? (
                    <div className="p-4 text-center text-sm text-muted-foreground">
                      No images or assets found in this document.
                    </div>
                  ) : (
                    <div className="flex flex-col">
                      {result.assets.map((a, i) => {
                        const url = base64ToDataUrl(a.content_type, a.data_base64);
                        const isImage = a.content_type.startsWith("image/");
                        return (
                          <div key={i} className="flex items-center justify-between border-b p-4 last:border-0 hover:bg-muted/50">
                            <div className="flex items-center gap-3 overflow-hidden">
                              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded bg-muted">
                                {isImage ? (
                                  <img src={url} alt="thumbnail" className="h-full w-full object-cover" />
                                ) : (
                                  <FileJson className="h-5 w-5 text-muted-foreground" />
                                )}
                              </div>
                              <div className="min-w-0 flex-1">
                                <p className="truncate text-sm font-medium" title={a.path}>
                                  {a.path.split('/').pop()}
                                </p>
                                <p className="text-xs text-muted-foreground">{a.content_type}</p>
                              </div>
                            </div>
                            <Button variant="ghost" size="icon" asChild>
                              <a href={url} download={a.path.split("/").pop() ?? "asset"}>
                                <Download className="h-4 w-4" />
                              </a>
                            </Button>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column: Markdown Preview */}
        <div className="lg:col-span-2">
          <Card className="h-full flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Markdown Preview
              </CardTitle>
            </CardHeader>
            <Separator />
            <CardContent className="flex-1 p-0">
              <ScrollArea className="h-[600px] w-full p-6">
                {!result ? (
                  <div className="flex h-full flex-col items-center justify-center text-muted-foreground opacity-50">
                    <FileText className="mb-4 h-16 w-16" />
                    <p>Upload a file to see the generated Markdown here.</p>
                  </div>
                ) : (
                  <div className="prose prose-sm dark:prose-invert max-w-none" dir="auto">
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        // This intercepts the images!
                        img: ({ node, ...props }) => {
                          // 1. Find the asset that matches this image URL (e.g., "assets/slide25_img1.jpg")
                          const asset = result.assets.find(a => props.src?.includes(a.path));
                          
                          // 2. If found, use the Base64 data instead of the broken link
                          const src = asset 
                            ? base64ToDataUrl(asset.content_type, asset.data_base64) 
                            : props.src;
                            
                          return (
                            <img 
                              {...props} 
                              src={src} 
                              className="rounded-lg border my-4 max-h-[400px] object-contain" 
                            />
                          );
                        }
                      }}
                    >
                      {cleanMarkdown(result.markdown) || "_(No text content found)_"}
                    </ReactMarkdown>
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}