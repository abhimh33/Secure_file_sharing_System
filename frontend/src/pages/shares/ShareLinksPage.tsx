import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format, isPast } from 'date-fns';
import {
  Link as LinkIcon,
  Copy,
  Trash2,
  Check,
  ExternalLink,
  AlertCircle,
  Search,
  Loader2,
  Download,
  Calendar,
  Clock,
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { shareApi, getErrorMessage } from '../../api';
import type { ShareLink } from '../../types';

export default function ShareLinksPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const queryClient = useQueryClient();

  const { data: shareLinks = [], isLoading } = useQuery<ShareLink[]>({
    queryKey: ['shareLinks'],
    queryFn: () => shareApi.getMyShareLinks(),
  });

  const revokeMutation = useMutation({
    mutationFn: (linkId: number) => shareApi.revokeShareLink(linkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shareLinks'] });
      toast.success('Share link revoked successfully');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });

  const handleCopyLink = async (shareLink: ShareLink) => {
    const token = shareLink.share_token || shareLink.token;
    const link = `${window.location.origin}/share/${token}`;
    await navigator.clipboard.writeText(link);
    setCopiedId(shareLink.id);
    setTimeout(() => setCopiedId(null), 2000);
    toast.success('Link copied to clipboard!');
  };

  const handleRevoke = (shareLink: ShareLink) => {
    if (confirm('Are you sure you want to revoke this share link? It will no longer be accessible.')) {
      revokeMutation.mutate(shareLink.id);
    }
  };

  const getStatus = (shareLink: ShareLink) => {
    if (!shareLink.is_active) {
      return { label: 'Revoked', color: 'text-red-600 bg-red-50' };
    }
    if (shareLink.expires_at && isPast(new Date(shareLink.expires_at))) {
      return { label: 'Expired', color: 'text-orange-600 bg-orange-50' };
    }
    if (shareLink.max_downloads && shareLink.download_count >= shareLink.max_downloads) {
      return { label: 'Limit Reached', color: 'text-yellow-600 bg-yellow-50' };
    }
    return { label: 'Active', color: 'text-green-600 bg-green-50' };
  };

  const filteredLinks = shareLinks.filter((link) => {
    const filename = link.file?.filename || link.filename || '';
    const token = link.share_token || link.token || '';
    return filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
           token.toLowerCase().includes(searchTerm.toLowerCase());
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Share Links</h1>
        <p className="text-gray-500">Manage your file sharing links</p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          placeholder="Search by file name or token..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="input pl-10"
        />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card p-4">
          <div className="text-2xl font-bold text-gray-900">
            {shareLinks.length}
          </div>
          <div className="text-sm text-gray-500">Total Links</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-green-600">
            {shareLinks.filter((l) => l.is_active && (!l.expires_at || !isPast(new Date(l.expires_at)))).length}
          </div>
          <div className="text-sm text-gray-500">Active Links</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-blue-600">
            {shareLinks.reduce((acc, l) => acc + (l.download_count || 0), 0)}
          </div>
          <div className="text-sm text-gray-500">Total Downloads</div>
        </div>
      </div>

      {/* Links List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
        </div>
      ) : filteredLinks.length === 0 ? (
        <div className="text-center py-12">
          <LinkIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {searchTerm ? 'No links found' : 'No share links yet'}
          </h3>
          <p className="text-gray-500">
            {searchTerm
              ? 'Try a different search term'
              : 'Create share links from the Files page'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredLinks.map((shareLink) => {
            const status = getStatus(shareLink);
            const isAccessible = status.label === 'Active';

            return (
              <div
                key={shareLink.id}
                className={`card p-4 ${!isAccessible ? 'opacity-75' : ''}`}
              >
                <div className="flex items-start gap-4">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <LinkIcon className="w-6 h-6 text-blue-600" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-gray-900 truncate">
                        {shareLink.file?.filename || shareLink.filename || 'Unknown File'}
                      </h3>
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${status.color}`}
                      >
                        {status.label}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" />
                        Created {format(new Date(shareLink.created_at), 'MMM d, yyyy')}
                      </span>
                      {shareLink.expires_at && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          {isPast(new Date(shareLink.expires_at))
                            ? 'Expired'
                            : `Expires ${format(new Date(shareLink.expires_at), 'MMM d, yyyy')}`}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Download className="w-3.5 h-3.5" />
                        {shareLink.download_count || 0}
                        {shareLink.max_downloads && ` / ${shareLink.max_downloads}`} downloads
                      </span>
                    </div>

                    <div className="mt-2 flex items-center gap-2">
                      <code className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-600 truncate max-w-xs">
                        {shareLink.share_token || shareLink.token}
                      </code>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleCopyLink(shareLink)}
                      disabled={!isAccessible}
                      className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Copy link"
                    >
                      {copiedId === shareLink.id ? (
                        <Check className="w-5 h-5 text-green-600" />
                      ) : (
                        <Copy className="w-5 h-5" />
                      )}
                    </button>
                    <a
                      href={`/share/${shareLink.share_token || shareLink.token}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={`p-2 hover:bg-gray-100 rounded-lg text-gray-600 hover:text-green-600 ${
                        !isAccessible ? 'pointer-events-none opacity-50' : ''
                      }`}
                      title="Open link"
                    >
                      <ExternalLink className="w-5 h-5" />
                    </a>
                    {shareLink.is_active && (
                      <button
                        onClick={() => handleRevoke(shareLink)}
                        className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 hover:text-red-600"
                        title="Revoke link"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
        <div className="flex gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-medium text-blue-900 mb-1">About Share Links</h4>
            <p className="text-sm text-blue-700">
              Share links allow anyone with the link to download your files without needing an account.
              You can add password protection, set expiry dates, and limit the number of downloads.
              Revoked or expired links will no longer work.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
