import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  FileText,
  Download,
  Lock,
  AlertCircle,
  Loader2,
  Shield,
  CheckCircle,
  HardDrive,
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { shareApi, getErrorMessage } from '../../api';

export default function PublicSharePage() {
  const { token } = useParams<{ token: string }>();
  const [password, setPassword] = useState('');
  const [downloadComplete, setDownloadComplete] = useState(false);

  // Fetch share link info to check if password is required
  const { data: linkInfo, isLoading: isLoadingInfo, error: infoError } = useQuery({
    queryKey: ['shareLink', token],
    queryFn: () => shareApi.getShareLinkInfo(token!),
    enabled: !!token,
    retry: false,
  });

  const downloadMutation = useMutation({
    mutationFn: () =>
      shareApi.downloadViaShareLink(token!, password || undefined),
    onSuccess: (response) => {
      // Create download link
      const url = URL.createObjectURL(response.blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = response.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setDownloadComplete(true);
      toast.success('Download started!');
    },
    onError: (error: unknown) => {
      const message = getErrorMessage(error);
      if (message.toLowerCase().includes('password')) {
        toast.error('Invalid password');
      } else {
        toast.error(message);
      }
    },
  });

  const handleDownload = () => {
    if (!token) return;
    // If password is required but not entered, show error
    if (linkInfo?.has_password && !password) {
      toast.error('Please enter the password');
      return;
    }
    downloadMutation.mutate();
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="card max-w-md w-full p-8 text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-xl font-semibold text-gray-900 mb-2">
            Invalid Share Link
          </h1>
          <p className="text-gray-500">
            This share link is invalid or has been corrupted.
          </p>
        </div>
      </div>
    );
  }

  if (isLoadingInfo) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="card max-w-md w-full p-8 text-center">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading share link...</p>
        </div>
      </div>
    );
  }

  if (infoError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="card max-w-md w-full p-8 text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-xl font-semibold text-gray-900 mb-2">
            Link Not Available
          </h1>
          <p className="text-gray-500">
            This share link has expired, been revoked, or reached its download limit.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="card max-w-md w-full p-8">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">SecureFile Share</h1>
          <p className="text-gray-500 mt-1">Secure file sharing made simple</p>
        </div>

        {downloadComplete ? (
          <div className="text-center">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-10 h-10 text-green-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Download Complete!
            </h2>
            <p className="text-gray-500 mb-6">
              Your file has been downloaded successfully.
            </p>
            <button
              onClick={() => {
                setDownloadComplete(false);
                handleDownload();
              }}
              className="btn btn-secondary"
            >
              Download Again
            </button>
          </div>
        ) : (
          <>
            {/* File Info */}
            <div className="bg-gray-50 rounded-xl p-6 mb-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <FileText className="w-8 h-8 text-blue-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-gray-900 truncate">
                    {linkInfo?.filename || 'Shared File'}
                  </h3>
                  <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                    <HardDrive className="w-3.5 h-3.5" />
                    <span>{linkInfo?.size ? formatBytes(linkInfo.size) : 'Unknown size'}</span>
                  </div>
                </div>
              </div>
              {linkInfo?.has_password && (
                <div className="mt-3 pt-3 border-t border-gray-200 flex items-center gap-2 text-sm text-amber-600">
                  <Lock className="w-4 h-4" />
                  <span>This file is password protected</span>
                </div>
              )}
            </div>

            {/* Password Input - Always show if required */}
            {linkInfo?.has_password && (
              <div className="mb-4">
                <label htmlFor="share-password" className="label flex items-center gap-2">
                  <Lock className="w-4 h-4" />
                  Enter Password
                </label>
                <input
                  id="share-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter the password to download"
                  className="input"
                  autoFocus
                  onKeyDown={(e) => e.key === 'Enter' && handleDownload()}
                />
              </div>
            )}

            {/* Download Button */}
            <button
              onClick={handleDownload}
              disabled={downloadMutation.isPending || (linkInfo?.has_password && !password)}
              className="btn btn-primary w-full flex items-center justify-center gap-2"
            >
              {downloadMutation.isPending ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Downloading...
                </>
              ) : (
                <>
                  <Download className="w-5 h-5" />
                  Download File
                </>
              )}
            </button>

            {/* Error Display */}
            {downloadMutation.isError &&
              !getErrorMessage(downloadMutation.error)
                .toLowerCase()
                .includes('password') && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-medium text-red-800">
                        Download Failed
                      </h4>
                      <p className="text-sm text-red-600 mt-1">
                        {getErrorMessage(downloadMutation.error)}
                      </p>
                    </div>
                  </div>
                </div>
              )}

            {/* Info Box */}
            <div className="mt-6 text-center text-sm text-gray-500">
              <p>
                This link may have an expiration date or download limit.
                <br />
                Download while it's available.
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
