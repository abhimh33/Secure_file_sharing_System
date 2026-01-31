import { useState } from 'react';
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
  Link as LinkIcon,
  Calendar,
  Eye,
  Copy,
  Check,
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { filesApi, shareApi, getErrorMessage } from '../../api';
import type { FileItem } from '../../types';
import FileUpload from '../../components/files/FileUpload';

export default function FilesPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [shareExpiry, setShareExpiry] = useState(7);
  const [shareMaxDownloads, setShareMaxDownloads] = useState<number | undefined>(undefined);
  const [sharePassword, setSharePassword] = useState('');
  const [createdShareLink, setCreatedShareLink] = useState<string | null>(null);
  const [linkCopied, setLinkCopied] = useState(false);

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
        password: sharePassword || undefined,
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
    setCreatedShareLink(null);
    setShowShareModal(true);
  };

  const handleCreateShare = () => {
    if (selectedFile) {
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
                  <label htmlFor="share-password" className="label flex items-center gap-2">
                    <LinkIcon className="w-4 h-4" />
                    Password (optional)
                  </label>
                  <input
                    id="share-password"
                    type="password"
                    value={sharePassword}
                    onChange={(e) => setSharePassword(e.target.value)}
                    placeholder="Add password protection"
                    className="input"
                  />
                </div>

                <button
                  onClick={handleCreateShare}
                  disabled={createShareMutation.isPending}
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
