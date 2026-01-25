const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchWithAuth<T = unknown>(
  endpoint: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

// Types
export interface Workflow {
  id: string;
  name: string;
  description: string | null;
  active: boolean;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface Agent {
  id: string;
  name: string;
  role: string;
  model: string;
  system_instructions: string;
  tools: string[];
}

export interface WorkflowConnection {
  id: string;
  from_agent_id: string | null;
  to_agent_id: string;
}

export interface WorkflowDetail extends Workflow {
  agents: Agent[];
  workflow_connections: WorkflowConnection[];
}

export interface CreateWorkflowInput {
  name: string;
  description?: string;
}

export interface SaveGraphInput {
  workflowId: string;
  agents: Array<{
    id: string;
    name: string;
    role: string;
    model: string;
    system_instructions: string;
    tools: string[];
  }>;
  connections: Array<{
    from_agent_id: string | null;
    to_agent_id: string;
  }>;
}

// Response wrapper types from Python backend
interface ListWorkflowsResponse {
  status: string;
  workflows: Workflow[];
}

interface GetWorkflowResponse {
  status: string;
  workflow: WorkflowDetail;
}

interface CreateWorkflowResponse {
  status: string;
  message: string;
  workflow: Workflow;
}

interface DeleteWorkflowResponse {
  status: string;
  message: string;
}

interface SaveGraphResponse {
  status: string;
  message: string;
}

// API functions
export const workflowApi = {
  list: async (token: string, userId?: string): Promise<Workflow[]> => {
    const response = await fetchWithAuth<ListWorkflowsResponse>(
      userId ? `/api/workflows?user_id=${userId}` : '/api/workflows',
      token
    );
    return response.workflows;
  },

  get: async (id: string, token: string): Promise<WorkflowDetail> => {
    const response = await fetchWithAuth<GetWorkflowResponse>(`/api/workflows/${id}`, token);
    return response.workflow;
  },

  create: async (data: CreateWorkflowInput, token: string): Promise<Workflow> => {
    const response = await fetchWithAuth<CreateWorkflowResponse>('/api/workflows', token, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.workflow;
  },

  delete: async (id: string, token: string): Promise<{ success: boolean }> => {
    await fetchWithAuth<DeleteWorkflowResponse>(`/api/workflows/${id}`, token, {
      method: 'DELETE',
    });
    return { success: true };
  },

  saveGraph: async (data: SaveGraphInput, token: string): Promise<{ success: boolean }> => {
    await fetchWithAuth<SaveGraphResponse>(`/api/workflows/${data.workflowId}/graph`, token, {
      method: 'PUT',
      body: JSON.stringify({
        agents: data.agents,
        connections: data.connections,
      }),
    });
    return { success: true };
  },
};
