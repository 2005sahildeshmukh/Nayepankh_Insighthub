"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useWorkspace } from "@/providers/workspace-provider";
import { uploadDataset } from "@/lib/api/datasets";
import { UploadCloud, FileSpreadsheet, AlertCircle, Loader2, ArrowLeft } from "lucide-react";
import { formatOptionalNumber } from "@/lib/formatters";
import Link from "next/link";

export default function UploadDatasetPage() {
  const { activeWorkspace } = useWorkspace();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    setError(null);
    const validTypes = [
      "text/csv", 
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "application/vnd.ms-excel"
    ];
    const extension = selectedFile.name.split('.').pop()?.toLowerCase();
    
    if (!validTypes.includes(selectedFile.type) && extension !== 'csv' && extension !== 'xlsx') {
      setError("Please select a valid CSV or XLSX file.");
      setFile(null);
      return;
    }
    
    if (selectedFile.size > 25 * 1024 * 1024) {
      setError("File exceeds the 25 MB limit.");
      setFile(null);
      return;
    }
    
    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file || !activeWorkspace) return;
    
    setIsUploading(true);
    setError(null);
    
    try {
      const dataset = await uploadDataset(activeWorkspace.id, file);
      // Navigate to mapping page immediately
      router.push(`/w/${activeWorkspace.id}/datasets/${dataset.id}/mapping`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred during upload.");
      setIsUploading(false);
    }
  };

  if (!activeWorkspace) return null;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-4 mb-8">
        <Link 
          href={`/w/${activeWorkspace.id}/datasets`}
          className="p-2 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Upload Dataset</h1>
          <p className="text-muted-foreground">Upload a CSV or Excel file up to 25MB.</p>
        </div>
      </div>

      <div 
        className={`border-2 border-dashed rounded-xl p-12 transition-all ${
          dragActive ? "border-primary bg-primary/5" : "border-border bg-card hover:bg-accent/50"
        } ${isUploading ? "pointer-events-none" : ""}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center justify-center text-center">
          <div className="h-20 w-20 rounded-full bg-primary/10 flex items-center justify-center mb-6">
            {file ? (
              <FileSpreadsheet className="h-10 w-10 text-primary" />
            ) : (
              <UploadCloud className="h-10 w-10 text-primary" />
            )}
          </div>
          
          {file ? (
            <div className="space-y-2">
              <h3 className="text-xl font-semibold text-foreground">{file.name}</h3>
              <p className="text-sm text-muted-foreground">
                {formatOptionalNumber(file.size / 1024 / 1024, 2)} MB
              </p>
              <button 
                onClick={() => setFile(null)}
                className="text-sm text-destructive hover:underline mt-2"
                disabled={isUploading}
              >
                Remove file
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <h3 className="text-xl font-semibold text-foreground">Drag & drop your file here</h3>
              <p className="text-sm text-muted-foreground mb-4">
                or click to browse from your computer
              </p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground h-9 px-4 py-2"
              >
                Browse Files
              </button>
              <input 
                ref={fileInputRef}
                type="file" 
                className="hidden" 
                accept=".csv,.xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,text/csv"
                onChange={handleChange}
              />
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-md bg-destructive/10 text-destructive flex items-center gap-3 border border-destructive/20">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {isUploading && (
        <div className="p-6 rounded-md bg-primary/5 border border-primary/20 flex flex-col items-center justify-center text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <div>
            <h4 className="font-medium text-foreground">Uploading and inspecting dataset...</h4>
            <p className="text-sm text-muted-foreground">This might take a moment depending on the file size.</p>
          </div>
        </div>
      )}

      <div className="flex justify-end pt-4">
        <button
          onClick={handleUpload}
          disabled={!file || isUploading}
          className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/90 h-10 px-8"
        >
          {isUploading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            'Upload and Continue'
          )}
        </button>
      </div>
    </div>
  );
}
