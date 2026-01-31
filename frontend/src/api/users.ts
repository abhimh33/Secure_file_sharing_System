import { api } from './client';
import type { UserListItem, User, Role } from '../types';

export const usersApi = {
  getUsers: async (): Promise<UserListItem[]> => {
    const response = await api.get<UserListItem[]>('/users/');
    return response.data;
  },

  getUser: async (userId: number): Promise<User> => {
    const response = await api.get<User>(`/users/${userId}`);
    return response.data;
  },

  updateMe: async (data: { full_name?: string }): Promise<User> => {
    const response = await api.put<User>('/users/me', data);
    return response.data;
  },

  updateUser: async (userId: number, data: { full_name?: string; is_active?: boolean }): Promise<User> => {
    const response = await api.put<User>(`/users/${userId}`, data);
    return response.data;
  },

  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    await api.post('/users/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },

  deactivateUser: async (userId: number): Promise<void> => {
    await api.delete(`/users/${userId}`);
  },

  assignRole: async (userId: number, roleName: string): Promise<User> => {
    const response = await api.put<User>(`/users/${userId}/role`, { role_name: roleName });
    return response.data;
  },

  getRoles: async (): Promise<Role[]> => {
    const response = await api.get<Role[]>('/users/roles/list');
    return response.data;
  },
};
