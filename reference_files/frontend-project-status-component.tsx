"use client"

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RefreshCw, CheckCircle, AlertCircle, Target } from "lucide-react";

// Types for our new project status API
interface CurrentTasks {
  next_steps: string[];
  blockers: string[];
  recent_wins: string[];
}

interface AIUnderstanding {
  knows_project: boolean;
  project_name: string;
  has_next_steps: boolean;
  current_phase: string;
  last_activity: string;
}

interface ProjectStatusData {
  ai_understanding: AIUnderstanding;
  current_tasks: CurrentTasks;
  project_summary: {
    name: string;
    type: string;
    phase: string;
    total_updates: number;
    last_update: string;
  };
  is_active: boolean;
}

interface ProjectStatusProps {
  userId: string;
}

export const ProjectStatusComponent: React.FC<ProjectStatusProps> = ({ userId }) => {
  const [statusData, setStatusData] = useState<ProjectStatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchProjectStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_API_URL}/project-status/${userId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.message || 'Failed to load project status');
      }
      
      setStatusData(data);
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Error fetching project status:', err);
      setError(err instanceof Error ? err.message : 'Failed to load project status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userId) {
      fetchProjectStatus();
    }
  }, [userId]);

  const handleRefresh = () => {
    fetchProjectStatus();
  };

  if (loading && !statusData) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Loading Project Status...
          </CardTitle>
        </CardHeader>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="text-red-600">Error Loading Project</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600 mb-4">{error}</p>
          <Button onClick={handleRefresh} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!statusData) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>No Project Data</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600">No project information available.</p>
        </CardContent>
      </Card>
    );
  }

  const { ai_understanding, current_tasks, project_summary, is_active } = statusData;

  return (
    <div className="w-full space-y-4">
      {/* Project Header */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">{project_summary.name || 'Your Project'}</CardTitle>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant={is_active ? "default" : "secondary"}>
                  {is_active ? "ACTIVE" : "INACTIVE"}
                </Badge>
                <Badge variant="outline">
                  {project_summary.phase || 'Unknown Phase'}
                </Badge>
              </div>
            </div>
            <Button 
              onClick={handleRefresh} 
              variant="ghost" 
              size="sm"
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* AI Understanding */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-gray-700">
            🤖 AI Understanding
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="space-y-1 text-sm">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-3 w-3 text-green-500" />
              <span>Knows your project: {ai_understanding.project_name}</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-3 w-3 text-green-500" />
              <span>Current phase: {ai_understanding.current_phase}</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-3 w-3 text-green-500" />
              <span>Has {current_tasks.next_steps.length} next steps ready</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Current Tasks */}
      <div className="grid gap-4">
        {/* Next Steps */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Target className="h-4 w-4 text-blue-500" />
              Next Steps ({current_tasks.next_steps.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {current_tasks.next_steps.length > 0 ? (
              <ul className="space-y-2">
                {current_tasks.next_steps.map((step, index) => (
                  <li key={index} className="text-sm flex items-start gap-2">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">No next steps defined</p>
            )}
          </CardContent>
        </Card>

        {/* Blockers */}
        {current_tasks.blockers.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-red-500" />
                Current Blockers ({current_tasks.blockers.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <ul className="space-y-2">
                {current_tasks.blockers.map((blocker, index) => (
                  <li key={index} className="text-sm flex items-start gap-2">
                    <span className="text-red-500 mt-1">⚠</span>
                    <span>{blocker}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Recent Wins */}
        {current_tasks.recent_wins.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                Recent Wins ({current_tasks.recent_wins.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <ul className="space-y-2">
                {current_tasks.recent_wins.map((win, index) => (
                  <li key={index} className="text-sm flex items-start gap-2">
                    <span className="text-green-500 mt-1">✓</span>
                    <span>{win}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Footer */}
      <div className="text-xs text-gray-500 text-center">
        Last updated: {lastRefresh.toLocaleTimeString()}
        {project_summary.total_updates > 0 && (
          <span> • {project_summary.total_updates} total updates</span>
        )}
      </div>
    </div>
  );
};

export default ProjectStatusComponent; 