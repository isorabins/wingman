/**
 * Photo upload utility for WingmanMatch profile setup
 * Handles secure photo uploads to Supabase Storage with validation
 */

import { supabase } from '../lib/supabase-client'
import { SupabaseClient } from '@supabase/supabase-js'

// File validation constants
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
const BUCKET_NAME = 'profile-photos';

export interface PhotoUploadResult {
  success: boolean;
  photoUrl?: string;
  error?: string;
}

export interface PhotoUploadProgress {
  progress: number;
  stage: 'validating' | 'uploading' | 'processing' | 'complete';
}

export class PhotoUploadService {
  private supabase: SupabaseClient

  constructor() {
    this.supabase = supabase
  }

  /**
   * Validate photo file before upload
   */
  validatePhotoFile(file: File): { valid: boolean; error?: string } {
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return {
        valid: false,
        error: `File too large. Maximum size is ${MAX_FILE_SIZE / (1024 * 1024)}MB`
      };
    }

    // Check MIME type
    if (!ALLOWED_MIME_TYPES.includes(file.type)) {
      return {
        valid: false,
        error: `Invalid file type. Allowed types: ${ALLOWED_MIME_TYPES.join(', ')}`
      };
    }

    // Basic validation passed (file header validation can be done during upload)
    return { valid: true };
  }

  /**
   * Validate photo file header (async version for thorough validation)
   */
  async validatePhotoFileAsync(file: File): Promise<{ valid: boolean; error?: string }> {
    // First do basic validation
    const basicValidation = this.validatePhotoFile(file);
    if (!basicValidation.valid) {
      return basicValidation;
    }

    // Check if it's actually an image by reading file header
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const arr = new Uint8Array(e.target?.result as ArrayBuffer);
        const header = Array.from(arr.slice(0, 4)).map(b => b.toString(16).padStart(2, '0')).join('');
        
        // Check for common image file signatures
        const imageSignatures = {
          'ffd8ffe0': 'JPEG',
          'ffd8ffe1': 'JPEG',
          'ffd8ffe2': 'JPEG',
          '89504e47': 'PNG',
          '47494638': 'GIF',
          '52494646': 'WEBP' // Actually checks for RIFF, WEBP is more complex
        };

        const isValidImage = Object.keys(imageSignatures).some(sig => 
          header.startsWith(sig.toLowerCase())
        );

        if (!isValidImage) {
          resolve({
            valid: false,
            error: 'File does not appear to be a valid image'
          });
        } else {
          resolve({ valid: true });
        }
      };
      reader.onerror = () => resolve({
        valid: false,
        error: 'Could not read file for validation'
      });
      reader.readAsArrayBuffer(file.slice(0, 4));
    });
  }

  /**
   * Generate unique file path for user photo
   */
  private generateFilePath(userId: string, fileName: string): string {
    const timestamp = Date.now();
    const randomId = Math.random().toString(36).substring(2, 15);
    const fileExtension = fileName.split('.').pop()?.toLowerCase() || 'jpg';
    return `${userId}/${timestamp}_${randomId}.${fileExtension}`;
  }

  /**
   * Upload photo to Supabase Storage
   */
  async uploadPhoto(
    file: File, 
    userId: string,
    onProgress?: (progress: PhotoUploadProgress) => void
  ): Promise<PhotoUploadResult> {
    try {
      // Validate file
      onProgress?.({ progress: 10, stage: 'validating' });
      
      const validation = await this.validatePhotoFileAsync(file);
      if (!validation.valid) {
        return {
          success: false,
          error: validation.error
        };
      }

      // Generate unique file path
      const filePath = this.generateFilePath(userId, file.name);
      
      onProgress?.({ progress: 30, stage: 'uploading' });

      // Upload to Supabase Storage
      const { data, error } = await this.supabase.storage
        .from(BUCKET_NAME)
        .upload(filePath, file, {
          cacheControl: '3600',
          upsert: false
        });

      if (error) {
        console.error('Storage upload error:', error);
        return {
          success: false,
          error: `Upload failed: ${error.message}`
        };
      }

      onProgress?.({ progress: 80, stage: 'processing' });

      // Get public URL
      const { data: urlData } = this.supabase.storage
        .from(BUCKET_NAME)
        .getPublicUrl(filePath);

      if (!urlData?.publicUrl) {
        return {
          success: false,
          error: 'Failed to generate photo URL'
        };
      }

      onProgress?.({ progress: 100, stage: 'complete' });

      return {
        success: true,
        photoUrl: urlData.publicUrl
      };

    } catch (error) {
      console.error('Photo upload error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Upload failed'
      };
    }
  }

  /**
   * Delete existing photo (for profile updates)
   */
  async deletePhoto(photoUrl: string, userId: string): Promise<boolean> {
    try {
      // Extract file path from URL
      const url = new URL(photoUrl);
      const pathParts = url.pathname.split('/');
      const filePath = pathParts.slice(-2).join('/'); // userId/filename

      // Verify user owns this photo
      if (!filePath.startsWith(userId + '/')) {
        console.error('Unauthorized photo deletion attempt');
        return false;
      }

      const { error } = await this.supabase.storage
        .from(BUCKET_NAME)
        .remove([filePath]);

      if (error) {
        console.error('Photo deletion error:', error);
        return false;
      }

      return true;
    } catch (error) {
      console.error('Photo deletion error:', error);
      return false;
    }
  }

  /**
   * Create signed upload URL (alternative approach for direct uploads)
   */
  async createSignedUploadUrl(
    userId: string,
    fileName: string,
    fileSize: number,
    mimeType: string
  ): Promise<{ uploadUrl?: string; finalUrl?: string; error?: string }> {
    try {
      // Validate parameters
      if (fileSize > MAX_FILE_SIZE) {
        return {
          error: `File too large. Maximum size is ${MAX_FILE_SIZE / (1024 * 1024)}MB`
        };
      }

      if (!ALLOWED_MIME_TYPES.includes(mimeType)) {
        return {
          error: `Invalid file type. Allowed types: ${ALLOWED_MIME_TYPES.join(', ')}`
        };
      }

      const filePath = this.generateFilePath(userId, fileName);

      // Create signed upload URL
      const { data, error } = await this.supabase.storage
        .from(BUCKET_NAME)
        .createSignedUploadUrl(filePath);

      if (error) {
        return {
          error: `Failed to create upload URL: ${error.message}`
        };
      }

      // Get the final public URL
      const { data: urlData } = this.supabase.storage
        .from(BUCKET_NAME)
        .getPublicUrl(filePath);

      return {
        uploadUrl: data.signedUrl,
        finalUrl: urlData.publicUrl
      };

    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Failed to create upload URL'
      };
    }
  }

  /**
   * Upload using signed URL (for better performance on large files)
   */
  async uploadWithSignedUrl(
    file: File,
    signedUrl: string,
    onProgress?: (progress: PhotoUploadProgress) => void
  ): Promise<PhotoUploadResult> {
    try {
      onProgress?.({ progress: 10, stage: 'validating' });

      // Validate file
      const validation = await this.validatePhotoFileAsync(file);
      if (!validation.valid) {
        return {
          success: false,
          error: validation.error
        };
      }

      onProgress?.({ progress: 30, stage: 'uploading' });

      // Upload to signed URL
      const response = await fetch(signedUrl, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type,
        },
      });

      if (!response.ok) {
        return {
          success: false,
          error: `Upload failed with status: ${response.status}`
        };
      }

      onProgress?.({ progress: 100, stage: 'complete' });

      return {
        success: true,
        photoUrl: signedUrl.split('?')[0] // Remove query params to get clean URL
      };

    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Upload failed'
      };
    }
  }

  /**
   * Compress image before upload (optional optimization)
   */
  async compressImage(file: File, maxWidth: number = 800, quality: number = 0.8): Promise<File> {
    return new Promise((resolve) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d')!;
      const img = new Image();

      img.onload = () => {
        // Calculate new dimensions maintaining aspect ratio
        const { width, height } = img;
        const aspectRatio = width / height;
        
        canvas.width = Math.min(width, maxWidth);
        canvas.height = canvas.width / aspectRatio;

        // Draw and compress
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        
        canvas.toBlob(
          (blob) => {
            if (blob) {
              const compressedFile = new File([blob], file.name, {
                type: file.type,
                lastModified: Date.now()
              });
              resolve(compressedFile);
            } else {
              resolve(file); // Return original if compression fails
            }
          },
          file.type,
          quality
        );
      };

      img.onerror = () => resolve(file); // Return original if processing fails
      img.src = URL.createObjectURL(file);
    });
  }
}

// Export singleton instance
export const photoUploadService = new PhotoUploadService();

// Utility functions for direct use
export async function uploadProfilePhoto(
  file: File,
  userId: string,
  onProgress?: (progress: PhotoUploadProgress) => void
): Promise<PhotoUploadResult> {
  return photoUploadService.uploadPhoto(file, userId, onProgress);
}

export function validatePhotoFile(file: File): { valid: boolean; error?: string } {
  return photoUploadService.validatePhotoFile(file);
}

export async function createPhotoUploadUrl(
  userId: string,
  fileName: string,
  fileSize: number,
  mimeType: string
): Promise<{ uploadUrl?: string; finalUrl?: string; error?: string }> {
  return photoUploadService.createSignedUploadUrl(userId, fileName, fileSize, mimeType);
}