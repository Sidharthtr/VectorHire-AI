"use client";
/**
 * Drag-and-drop PDF picker — surfaces a chosen resume File to its parent.
 *
 * What it does:
 * - Supports click-to-browse and drag/drop, rejecting non-PDF files with an alert
 * - Tracks the selected file locally for preview (name + KB size) and clear button
 * - Calls onFileSelect(file) so the parent page owns the actual File object
 *
 * Upstream (who imports this OR which URL renders it): app/(app)/upload/page.tsx
 * Downstream (what this imports): lucide-react icons, @/lib/utils cn (class merge helper)
 */
// useRef — access the hidden <input type="file">; useState — drag-highlight + selected file preview
import { useRef, useState } from "react";
// Upload/FileText/X icons — drop hint, selected-file badge, and the "Remove file" button
import { Upload, FileText, X } from "lucide-react";
// cn — conditional Tailwind classnames helper used for drag/selected/disabled states
import { cn } from "@/lib/utils";

interface ResumeUploadProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export default function ResumeUpload({ onFileSelect, disabled }: ResumeUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFile = (file: File) => {
    if (file.type !== "application/pdf") {
      alert("Only PDF files are accepted.");
      return;
    }
    setSelectedFile(file);
    onFileSelect(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const clearFile = () => {
    setSelectedFile(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="space-y-3">
      <div
        onClick={() => !disabled && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={cn(
          "border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all",
          dragging ? "border-brand-500 bg-brand-50" : "border-gray-300 hover:border-brand-400 hover:bg-gray-50",
          disabled && "opacity-50 cursor-not-allowed",
          selectedFile && "border-green-400 bg-green-50"
        )}
      >
        {selectedFile ? (
          <div className="space-y-2">
            <FileText size={40} className="mx-auto text-green-500" />
            <p className="font-medium text-gray-900">{selectedFile.name}</p>
            <p className="text-sm text-gray-500">{(selectedFile.size / 1024).toFixed(0)} KB</p>
          </div>
        ) : (
          <div className="space-y-3">
            <Upload size={40} className="mx-auto text-gray-400" />
            <div>
              <p className="font-semibold text-gray-700">Drop your resume here</p>
              <p className="text-sm text-gray-500">or click to browse — PDF only, max 10MB</p>
            </div>
          </div>
        )}
      </div>

      {selectedFile && (
        <button
          onClick={clearFile}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-red-500 transition-colors"
        >
          <X size={14} />
          Remove file
        </button>
      )}

      <input ref={inputRef} type="file" accept=".pdf" onChange={handleChange} className="hidden" />
    </div>
  );
}
