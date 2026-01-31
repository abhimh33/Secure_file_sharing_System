import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import {
  ClipboardList,
  Search,
  Loader2,
  Filter,
  Download,
  Upload,
  Share2,
  Trash2,
  LogIn,
  LogOut,
  User,
  Eye,
  Calendar,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { auditApi } from '../../api';
import type { AuditLog } from '../../types';

const ACTION_ICONS: Record<string, React.ReactNode> = {
  login: <LogIn className="w-4 h-4" />,
  logout: <LogOut className="w-4 h-4" />,
  file_upload: <Upload className="w-4 h-4" />,
  file_download: <Download className="w-4 h-4" />,
  file_delete: <Trash2 className="w-4 h-4" />,
  share_create: <Share2 className="w-4 h-4" />,
  share_revoke: <Trash2 className="w-4 h-4" />,
  share_download: <Download className="w-4 h-4" />,
};

const ACTION_COLORS: Record<string, string> = {
  login: 'bg-green-100 text-green-600',
  logout: 'bg-gray-100 text-gray-600',
  file_upload: 'bg-blue-100 text-blue-600',
  file_download: 'bg-purple-100 text-purple-600',
  file_delete: 'bg-red-100 text-red-600',
  share_create: 'bg-yellow-100 text-yellow-600',
  share_revoke: 'bg-orange-100 text-orange-600',
  share_download: 'bg-cyan-100 text-cyan-600',
};

export default function AuditLogsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [actionFilter, setActionFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const limit = 20;

  const { data: logs = [], isLoading } = useQuery<AuditLog[]>({
    queryKey: ['auditLogs', page, limit],
    queryFn: () => auditApi.getAuditLogs((page - 1) * limit, limit),
  });

  const total = logs.length;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  const getActionIcon = (action: string) => {
    return ACTION_ICONS[action] || <Eye className="w-4 h-4" />;
  };

  const getActionColor = (action: string) => {
    return ACTION_COLORS[action] || 'bg-gray-100 text-gray-600';
  };

  const formatAction = (action: string) => {
    return action.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  };

  const filteredLogs = logs.filter((log: AuditLog) => {
    const matchesSearch =
      log.user_email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.details?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesAction = !actionFilter || log.action === actionFilter;

    return matchesSearch && matchesAction;
  });

  const uniqueActions = [...new Set(logs.map((log: AuditLog) => log.action))];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Audit Logs</h1>
        <p className="text-gray-500">Track all system activities and user actions</p>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search by user, action, or details..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input pl-10"
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <select
            aria-label="Filter by action"
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="input pl-10 pr-8 appearance-none cursor-pointer"
          >
            <option value="">All Actions</option>
            {uniqueActions.map((action: string) => (
              <option key={action} value={action}>
                {formatAction(action)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="text-2xl font-bold text-gray-900">{total}</div>
          <div className="text-sm text-gray-500">Total Events</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-green-600">
            {logs.filter((l) => l.action === 'login').length}
          </div>
          <div className="text-sm text-gray-500">Logins</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-blue-600">
            {logs.filter((l) => l.action.startsWith('file_')).length}
          </div>
          <div className="text-sm text-gray-500">File Operations</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-purple-600">
            {logs.filter((l) => l.action.startsWith('share_')).length}
          </div>
          <div className="text-sm text-gray-500">Share Operations</div>
        </div>
      </div>

      {/* Logs List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
        </div>
      ) : filteredLogs.length === 0 ? (
        <div className="text-center py-12">
          <ClipboardList className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {searchTerm || actionFilter ? 'No logs found' : 'No audit logs yet'}
          </h3>
          <p className="text-gray-500">
            {searchTerm || actionFilter
              ? 'Try adjusting your filters'
              : 'Activity logs will appear here'}
          </p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Action
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Details
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    IP Address
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Time
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <div
                          className={`p-1.5 rounded-lg ${getActionColor(log.action)}`}
                        >
                          {getActionIcon(log.action)}
                        </div>
                        <span className="text-sm font-medium text-gray-900">
                          {formatAction(log.action)}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                          <User className="w-4 h-4 text-gray-500" />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {log.user_email || 'N/A'}
                          </div>
                          <div className="text-xs text-gray-500">
                            User ID: {log.user_id || 'Unknown'}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm text-gray-600 max-w-xs truncate">
                        {log.details || '-'}
                      </p>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <code className="text-sm text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                        {log.ip_address || 'N/A'}
                      </code>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-1 text-sm text-gray-500">
                        <Calendar className="w-3.5 h-3.5" />
                        {format(new Date(log.created_at), 'MMM d, yyyy HH:mm')}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200">
              <div className="text-sm text-gray-500">
                Showing {(page - 1) * limit + 1} to{' '}
                {Math.min(page * limit, total)} of {total} entries
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Previous page"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <span className="text-sm text-gray-600">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Next page"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
