import { type ChangeEvent, type DragEvent, useRef, useState } from "react";
import {
  CheckCircle2,
  CloudUpload,
  FileImage,
  LoaderCircle,
} from "lucide-react";

interface MediaUploadDropzoneProps {
  isUploading: boolean;
  onFilesSelected: (files: File[]) => void;
}

const ACCEPTED_TYPES =
  "image/jpeg,image/png,image/webp,image/avif,application/pdf";

export function MediaUploadDropzone({
  isUploading,
  onFilesSelected,
}: MediaUploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  function selectFiles(files: FileList | null) {
    if (!files?.length || isUploading) {
      return;
    }

    onFilesSelected(Array.from(files));
  }

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    selectFiles(event.target.files);
    event.target.value = "";
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();

    if (!isUploading) {
      setIsDragging(true);
    }
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
    selectFiles(event.dataTransfer.files);
  }

  return (
    <div
      className={`media-dropzone${
        isDragging ? " media-dropzone--dragging" : ""
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_TYPES}
        multiple
        hidden
        onChange={handleInputChange}
      />

      <div className="media-dropzone__icon">
        {isUploading ? (
          <LoaderCircle className="media-dropzone__spinner" size={27} />
        ) : (
          <CloudUpload size={27} />
        )}
      </div>

      <div className="media-dropzone__copy">
        <strong>
          {isUploading ? "Uploading media..." : "Drop files here to upload"}
        </strong>

        <span>JPEG, PNG, WebP, AVIF or PDF · up to 20 MB</span>
      </div>

      <button
        className="media-dropzone__button"
        type="button"
        disabled={isUploading}
        onClick={() => inputRef.current?.click()}
      >
        {isUploading ? (
          <>
            <LoaderCircle className="media-dropzone__spinner" size={17} />
            Uploading
          </>
        ) : (
          <>
            <FileImage size={17} />
            Choose files
          </>
        )}
      </button>

      {!isUploading && (
        <div className="media-dropzone__ready">
          <CheckCircle2 size={15} />
          R2 ready
        </div>
      )}
    </div>
  );
}
