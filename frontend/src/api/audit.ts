import { api } from './client';
import type { AuditLog } from '../types';

export const auditApi = {
  getAuditLogs: async (
    skip = 0,
    limit = 50,
    action?: string,
    userId?: number
  ): Promise<AuditLog[]> => {
    const response = await api.get<AuditLog[]>('/audit/', {
      params: { skip, limit, action, user_id: userId },
    });
    return response.data;
  },

  getAuditLogsByUser: async (userId: number, limit = 50): Promise<AuditLog[]> => {
    const response = await api.get<AuditLog[]>('/audit/', {
      params: { user_id: userId, limit },
    });
    return response.data;
  },
};
