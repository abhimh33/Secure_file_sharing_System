import { useEffect, useState } from 'react';
import { 
  FolderOpen, 
  Share2, 
  Download, 
  TrendingUp,
  Clock,
  FileText
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { filesApi, shareApi } from '../../api';
import type { FileItem, ShareLink } from '../../types';
import { formatDistanceToNow } from 'date-fns';

export default function DashboardPage() {
  const { user } = useAuthStore();
  const [files, setFiles] = useState<FileItem[]>([]);
  const [shareLinks, setShareLinks] = useState<ShareLink[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [filesData, sharesData] = await Promise.all([
          filesApi.getFiles(),
          shareApi.getMyShareLinks(),
        ]);
        setFiles(filesData.slice(0, 5));
        setShareLinks(sharesData);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const totalSize = files.reduce((acc, file) => acc + file.size, 0);
  const activeShares = shareLinks.filter((link) => link.is_active).length;

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const stats = [
    {
      name: 'Total Files',
      value: files.length.toString(),
      icon: FolderOpen,
      color: 'bg-blue-500',
    },
    {
      name: 'Storage Used',
      value: formatBytes(totalSize),
      icon: TrendingUp,
      color: 'bg-green-500',
    },
    {
      name: 'Active Share Links',
      value: activeShares.toString(),
      icon: Share2,
      color: 'bg-purple-500',
    },
    {
      name: 'Total Downloads',
      value: shareLinks.reduce((acc, link) => acc + link.download_count, 0).toString(),
      icon: Download,
      color: 'bg-orange-500',
    },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.full_name || user?.email?.split('@')[0]}! 👋
        </h1>
        <p className="text-gray-600 mt-1">
          Here's an overview of your file sharing activity.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-xl ${stat.color}`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-600">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Files & Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Files */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Files</h2>
            <a href="/files" className="text-sm text-blue-600 hover:text-blue-700">
              View all →
            </a>
          </div>
          {files.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No files uploaded yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {files.slice(0, 5).map((file) => (
                <div
                  key={file.id}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <FileText className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.original_filename}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatBytes(file.size)} • {formatDistanceToNow(new Date(file.created_at), { addSuffix: true })}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Share Links */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Share Links</h2>
            <a href="/shares" className="text-sm text-blue-600 hover:text-blue-700">
              View all →
            </a>
          </div>
          {shareLinks.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Share2 className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No share links created yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {shareLinks.slice(0, 5).map((link) => (
                <div
                  key={link.id}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className={`p-2 rounded-lg ${link.is_active ? 'bg-green-100' : 'bg-gray-100'}`}>
                    <Share2 className={`w-5 h-5 ${link.is_active ? 'text-green-600' : 'text-gray-400'}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {link.filename}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <Clock className="w-3 h-3" />
                      <span>
                        {link.is_active 
                          ? `Expires ${formatDistanceToNow(new Date(link.expires_at), { addSuffix: true })}`
                          : 'Expired'}
                      </span>
                      <span>•</span>
                      <span>{link.download_count} downloads</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
