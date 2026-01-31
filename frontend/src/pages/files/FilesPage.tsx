import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import {
  FileText,
  Download,
  Trash2,
  Share2,
  Upload,
  Search,
  Loader2,
  FileArchive,
  FileImage,
  FileVideo,
  FileAudio,
  File,
  X,
  Calendar,
  Eye,
  Copy,
  Check,
  Lock,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { filesApi, shareApi, getErrorMessage } from '../../api';
import type { FileItem } from '../../types';
import FileUpload from '../../components/files/FileUpload';

// Password validation function
const validatePassword = (password: string) => {
  const requirements = {
    minLength: password.length >= 8,
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumber: /[0-9]/.test(password),
    hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(password),
  };
  const isValid = Object.values(requirements).every(Boolean);
  return { requirements, isValid };
};

export default function FilesPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [shareExpiry, setShareExpiry] = useState(7);
  const [shareMaxDownloads, setShareMaxDownloads] = useState<number | undefined>(undefined);
  const [sharePassword, setSharePassword] = useState('');
  const [showPasswordField, setShowPasswordField] = useState(false);
  const [createdShareLink, setCreatedShareLink] = useState<string | null>(null);
  const [linkCopied, setLinkCopied] = useState(false);

  // Password validation
  const passwordValidation = useMemo(() => validatePassword(sharePassword), [sharePassword]);

  const queryClient = useQueryClient();

  const { data: files = [], isLoading } = useQuery<FileItem[]>({
    queryKey: ['files'],
    queryFn: () => filesApi.getFiles(),
  });

  const deleteMutation = useMutation({
    mutationFn: filesApi.deleteFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      toast.success('File deleted successfully');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });

  const createShareMutation = useMutation({
    mutationFn: (fileId: number) =>
      shareApi.createShareLink({
        file_id: fileId,
        expires_in_days: shareExpiry,
        max_downloads: shareMaxDownloads,
        password: showPasswordField && sharePassword ? sharePassword : undefined,
      }),
    onSuccess: (shareLink) => {
      queryClient.invalidateQueries({ queryKey: ['shareLinks'] });
      const link = `${window.location.origin}/share/${shareLink.token || shareLink.share_token}`;
      setCreatedShareLink(link);
      toast.success('Share link created!');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });

  const handleDownload = async (file: FileItem) => {
    try {
      const blob = await filesApi.downloadFile(file.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('Download started');
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  const handleDelete = (file: FileItem) => {
    if (confirm(`Are you sure you want to delete "${file.filename}"?`)) {
      deleteMutation.mutate(file.id);
    }
  };

  const handleShare = (file: FileItem) => {
    setSelectedFile(file);
    setShareExpiry(7);
    setShareMaxDownloads(undefined);
    setSharePassword('');
    setShowPasswordField(false);
    setCreatedShareLink(null);
    setShowShareModal(true);
  };

  const handleCreateShare = () => {
    if (selectedFile) {
      // Validate password if provided
      if (showPasswordField && sharePassword && !passwordValidation.isValid) {
        toast.error('Please enter a strong password that meets all requirements');
        return;
      }
      createShareMutation.mutate(selectedFile.id);
    }
  };

  const copyShareLink = async () => {
    if (createdShareLink) {
      await navigator.clipboard.writeText(createdShareLink);
      setLinkCopied(true);
      setTimeout(() => setLinkCopied(false), 2000);
      toast.success('Link copied to clipboard!');
    }
  };

  const getFileIcon = (mimeType: string | undefined) => {
    if (!mimeType) return <File className="w-8 h-8 text-gray-400" />;
    
    if (mimeType.startsWith('image/')) {
      return <FileImage className="w-8 h-8 text-purple-500" />;
    } else if (mimeType.startsWith('video/')) {
      return <FileVideo className="w-8 h-8 text-pink-500" />;
    } else if (mimeType.startsWith('audio/')) {
      return <FileAudio className="w-8 h-8 text-green-500" />;
    } else if (mimeType.includes('zip') || mimeType.includes('compressed')) {
      return <FileArchive className="w-8 h-8 text-yellow-500" />;
    } else if (mimeType.includes('text') || mimeType.includes('document')) {
      return <FileText className="w-8 h-8 text-blue-500" />;
    }
    return <File className="w-8 h-8 text-gray-400" />;
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const filteredFiles = files.filter((file) =>
    file.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Files</h1>
          <p className="text-gray-500">Manage your uploaded files</p>
        </div>
        <button
          onClick={() => setShowUploadModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Upload className="w-5 h-5" />
          Upload Files
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <label htmlFor="search-files" className="sr-only">Search files</label>
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          id="search-files"
          type="text"
          placeholder="Search files..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="input pl-10"
        />
      </div>

      {/* Files Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
        </div>
      ) : filteredFiles.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {searchTerm ? 'No files found' : 'No files yet'}
          </h3>
          <p className="text-gray-500 mb-4">
            {searchTerm
              ? 'Try a different search term'
              : 'Upload your first file to get started'}
          </p>
          {!searchTerm && (
            <button
              onClick={() => setShowUploadModal(true)}
              className="btn btn-primary"
            >
              Upload Files
            </button>
          )}
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredFiles.map((file) => (
            <div
              key={file.id}
              className="card p-4 flex items-center gap-4 hover:shadow-md transition-shadow"
            >
              <div className="flex-shrink-0">
                {getFileIcon(file.content_type)}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-medium text-gray-900 truncate">
                  {file.filename}
                </h3>
                <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                  <span>{formatBytes(file.size)}</span>
                  <span>•</span>
                  <span>{format(new Date(file.created_at), 'MMM d, yyyy')}</span>
                  {file.download_count !== undefined && (
                    <>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Download className="w-3 h-3" />
                        {file.download_count}
                      </span>
                    </>
                  )}
                </div>
                {file.description && (
                  <p className="text-sm text-gray-400 mt-1 truncate">
                    {file.description}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleDownload(file)}
                  className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 hover:text-blue-600"
                  title="Download"
                >
                  <Download className="w-5 h-5" />
                </button>
                <button
                  onClick={() => handleShare(file)}
                  className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 hover:text-green-600"
                  title="Share"
                >
                  <Share2 className="w-5 h-5" />
                </button>
                <button
                  onClick={() => handleDelete(file)}
                  className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 hover:text-red-600"
                  title="Delete"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setShowUploadModal(false)}
          />
          <div className="relative bg-white rounded-xl shadow-xl max-w-lg w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Upload Files</h2>
              <button
                onClick={() => setShowUploadModal(false)}
                className="p-1 hover:bg-gray-100 rounded"
                aria-label="Close upload modal"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            <FileUpload
              onUploadComplete={() => {
                queryClient.invalidateQueries({ queryKey: ['files'] });
                setShowUploadModal(false);
              }}
            />
          </div>
        </div>
      )}

      {/* Share Modal */}
      {showShareModal && selectedFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setShowShareModal(false)}
          />
          <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Share File</h2>
              <button
                onClick={() => setShowShareModal(false)}
                className="p-1 hover:bg-gray-100 rounded"
                aria-label="Close share modal"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="bg-gray-50 p-3 rounded-lg mb-4">
              <p className="font-medium text-gray-900 truncate">{selectedFile.filename}</p>
              <p className="text-sm text-gray-500">{formatBytes(selectedFile.size)}</p>
            </div>

            {createdShareLink ? (
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <p className="text-sm text-green-800 font-medium mb-2">Share link created!</p>
                  <div className="flex items-center gap-2">
                    <label htmlFor="share-link" className="sr-only">Share link</label>
                    <input
                      id="share-link"
                      type="text"
                      value={createdShareLink}
                      readOnly
                      className="input text-sm flex-1"
                    />
                    <button
                      onClick={copyShareLink}
                      className="btn btn-primary p-2"
                      aria-label="Copy share link"
                    >
                      {linkCopied ? (
                        <Check className="w-5 h-5" />
                      ) : (
                        <Copy className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                </div>
                <button
                  onClick={() => setShowShareModal(false)}
                  className="btn btn-secondary w-full"
                >
                  Done
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label htmlFor="share-expiry" className="label flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    Expiry (days)
                  </label>
                  <select
                    id="share-expiry"
                    value={shareExpiry}
                    onChange={(e) => setShareExpiry(Number(e.target.value))}
                    className="input"
                  >
                    <option value={1}>1 day</option>
                    <option value={3}>3 days</option>
                    <option value={7}>7 days</option>
                    <option value={14}>14 days</option>
                    <option value={30}>30 days</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="max-downloads" className="label flex items-center gap-2">
                    <Eye className="w-4 h-4" />
                    Max Downloads (optional)
                  </label>
                  <input
                    id="max-downloads"
                    type="number"
                    min={1}
                    value={shareMaxDownloads || ''}
                    onChange={(e) =>
                      setShareMaxDownloads(e.target.value ? Number(e.target.value) : undefined)
                    }
                    placeholder="Unlimited"
                    className="input"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="label flex items-center gap-2 mb-0">
                      <Lock className="w-4 h-4" />
                      Password Protection
                    </label>
                    <button
                      type="button"
                      onClick={() => {
                        setShowPasswordField(!showPasswordField);
                        if (showPasswordField) setSharePassword('');
                      }}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        showPasswordField ? 'bg-blue-600' : 'bg-gray-200'
                      }`}
                      aria-label="Toggle password protection"
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          showPasswordField ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                  
                  {showPasswordField && (
                    <div className="space-y-3">
                      <input
                        id="share-password"
                        type="password"
                        value={sharePassword}
                        onChange={(e) => setSharePassword(e.target.value)}
                        placeholder="Enter a strong password"
                        className={`input ${sharePassword && !passwordValidation.isValid ? 'border-red-300 focus:border-red-500 focus:ring-red-200' : ''}`}
                        autoFocus
                      />
                      
                      {/* Password Requirements */}
                      <div className="bg-gray-50 rounded-lg p-3 space-y-1.5">
                        <p className="text-xs font-medium text-gray-700 mb-2">Password must contain:</p>
                        <div className="grid grid-cols-2 gap-1.5 text-xs">
                          <div className={`flex items-center gap-1.5 ${passwordValidation.requirements.minLength ? 'text-green-600' : 'text-gray-500'}`}>
                            {passwordValidation.requirements.minLength ? (
                              <CheckCircle2 className="w-3.5 h-3.5" />
                            ) : (
                              <AlertCircle className="w-3.5 h-3.5" />
                            )}
                            At least 8 characters
                          </div>
                          <div className={`flex items-center gap-1.5 ${passwordValidation.requirements.hasUppercase ? 'text-green-600' : 'text-gray-500'}`}>
                            {passwordValidation.requirements.hasUppercase ? (
                              <CheckCircle2 className="w-3.5 h-3.5" />
                            ) : (
                              <AlertCircle className="w-3.5 h-3.5" />
                            )}
                            One uppercase letter
                          </div>
                          <div className={`flex items-center gap-1.5 ${passwordValidation.requirements.hasLowercase ? 'text-green-600' : 'text-gray-500'}`}>
                            {passwordValidation.requirements.hasLowercase ? (
                              <CheckCircle2 className="w-3.5 h-3.5" />
                            ) : (
                              <AlertCircle className="w-3.5 h-3.5" />
                            )}
                            One lowercase letter
                          </div>
                          <div className={`flex items-center gap-1.5 ${passwordValidation.requirements.hasNumber ? 'text-green-600' : 'text-gray-500'}`}>
                            {passwordValidation.requirements.hasNumber ? (
                              <CheckCircle2 className="w-3.5 h-3.5" />
                            ) : (
                              <AlertCircle className="w-3.5 h-3.5" />
                            )}
                            One number
                          </div>
                          <div className={`flex items-center gap-1.5 ${passwordValidation.requirements.hasSpecial ? 'text-green-600' : 'text-gray-500'}`}>
                            {passwordValidation.requirements.hasSpecial ? (
                              <CheckCircle2 className="w-3.5 h-3.5" />
                            ) : (
                              <AlertCircle className="w-3.5 h-3.5" />
                            )}
                            One special character
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <button
                  onClick={handleCreateShare}
                  disabled={createShareMutation.isPending || (showPasswordField && !!sharePassword && !passwordValidation.isValid)}
                  className="btn btn-primary w-full flex items-center justify-center gap-2"
                >
                  {createShareMutation.isPending ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Share2 className="w-5 h-5" />
                      Create Share Link
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
