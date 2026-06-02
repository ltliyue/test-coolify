import { useRef, useState, type DragEvent, type ChangeEvent } from "react";
import { Upload, FileUp } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "../components/ui/PageHeader";
import { Button } from "../components/ui/Button";
import { Input, Label } from "../components/ui/Input";
import { Card } from "../components/ui/Card";
import { api, extractErrorMessage } from "../lib/api";

export default function Imports() {
  const [file, setFile] = useState<File | null>(null);
  const [platform, setPlatform] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const handleFile = (f: File | null) => {
    setFile(f);
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0] ?? null;
    handleFile(f);
  };

  const onPick = (e: ChangeEvent<HTMLInputElement>) => {
    handleFile(e.target.files?.[0] ?? null);
  };

  const onSubmit = async () => {
    if (!file) {
      toast.error("Please select a file first");
      return;
    }
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      if (platform) form.append("platform", platform);
      await api.post("/imports/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success("Upload complete", {
        description: `${file.name} queued for processing`,
      });
      setFile(null);
      setPlatform("");
      if (inputRef.current) inputRef.current.value = "";
    } catch (err) {
      toast.error("Upload failed", {
        description: extractErrorMessage(err),
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Imports"
        description="Upload CSV, JSON, or Excel files to ingest data into the warehouse."
      />

      <Card className="p-6">
        <div className="space-y-5">
          <div>
            <Label htmlFor="platform">Source platform (optional)</Label>
            <Input
              id="platform"
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              placeholder="e.g. meta, ga4, hubspot"
            />
          </div>

          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors ${
              dragOver
                ? "border-accent bg-accent/5"
                : "border-border bg-muted/20"
            }`}
          >
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
              <Upload className="h-5 w-5" />
            </div>
            <h3 className="text-base font-semibold">
              Drag & drop your file here
            </h3>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground">
              Supports CSV, JSON, XLSX. Max 100MB per file.
            </p>
            <input
              ref={inputRef}
              type="file"
              className="hidden"
              accept=".csv,.json,.xlsx,.xls"
              onChange={onPick}
            />
            <Button
              variant="outline"
              size="sm"
              className="mt-4"
              onClick={() => inputRef.current?.click()}
            >
              <FileUp className="h-3.5 w-3.5" />
              Browse files
            </Button>
            {file && (
              <p className="mt-3 text-xs text-muted-foreground">
                Selected: <span className="font-medium">{file.name}</span> (
                {(file.size / 1024).toFixed(1)} KB)
              </p>
            )}
          </div>

          <div className="flex justify-end">
            <Button onClick={onSubmit} loading={uploading} disabled={!file}>
              <Upload className="h-4 w-4" />
              Upload
            </Button>
          </div>
        </div>
      </Card>
    </>
  );
}
