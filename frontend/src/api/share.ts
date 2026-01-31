import { api } from './client';
import type { ShareLink, ShareLinkCreate, ShareLinkResponse } from '../types';

export const shareApi = {
  createShareLink: async (data: ShareLinkCreate): Promise<ShareLinkResponse> => {
    // Convert expires_in_days to expiry_minutes for the backend
    const payload = {
      file_id: data.file_id,
      expiry_minutes: data.expires_in_days ? data.expires_in_days * 24 * 60 : data.expiry_minutes || 60,
      max_downloads: data.max_downloads,
      requires_auth: data.requires_auth,
    };
    const response = await api.post<ShareLinkResponse>('/share/', payload);
    // Add share_token alias
    return { ...response.data, share_token: response.data.token };
  },

  getMyShareLinks: async (): Promise<ShareLink[]> => {
    const response = await api.get<ShareLink[]>('/share/');
    // Add share_token and file aliases
    return response.data.map(link => ({
      ...link,
      share_token: link.token,
      file: { filename: link.filename },
    }));
  },

  getShareLinkInfo: async (token: string) => {
    const response = await api.get(`/share/${token}/info`);
    return response.data;
  },

  downloadViaShareLink: async (token: string, password?: string): Promise<{ blob: Blob; filename: string }> => {
    const response = await api.get(`/share/${token}/download`, {
      responseType: 'blob',
      params: password ? { password } : undefined,
    });
    // Extract filename from content-disposition header
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'download';
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/['"]/g, '');
      }
    }
    return { blob: response.data, filename };
  },

  revokeShareLink: async (linkId: number | string): Promise<void> => {
    await api.delete(`/share/${linkId}`);
  },
};
