import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, FileText, Loader2, Check } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { filesApi, getErrorMessage } from '../../api';

interface FileUploadProps {
  onUploadComplete?: () => void;
}

interface UploadingFile {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'complete' | 'error';
  error?: string;
}

export default function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [description, setDescription] = useState('');

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map((file) => ({
      file,
      progress: 0,
      status: 'pending' as const,
    }));
    setUploadingFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxSize: 200 * 1024 * 1024, // 200MB
  });

  const removeFile = (index: number) => {
    setUploadingFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    if (uploadingFiles.length === 0) return;

    for (let i = 0; i < uploadingFiles.length; i++) {
      if (uploadingFiles[i].status !== 'pending') continue;

      setUploadingFiles((prev) =>
        prev.map((f, idx) =>
          idx === i ? { ...f, status: 'uploading' as const, progress: 50 } : f
        )
      );

      try {
        await filesApi.uploadFile(uploadingFiles[i].file, description || undefined);
        
        setUploadingFiles((prev) =>
          prev.map((f, idx) =>
            idx === i ? { ...f, status: 'complete' as const, progress: 100 } : f
          )
        );
        
        toast.success(`${uploadingFiles[i].file.name} uploaded successfully!`);
      } catch (error) {
        setUploadingFiles((prev) =>
          prev.map((f, idx) =>
            idx === i
              ? { ...f, status: 'error' as const, error: getErrorMessage(error) }
              : f
          )
        );
        toast.error(`Failed to upload ${uploadingFiles[i].file.name}`);
      }
    }

    onUploadComplete?.();
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const pendingCount = uploadingFiles.filter((f) => f.status === 'pending').length;
  const hasUploading = uploadingFiles.some((f) => f.status === 'uploading');

  return (
    <div className="space-y-4">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className={`w-12 h-12 mx-auto mb-4 ${isDragActive ? 'text-blue-500' : 'text-gray-400'}`} />
        <p className="text-gray-600 mb-2">
          {isDragActive
            ? 'Drop files here...'
            : 'Drag & drop files here, or click to select'}
        </p>
        <p className="text-sm text-gray-400">Max file size: 200MB</p>
      </div>

      {/* Description */}
      {uploadingFiles.length > 0 && (
        <div>
          <label className="label">Description (Optional)</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="input"
            placeholder="Add a description for your files..."
          />
        </div>
      )}

      {/* File List */}
      {uploadingFiles.length > 0 && (
        <div className="space-y-2">
          {uploadingFiles.map((item, index) => (
            <div
              key={index}
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
            >
              <div className={`p-2 rounded-lg ${
                item.status === 'complete' ? 'bg-green-100' :
                item.status === 'error' ? 'bg-red-100' : 'bg-blue-100'
              }`}>
                {item.status === 'uploading' ? (
                  <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                ) : item.status === 'complete' ? (
                  <Check className="w-5 h-5 text-green-600" />
                ) : (
                  <FileText className={`w-5 h-5 ${item.status === 'error' ? 'text-red-600' : 'text-blue-600'}`} />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {item.file.name}
                </p>
                <p className="text-xs text-gray-500">
                  {formatBytes(item.file.size)}
                  {item.error && <span className="text-red-500"> • {item.error}</span>}
                </p>
              </div>
              {item.status === 'pending' && (
                <button
                  onClick={() => removeFile(index)}
                  className="p-1 hover:bg-gray-200 rounded"
                  aria-label="Remove file"
                >
                  <X className="w-4 h-4 text-gray-500" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Upload Button */}
      {pendingCount > 0 && (
        <button
          onClick={uploadFiles}
          disabled={hasUploading}
          className="btn btn-primary w-full flex items-center justify-center gap-2"
        >
          {hasUploading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="w-5 h-5" />
              Upload {pendingCount} {pendingCount === 1 ? 'file' : 'files'}
            </>
          )}
        </button>
      )}
    </div>
  );
}
