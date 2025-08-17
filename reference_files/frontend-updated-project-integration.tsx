// Updated Frontend Integration for New Caching System
// Replace your existing project overview fetching logic with this

import React, { useState, useEffect } from 'react';

// Goal and Challenge interfaces to match backend schema
interface Goal {
  title: string;
  description: string;
}

interface Challenge {
  title: string;
  description: string;
}

// Updated TypeScript interfaces
interface ProjectOverviewResponse {
  status: 'cached' | 'loading' | 'error';
  data?: {
    profile?: any;
    project?: {
      project_name: string;
      project_type: string;
      current_phase: string;
      goals: Goal[];  // CORRECTED: Now properly typed as objects with title/description
      challenges: Challenge[];  // CORRECTED: Now properly typed as objects with title/description
      description: string;
      // ... other project fields
    };
    recent_updates?: any[];
    recent_activity?: any[];
    loaded_at?: string;
  };
  message?: string;
  cache_age_minutes?: number;
}

interface ProjectStatusResponse {
  ready: boolean;
  data?: any;
  message?: string;
  cache_age_minutes?: number;
}

// Updated React Hook
export const useProjectOverview = (userId: string) => {
  const [projectData, setProjectData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<'initial' | 'loading' | 'cached' | 'error'>('initial');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (userId) {
      loadProjectData();
    }
  }, [userId]);

  const loadProjectData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // 1. Make initial request
      const response = await fetch(`/api/project-overview/${userId}`);
      const result: ProjectOverviewResponse = await response.json();
      
      if (result.status === 'cached') {
        // ✅ Got cached data immediately
        setProjectData(result.data);
        setStatus('cached');
        setLoading(false);
        console.log(`Using cached data (${result.cache_age_minutes} minutes old)`);
        
      } else if (result.status === 'loading') {
        // ⏳ Background loading started - show minimal data
        setProjectData(result.data); // Has basic project info
        setStatus('loading');
        
        // Poll for completion (non-blocking)
        pollForCompletion();
        
      } else if (result.status === 'error') {
        setError(result.message || 'Failed to load project data');
        setStatus('error');
        setLoading(false);
      }
      
    } catch (err) {
      console.error('Error loading project data:', err);
      setError('Network error loading project data');
      setStatus('error');
      setLoading(false);
    }
  };

  const pollForCompletion = async () => {
    const pollInterval = setInterval(async () => {
      try {
        const statusResponse = await fetch(`/api/project-data-status/${userId}`);
        const statusResult: ProjectStatusResponse = await statusResponse.json();
        
        if (statusResult.ready && statusResult.data) {
          // ✅ Full data is now ready!
          setProjectData(statusResult.data);
          setStatus('cached');
          setLoading(false);
          clearInterval(pollInterval);
          console.log('Full project data loaded in background');
        }
        
      } catch (error) {
        console.error('Error polling for project data:', error);
        clearInterval(pollInterval);
        setLoading(false);
        setStatus('error');
        setError('Failed to load complete project data');
      }
    }, 2000); // Poll every 2 seconds

    // Stop polling after 30 seconds
    setTimeout(() => {
      clearInterval(pollInterval);
      if (status === 'loading') {
        setLoading(false);
        setStatus('error');
        setError('Project data loading timeout');
      }
    }, 30000);
  };

  const refreshCache = async () => {
    try {
      await fetch(`/api/refresh-project-cache/${userId}`, { method: 'POST' });
      // Reload data after refresh
      setTimeout(() => loadProjectData(), 1000);
    } catch (error) {
      console.error('Error refreshing cache:', error);
    }
  };

  return {
    projectData,
    loading,
    status,
    error,
    refreshCache,
    reload: loadProjectData
  };
};

// Updated React Component
export const ProjectOverview: React.FC<{ userId: string }> = ({ userId }) => {
  const { projectData, loading, status, error, refreshCache } = useProjectOverview(userId);

  // Handle different loading states
  if (status === 'initial' && loading) {
    return <div className="loading">🚀 Checking for project data...</div>;
  }

  if (status === 'error') {
    return (
      <div className="error">
        <p>❌ Error: {error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  if (status === 'loading') {
    return (
      <div className="loading-with-partial-data">
        {projectData?.project ? (
          <div>
            <h2>{projectData.project.project_name}</h2>
            <p>Type: {projectData.project.project_type}</p>
            <p>📊 Loading detailed project data in background...</p>
            <div className="spinner">⏳</div>
          </div>
        ) : (
          <div>
            <p>📊 Loading project data...</p>
            <div className="spinner">⏳</div>
          </div>
        )}
      </div>
    );
  }

  // status === 'cached' - Full data available
  if (!projectData?.project) {
    return <div>No project data available</div>;
  }

  const project = projectData.project;

  return (
    <div className="project-overview">
      <div className="project-header">
        <h1>{project.project_name}</h1>
        <p className="project-type">{project.project_type}</p>
        <p className="current-phase">Phase: {project.current_phase}</p>
        
        {/* Cache status indicator */}
        <div className="cache-status">
          ✅ Data loaded {projectData.loaded_at ? 
            `at ${new Date(projectData.loaded_at).toLocaleTimeString()}` : 
            'from cache'
          }
          <button onClick={refreshCache} className="refresh-btn">
            🔄 Refresh
          </button>
        </div>
      </div>

      <div className="project-content">
        <section className="goals">
          <h3>Goals</h3>
          <ul>
            {project.goals?.map((goal: Goal, index: number) => (
              <li key={index}>
                <strong>{goal.title}</strong>: {goal.description}
              </li>
            ))}
          </ul>
        </section>

        <section className="challenges">
          <h3>Challenges</h3>
          <ul>
            {project.challenges?.map((challenge: Challenge, index: number) => (
              <li key={index}>
                <strong>{challenge.title}</strong>: {challenge.description}
              </li>
            ))}
          </ul>
        </section>

        {/* New: Recent updates from cache */}
        {projectData.recent_updates && projectData.recent_updates.length > 0 && (
          <section className="recent-updates">
            <h3>Recent Updates</h3>
            {projectData.recent_updates.map((update: any, index: number) => (
              <div key={index} className="update-item">
                <p>{update.progress_summary}</p>
                <small>{new Date(update.created_at).toLocaleDateString()}</small>
              </div>
            ))}
          </section>
        )}
      </div>
    </div>
  );
};

// Example: Update existing API calls
export const updateExistingApiCall = async (userId: string) => {
  // OLD WAY (still works but change to new pattern):
  // const project = await fetch(`/api/project-overview/${userId}`).then(r => r.json());
  
  // NEW WAY (handles caching):
  const response = await fetch(`/api/project-overview/${userId}`);
  const result: ProjectOverviewResponse = await response.json();
  
  if (result.status === 'cached') {
    // Use result.data.project instead of result directly
    const project = result.data?.project;
    return project;
  } else if (result.status === 'loading') {
    // Handle loading state - maybe show spinner and poll
    console.log('Project data loading in background...');
    return result.data?.project; // Partial data available
  } else {
    throw new Error(result.message || 'Failed to load project');
  }
};

export default ProjectOverview; 