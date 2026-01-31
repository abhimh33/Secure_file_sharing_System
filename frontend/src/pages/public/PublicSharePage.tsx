import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import {
  FileText,
  Download,
  Lock,
  AlertCircle,
  Loader2,
  Shield,
  CheckCircle,
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { shareApi, getErrorMessage } from '../../api';

export default function PublicSharePage() {
  const { token } = useParams<{ token: string }>();
  const [password, setPassword] = useState('');
  const [showPasswordInput, setShowPasswordInput] = useState(false);
  const [downloadComplete, setDownloadComplete] = useState(false);

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
        setShowPasswordInput(true);
        toast.error('This file is password protected');
      } else {
        toast.error(message);
      }
    },
  });

  const handleDownload = () => {
    if (!token) return;
    downloadMutation.mutate();
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
            <div className="bg-gray-50 rounded-xl p-6 mb-6 text-center">
              <FileText className="w-12 h-12 text-blue-500 mx-auto mb-3" />
              <p className="text-gray-600 text-sm">
                Someone shared a file with you
              </p>
            </div>

            {/* Password Input */}
            {showPasswordInput && (
              <div className="mb-4">
                <label className="label flex items-center gap-2">
                  <Lock className="w-4 h-4" />
                  Password Required
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter the password"
                  className="input"
                  autoFocus
                />
              </div>
            )}

            {/* Download Button */}
            <button
              onClick={handleDownload}
              disabled={downloadMutation.isPending}
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
