"use client"

import { useState, useCallback, useRef } from 'react'

export interface OptimisticUpdateOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error, rollbackData: T) => void;
  onRollback?: (data: T) => void;
  timeout?: number; // Timeout for API call
}

export const useOptimisticUpdate = <T>(
  initialData: T,
  apiCall: (data: T) => Promise<T>,
  options: OptimisticUpdateOptions<T> = {}
) => {
  const [data, setData] = useState<T>(initialData);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const originalDataRef = useRef<T>(initialData);
  const timeoutRef = useRef<NodeJS.Timeout>();

  const updateOptimistically = useCallback(async (optimisticUpdate: Partial<T>) => {
    // Store the current data for potential rollback
    originalDataRef.current = data;
    
    // Apply optimistic update immediately
    const newData = { ...data, ...optimisticUpdate } as T;
    setData(newData);
    setIsLoading(true);
    setError(null);

    // Set timeout if specified
    if (options.timeout) {
      timeoutRef.current = setTimeout(() => {
        setIsLoading(false);
        setError(new Error('Request timeout'));
        // Rollback on timeout
        setData(originalDataRef.current);
        options.onRollback?.(originalDataRef.current);
      }, options.timeout);
    }

    try {
      // Confirm with API
      const confirmedData = await apiCall(newData);
      
      // Clear timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      setData(confirmedData);
      options.onSuccess?.(confirmedData);
      
      if (process.env.NODE_ENV === 'development') {
        console.log('✅ Optimistic update confirmed', confirmedData);
      }
      
      return confirmedData;
    } catch (error) {
      // Clear timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      const errorObj = error instanceof Error ? error : new Error('Unknown error');
      
      // Rollback on error
      setData(originalDataRef.current);
      setError(errorObj);
      options.onError?.(errorObj, originalDataRef.current);
      options.onRollback?.(originalDataRef.current);
      
      if (process.env.NODE_ENV === 'development') {
        console.error('❌ Optimistic update failed, rolling back', errorObj);
      }
      
      throw errorObj;
    } finally {
      setIsLoading(false);
    }
  }, [data, apiCall, options]);

  const reset = useCallback(() => {
    setData(initialData);
    setError(null);
    setIsLoading(false);
    originalDataRef.current = initialData;
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  }, [initialData]);

  const rollback = useCallback(() => {
    setData(originalDataRef.current);
    setError(null);
    setIsLoading(false);
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    options.onRollback?.(originalDataRef.current);
  }, [options]);

  return { 
    data, 
    updateOptimistically, 
    isLoading, 
    error,
    reset,
    rollback,
    hasChanges: JSON.stringify(data) !== JSON.stringify(originalDataRef.current)
  };
};

// Specialized hook for form updates
export const useOptimisticForm = <T extends Record<string, any>>(
  initialData: T,
  submitHandler: (data: T) => Promise<T>,
  options: OptimisticUpdateOptions<T> = {}
) => {
  const optimistic = useOptimisticUpdate(initialData, submitHandler, options);
  
  const updateField = useCallback((field: keyof T, value: any) => {
    const update = { [field]: value } as Partial<T>;
    optimistic.updateOptimistically(update);
  }, [optimistic]);

  const updateFields = useCallback((updates: Partial<T>) => {
    optimistic.updateOptimistically(updates);
  }, [optimistic]);

  return {
    ...optimistic,
    updateField,
    updateFields
  };
};

// Hook for optimistic list operations
export const useOptimisticList = <T extends { id: string }>(
  initialItems: T[],
  apiOperations: {
    add: (item: Omit<T, 'id'>) => Promise<T>;
    update: (item: T) => Promise<T>;
    delete: (id: string) => Promise<void>;
  },
  options: OptimisticUpdateOptions<T[]> = {}
) => {
  const [items, setItems] = useState<T[]>(initialItems);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const addOptimistically = useCallback(async (newItem: Omit<T, 'id'>) => {
    const optimisticItem = { ...newItem, id: `temp-${Date.now()}` } as T;
    const previousItems = items;
    
    setItems(prev => [...prev, optimisticItem]);
    setIsLoading(true);
    setError(null);

    try {
      const confirmedItem = await apiOperations.add(newItem);
      setItems(prev => prev.map(item => 
        item.id === optimisticItem.id ? confirmedItem : item
      ));
      return confirmedItem;
    } catch (error) {
      setItems(previousItems);
      const errorObj = error instanceof Error ? error : new Error('Failed to add item');
      setError(errorObj);
      throw errorObj;
    } finally {
      setIsLoading(false);
    }
  }, [items, apiOperations]);

  const updateOptimistically = useCallback(async (updatedItem: T) => {
    const previousItems = items;
    
    setItems(prev => prev.map(item => 
      item.id === updatedItem.id ? updatedItem : item
    ));
    setIsLoading(true);
    setError(null);

    try {
      const confirmedItem = await apiOperations.update(updatedItem);
      setItems(prev => prev.map(item => 
        item.id === confirmedItem.id ? confirmedItem : item
      ));
      return confirmedItem;
    } catch (error) {
      setItems(previousItems);
      const errorObj = error instanceof Error ? error : new Error('Failed to update item');
      setError(errorObj);
      throw errorObj;
    } finally {
      setIsLoading(false);
    }
  }, [items, apiOperations]);

  const deleteOptimistically = useCallback(async (id: string) => {
    const previousItems = items;
    
    setItems(prev => prev.filter(item => item.id !== id));
    setIsLoading(true);
    setError(null);

    try {
      await apiOperations.delete(id);
    } catch (error) {
      setItems(previousItems);
      const errorObj = error instanceof Error ? error : new Error('Failed to delete item');
      setError(errorObj);
      throw errorObj;
    } finally {
      setIsLoading(false);
    }
  }, [items, apiOperations]);

  return {
    items,
    addOptimistically,
    updateOptimistically,
    deleteOptimistically,
    isLoading,
    error,
    reset: () => setItems(initialItems)
  };
};