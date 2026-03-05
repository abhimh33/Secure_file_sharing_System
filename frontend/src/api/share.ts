import { api } from './client';
import type { ShareLink, ShareLinkCreate, ShareLinkResponse } from '../types';

export interface ShareLinkInfo {
  token: string;
  file_id: number;
  filename: string;
  content_type: string;
  size: number;
  expires_at: string;
  is_valid: boolean;
  download_count: number;
  max_downloads: number | null;
  has_password: boolean;
}

export const shareApi = {
  createShareLink: async (data: ShareLinkCreate): Promise<ShareLinkResponse> => {
    // Convert expires_in_days to expiry_minutes for the backend
    const payload = {
      file_id: data.file_id,
      expiry_minutes: data.expires_in_days ? data.expires_in_days * 24 * 60 : data.expiry_minutes || 60,
      max_downloads: data.max_downloads,
      password: data.password,
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

  getShareLinkInfo: async (token: string): Promise<ShareLinkInfo> => {
    const response = await api.get<ShareLinkInfo>(`/share/${token}/info`);
    return response.data;
  },

  downloadViaShareLink: async (token: string, password?: string): Promise<{ blob: Blob; filename: string }> => {
    try {
      const response = await api.get(`/share/${token}/download`, {
        responseType: 'blob',
        params: password ? { password } : undefined,
      });
      // Extract filename from content-disposition header
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'download';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=(['"].*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }
      return { blob: response.data, filename };
    } catch (error: unknown) {
      // When responseType is 'blob', error response data is a Blob — parse it to extract the JSON detail
      if (typeof error === 'object' && error !== null && 'response' in error) {
        const axiosErr = error as { response?: { data?: Blob; status?: number } };
        if (axiosErr.response?.data instanceof Blob) {
          try {
            const text = await axiosErr.response.data.text();
            const json = JSON.parse(text);
            if (json.detail) {
              throw new Error(json.detail);
            }
          } catch (parseErr) {
            if (parseErr instanceof Error && parseErr.message !== 'Unexpected token') {
              throw parseErr;
            }
          }
        }
      }
      throw error;
    }
  },

  revokeShareLink: async (linkId: number | string): Promise<void> => {
    await api.delete(`/share/${linkId}`);
  },
};
