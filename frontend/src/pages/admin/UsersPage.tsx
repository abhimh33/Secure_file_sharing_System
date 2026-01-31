import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import {
  Users,
  Search,
  Loader2,
  Shield,
  ShieldCheck,
  User,
  CheckCircle,
  XCircle,
  ChevronDown,
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { usersApi, getErrorMessage } from '../../api';
import type { UserListItem, Role } from '../../types';

export default function UsersPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [roleMenuOpen, setRoleMenuOpen] = useState<number | null>(null);

  const queryClient = useQueryClient();

  const { data: users = [], isLoading } = useQuery<UserListItem[]>({
    queryKey: ['users'],
    queryFn: () => usersApi.getUsers(),
  });

  const { data: roles = [] } = useQuery<Role[]>({
    queryKey: ['roles'],
    queryFn: () => usersApi.getRoles(),
  });

  const assignRoleMutation = useMutation({
    mutationFn: ({ userId, roleName }: { userId: number; roleName: string }) =>
      usersApi.assignRole(userId, roleName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast.success('Role updated successfully');
      setRoleMenuOpen(null);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });

  const handleRoleChange = (userId: number, roleName: string) => {
    assignRoleMutation.mutate({ userId, roleName });
  };

  const getRoleBadge = (roleName: string | null | undefined) => {
    if (!roleName) return null;

    const isAdmin = roleName === 'admin';
    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
          isAdmin
            ? 'bg-purple-100 text-purple-700'
            : 'bg-gray-100 text-gray-700'
        }`}
      >
        {isAdmin ? (
          <ShieldCheck className="w-3 h-3" />
        ) : (
          <Shield className="w-3 h-3" />
        )}
        {roleName}
      </span>
    );
  };

  const filteredUsers = users.filter(
    (user) =>
      user.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
        <p className="text-gray-500">Manage users and their roles</p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          placeholder="Search by name or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="input pl-10"
        />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card p-4">
          <div className="text-2xl font-bold text-gray-900">{users.length}</div>
          <div className="text-sm text-gray-500">Total Users</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-green-600">
            {users.filter((u) => u.is_active).length}
          </div>
          <div className="text-sm text-gray-500">Active Users</div>
        </div>
        <div className="card p-4">
          <div className="text-2xl font-bold text-purple-600">
            {users.filter((u) => u.role_name === 'admin').length}
          </div>
          <div className="text-sm text-gray-500">Administrators</div>
        </div>
      </div>

      {/* Users Table */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
        </div>
      ) : filteredUsers.length === 0 ? (
        <div className="text-center py-12">
          <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {searchTerm ? 'No users found' : 'No users yet'}
          </h3>
          <p className="text-gray-500">
            {searchTerm ? 'Try a different search term' : 'Users will appear here once they register'}
          </p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Joined
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                          <User className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">
                            {user.full_name || 'N/A'}
                          </div>
                          <div className="text-sm text-gray-500">{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="relative">
                        <button
                          onClick={() =>
                            setRoleMenuOpen(roleMenuOpen === user.id ? null : user.id)
                          }
                          className="flex items-center gap-1 hover:bg-gray-100 rounded px-2 py-1"
                          aria-label="Change user role"
                        >
                          {getRoleBadge(user.role_name)}
                          <ChevronDown className="w-3 h-3 text-gray-400" />
                        </button>

                        {roleMenuOpen === user.id && (
                          <div className="absolute z-10 mt-1 w-40 bg-white rounded-lg shadow-lg border border-gray-200 py-1">
                            {roles.map((role) => (
                              <button
                                key={role.id}
                                onClick={() => handleRoleChange(user.id, role.name)}
                                className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 flex items-center gap-2 ${
                                  user.role_name === role.name ? 'bg-blue-50 text-blue-600' : ''
                                }`}
                              >
                                {role.name === 'admin' ? (
                                  <ShieldCheck className="w-4 h-4" />
                                ) : (
                                  <Shield className="w-4 h-4" />
                                )}
                                {role.name}
                                {user.role_name === role.name && (
                                  <CheckCircle className="w-4 h-4 ml-auto" />
                                )}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {user.is_active ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                          <CheckCircle className="w-3 h-3" />
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                          <XCircle className="w-3 h-3" />
                          Inactive
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.created_at
                        ? format(new Date(user.created_at), 'MMM d, yyyy')
                        : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
