import { useState } from 'react';
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
  Clock,
  Ban,
  ShieldX,
  KeyRound,
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

  // Classify error into a specific type for user-friendly display
  const classifyError = (error: unknown): { type: string; title: string; message: string; icon: 'expired' | 'limit' | 'password' | 'restricted' | 'generic' } => {
    const raw = (error instanceof Error ? error.message : getErrorMessage(error)).toLowerCase();

    if (raw.includes('expired') || raw.includes('not found or expired')) {
      return {
        type: 'expired',
        title: 'Link Expired',
        message: 'This share link has expired and is no longer available. Please ask the file owner to create a new share link.',
        icon: 'expired',
      };
    }
    if (raw.includes('download limit') || raw.includes('limit reached')) {
      return {
        type: 'limit',
        title: 'Download Limit Reached',
        message: 'This file has reached its maximum number of downloads. Please contact the file owner to generate a new share link with additional downloads.',
        icon: 'limit',
      };
    }
    if (raw.includes('invalid password') || raw.includes('password required')) {
      return {
        type: 'password',
        title: 'Incorrect Password',
        message: 'The password you entered is incorrect. Please check with the file owner and try again.',
        icon: 'password',
      };
    }
    if (raw.includes('restricted') || raw.includes('specific user') || raw.includes('authentication required')) {
      return {
        type: 'restricted',
        title: 'Access Restricted',
        message: 'You do not have permission to access this file. This link is restricted to an authorized user.',
        icon: 'restricted',
      };
    }
    return {
      type: 'generic',
      title: 'Download Failed',
      message: raw || 'Something went wrong while downloading. Please try again later or contact the file owner.',
      icon: 'generic',
    };
  };

  const errorIconMap = {
    expired: <Clock className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />,
    limit: <Ban className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />,
    password: <KeyRound className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />,
    restricted: <ShieldX className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />,
    generic: <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />,
  };

  const errorStyleMap: Record<string, string> = {
    expired: 'bg-amber-50 border-amber-200',
    limit: 'bg-orange-50 border-orange-200',
    password: 'bg-red-50 border-red-200',
    restricted: 'bg-red-50 border-red-200',
    generic: 'bg-red-50 border-red-200',
  };

  const errorTitleColorMap: Record<string, string> = {
    expired: 'text-amber-800',
    limit: 'text-orange-800',
    password: 'text-red-800',
    restricted: 'text-red-800',
    generic: 'text-red-800',
  };

  const errorMsgColorMap: Record<string, string> = {
    expired: 'text-amber-700',
    limit: 'text-orange-700',
    password: 'text-red-600',
    restricted: 'text-red-600',
    generic: 'text-red-600',
  };

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
      const classified = classifyError(error);
      if (classified.type === 'password') {
        toast.error(classified.title);
      } else {
        toast.error(classified.title);
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
    const classified = classifyError(infoError);

    const fullPageIconMap: Record<string, React.ReactNode> = {
      expired: <Clock className="w-16 h-16 text-amber-500 mx-auto mb-4" />,
      limit: <Ban className="w-16 h-16 text-orange-500 mx-auto mb-4" />,
      password: <KeyRound className="w-16 h-16 text-red-500 mx-auto mb-4" />,
      restricted: <ShieldX className="w-16 h-16 text-red-500 mx-auto mb-4" />,
      generic: <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />,
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="card max-w-md w-full p-8 text-center">
          {fullPageIconMap[classified.icon]}
          <h1 className="text-xl font-semibold text-gray-900 mb-3">
            {classified.title}
          </h1>
          <p className="text-gray-500 leading-relaxed">
            {classified.message}
          </p>
          <div className="mt-6 pt-4 border-t border-gray-100">
            <p className="text-xs text-gray-400">
              If you believe this is a mistake, please contact the person who shared this link with you.
            </p>
          </div>
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
            {downloadMutation.isError && (() => {
              const errInfo = classifyError(downloadMutation.error);
              // Don't show inline for password errors (toast is enough)
              if (errInfo.type === 'password') return null;
              return (
                <div className={`mt-4 p-4 border rounded-lg ${errorStyleMap[errInfo.icon]}`}>
                  <div className="flex items-start gap-3">
                    {errorIconMap[errInfo.icon]}
                    <div>
                      <h4 className={`font-medium ${errorTitleColorMap[errInfo.icon]}`}>
                        {errInfo.title}
                      </h4>
                      <p className={`text-sm mt-1 ${errorMsgColorMap[errInfo.icon]}`}>
                        {errInfo.message}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })()}

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
