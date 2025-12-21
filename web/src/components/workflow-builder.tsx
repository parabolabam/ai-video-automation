'use client';

import { useCallback, useState, useEffect } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  type Connection,
  type Edge,
  type Node,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Button } from '@/components/ui/button';
import { Plus, Save, Loader2 } from 'lucide-react';
import { AgentNode } from '@/components/agent-node';
import { AgentConfigDialog } from '@/components/agent-config-dialog';
import { useAuth } from '@/lib/auth-context';

const nodeTypes = {
  agent: AgentNode,
};

interface WorkflowBuilderProps {
  workflowId: string;
  userId: string;
}

export function WorkflowBuilder({ workflowId, userId }: WorkflowBuilderProps) {
  const { session } = useAuth();
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [editingNodeId, setEditingNodeId] = useState<string | null>(null);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const onConnect = useCallback(
    (params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeDoubleClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setEditingNodeId(node.id);
    setConfigDialogOpen(true);
  }, []);

  // Load workflow on mount
  useEffect(() => {
    const loadWorkflow = async () => {
      if (!session?.access_token) {
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`${apiUrl}/api/workflows/${workflowId}`, {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to load workflow');
        }

        const data = await response.json();

        // Convert agents to nodes
        const loadedNodes: Node[] = data.agents?.map((agent: any, index: number) => ({
          id: agent.id,
          type: 'agent',
          position: { x: 100 + (index % 3) * 300, y: 100 + Math.floor(index / 3) * 200 },
          data: {
            label: agent.name,
            role: agent.role,
            model: agent.model,
            systemInstructions: agent.system_instructions,
            tools: agent.tools || [],
          },
        })) || [];

        // Convert connections to edges
        const loadedEdges: Edge[] = data.workflow_connections?.map((conn: any) => ({
          id: conn.id,
          source: conn.from_agent_id,
          target: conn.to_agent_id,
          type: 'default',
        })).filter((e: Edge) => e.source && e.target) || [];

        setNodes(loadedNodes);
        setEdges(loadedEdges);
      } catch (error) {
        console.error('Load workflow error:', error);
        alert(`Error loading workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
      } finally {
        setLoading(false);
      }
    };

    loadWorkflow();
  }, [workflowId, session?.access_token, apiUrl, setNodes, setEdges]);

  const addNewAgent = () => {
    const timestamp = Date.now();
    const newNode: Node = {
      id: `agent-${timestamp}`,
      type: 'agent',
      position: { x: 100, y: 100 + nodes.length * 150 },
      data: {
        label: 'New Agent',
        role: 'Researcher',
        model: 'gpt-4o',
        systemInstructions: 'You are a helpful AI assistant.',
        tools: [],
      },
    };
    setNodes((nds) => [...nds, newNode]);
    // Immediately open config dialog for new agent
    setEditingNodeId(newNode.id);
    setConfigDialogOpen(true);
  };

  const handleSaveAgentConfig = (config: {
    label: string;
    role: string;
    model: string;
    systemInstructions: string;
    tools: string[];
  }) => {
    if (!editingNodeId) return;

    setNodes((nds) =>
      nds.map((node) =>
        node.id === editingNodeId
          ? { ...node, data: config }
          : node
      )
    );
    setEditingNodeId(null);
  };

  const getCurrentAgentConfig = (): {
    label: string;
    role: string;
    model: string;
    systemInstructions: string;
    tools: string[];
  } | undefined => {
    if (!editingNodeId) return undefined;
    const node = nodes.find((n) => n.id === editingNodeId);
    return node?.data as {
      label: string;
      role: string;
      model: string;
      systemInstructions: string;
      tools: string[];
    } | undefined;
  };

  const saveWorkflow = async () => {
    if (!session?.access_token) {
      alert('Not authenticated');
      return;
    }

    setSaving(true);

    try {
      // First, delete all existing agents and connections for this workflow
      // (We'll do a full replace for simplicity - could be optimized with diffing)
      const existingAgents = await fetch(
        `${apiUrl}/api/workflows/${workflowId}`,
        {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
          },
        }
      ).then(res => res.json());

      // Delete existing agents
      if (existingAgents?.agents) {
        await Promise.all(
          existingAgents.agents.map((agent: any) =>
            fetch(`${apiUrl}/api/agents/${agent.id}`, {
              method: 'DELETE',
              headers: {
                'Authorization': `Bearer ${session.access_token}`,
              },
            })
          )
        );
      }

      // Save all nodes as agents
      const agentIdMap = new Map<string, string>(); // client ID -> server ID

      for (const node of nodes) {
        const response = await fetch(`${apiUrl}/api/agents`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({
            workflow_id: workflowId,
            name: node.data.label,
            role: node.data.role || 'Researcher',
            model: node.data.model || 'gpt-4o',
            system_instructions: node.data.systemInstructions || 'You are a helpful AI assistant.',
            tools: node.data.tools || [],
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to save agent: ${node.data.label}`);
        }

        const result = await response.json();
        agentIdMap.set(node.id, result.agent.id);
      }

      // Save all edges as connections
      for (const edge of edges) {
        const fromAgentId = agentIdMap.get(edge.source);
        const toAgentId = agentIdMap.get(edge.target);

        if (!fromAgentId || !toAgentId) {
          console.warn(`Skipping edge ${edge.id} - missing agent mapping`);
          continue;
        }

        const response = await fetch(`${apiUrl}/api/connections`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({
            workflow_id: workflowId,
            from_agent_id: fromAgentId,
            to_agent_id: toAgentId,
            description: '',
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to save connection: ${edge.id}`);
        }
      }

      alert('Workflow saved successfully!');
    } catch (error) {
      console.error('Save workflow error:', error);
      alert(`Error saving workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="h-full w-full flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <p className="ml-2 text-muted-foreground">Loading workflow...</p>
      </div>
    );
  }

  return (
    <div className="h-full w-full relative">
      <div className="absolute top-4 left-4 z-10 flex gap-2">
        <Button onClick={addNewAgent} size="sm" disabled={saving}>
          <Plus className="mr-2 h-4 w-4" /> Add Agent
        </Button>
        <Button onClick={saveWorkflow} size="sm" disabled={saving}>
          <Save className="mr-2 h-4 w-4" /> {saving ? 'Saving...' : 'Save'}
        </Button>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeDoubleClick={onNodeDoubleClick}
        nodeTypes={nodeTypes}
        fitView
      >
        <Controls />
        <MiniMap />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
      </ReactFlow>

      <AgentConfigDialog
        open={configDialogOpen}
        onClose={() => {
          setConfigDialogOpen(false);
          setEditingNodeId(null);
        }}
        onSave={handleSaveAgentConfig}
        initialConfig={getCurrentAgentConfig()}
      />
    </div>
  );
}
