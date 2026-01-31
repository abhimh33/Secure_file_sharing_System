import { api } from './client';
import type { FileItem, FileUploadResponse } from '../types';

export const filesApi = {
  uploadFile: async (file: File, description?: string): Promise<FileUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (description) {
      formData.append('description', description);
    }

    const response = await api.post<FileUploadResponse>('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getFiles: async (): Promise<FileItem[]> => {
    const response = await api.get<FileItem[]>('/files/');
    // Add file_size alias for size
    return response.data.map(file => ({
      ...file,
      file_size: file.size,
    }));
  },

  getFile: async (fileId: number): Promise<FileItem> => {
    const response = await api.get<FileItem>(`/files/${fileId}`);
    return { ...response.data, file_size: response.data.size };
  },

  downloadFile: async (fileId: number): Promise<Blob> => {
    const response = await api.get(`/files/${fileId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },

  deleteFile: async (fileId: number): Promise<void> => {
    await api.delete(`/files/${fileId}`);
  },

  updateFile: async (fileId: number, description: string): Promise<FileItem> => {
    const response = await api.put<FileItem>(`/files/${fileId}`, { description });
    return response.data;
  },
};
