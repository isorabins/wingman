// Example: Progressive Project Data Loading
// This shows how the frontend can handle the new caching system

const ProjectOverview = ({ userId }) => {
  const [projectData, setProjectData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('initial');

  useEffect(() => {
    loadProjectData();
  }, [userId]);

  const loadProjectData = async () => {
    try {
      setLoading(true);
      
      // 1. Make initial request - this either returns cached data or triggers background loading
      const response = await fetch(`/api/project-overview/${userId}`);
      const result = await response.json();
      
      if (result.status === 'cached') {
        // ✅ We got cached data immediately - chat UI stays responsive!
        setProjectData(result.data);
        setStatus('loaded');
        setLoading(false);
        console.log(`Using cached data (${result.cache_age_minutes} minutes old)`);
        
      } else if (result.status === 'loading') {
        // ⏳ Background loading started - show minimal data and poll for completion
        setProjectData(result.data); // This has basic project info
        setStatus('loading');
        
        // Poll for completion (non-blocking)
        pollForCompletion();
      }
      
    } catch (error) {
      console.error('Error loading project data:', error);
      setLoading(false);
      setStatus('error');
    }
  };

  const pollForCompletion = async () => {
    const pollInterval = setInterval(async () => {
      try {
        const statusResponse = await fetch(`/api/project-data-status/${userId}`);
        const statusResult = await statusResponse.json();
        
        if (statusResult.ready) {
          // ✅ Full data is now ready!
          setProjectData(statusResult.data);
          setStatus('loaded');
          setLoading(false);
          clearInterval(pollInterval);
          console.log('Full project data loaded in background');
        }
        
      } catch (error) {
        console.error('Error polling for project data:', error);
        clearInterval(pollInterval);
        setLoading(false);
        setStatus('error');
      }
    }, 2000); // Poll every 2 seconds

    // Stop polling after 30 seconds to avoid infinite polling
    setTimeout(() => {
      clearInterval(pollInterval);
      if (status === 'loading') {
        setLoading(false);
        setStatus('timeout');
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

  return (
    <div className="project-overview">
      {/* Chat UI can render immediately - not blocked! */}
      
      {status === 'loaded' && projectData && (
        <div className="project-details">
          <h2>{projectData.project?.project_name || 'Your Project'}</h2>
          <p>Type: {projectData.project?.project_type}</p>
          <p>Phase: {projectData.project?.current_phase}</p>
          
          {/* Rich data available when loaded */}
          {projectData.recent_updates && (
            <div className="recent-updates">
              <h3>Recent Updates</h3>
              {projectData.recent_updates.map((update, i) => (
                <div key={i}>{update.summary}</div>
              ))}
            </div>
          )}
          
          <button onClick={refreshCache}>Refresh Data</button>
        </div>
      )}
      
      {status === 'loading' && (
        <div className="loading-state">
          <h2>{projectData?.project?.project_name || 'Loading Project...'}</h2>
          <p>📊 Loading detailed project data in background...</p>
          <div className="spinner">⏳</div>
        </div>
      )}
      
      {status === 'initial' && loading && (
        <div className="initial-loading">
          <p>🚀 Checking for project data...</p>
        </div>
      )}
      
      {status === 'error' && (
        <div className="error-state">
          <p>❌ Error loading project data</p>
          <button onClick={loadProjectData}>Retry</button>
        </div>
      )}
    </div>
  );
};

// Usage in main app:
const App = () => {
  return (
    <div className="app">
      {/* Chat loads immediately - never blocked */}
      <ChatInterface userId={userId} />
      
      {/* Project overview loads progressively */}
      <ProjectOverview userId={userId} />
    </div>
  );
}; 