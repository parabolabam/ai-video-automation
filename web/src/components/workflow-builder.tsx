'use client';

import { useCallback, useState, useEffect, useRef } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  useReactFlow,
  type Connection,
  type Edge,
  type Node,
  BackgroundVariant,
  ReactFlowProvider,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Plus, Save, Loader2, Play, Settings } from 'lucide-react';
import { AgentNode } from '@/components/agent-node';
import { AgentConfigDialog } from '@/components/agent-config-dialog';
import { WorkflowSettingsSidebar } from '@/components/workflow-builder/workflow-settings-sidebar';
import { useAuth } from '@/lib/auth-context';
import { useWorkflow } from '@/hooks/use-workflows';

const nodeTypes = {
  agent: AgentNode,
};

interface WorkflowBuilderProps {
  workflowId: string;
  userId: string;
}

function WorkflowBuilderInner({ workflowId }: WorkflowBuilderProps) {
  const { session } = useAuth();
  const { data: workflowData, refetch: refetchWorkflow } = useWorkflow(workflowId);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [editingNodeId, setEditingNodeId] = useState<string | null>(null);
  const [workflowName, setWorkflowName] = useState('');
  const [isEditingName, setIsEditingName] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const reactFlowInstance = useReactFlow();
  const containerRef = useRef<HTMLDivElement>(null);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Update workflow name when data loads
  useEffect(() => {
    if (workflowData?.name) {
      setWorkflowName(workflowData.name);
    }
  }, [workflowData?.name]);

  const onConnect = useCallback(
    (params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeDoubleClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setEditingNodeId(node.id);
    setConfigDialogOpen(true);
  }, []);

  // Delete selected nodes
  const deleteSelectedNodes = useCallback(() => {
    const selectedNodes = nodes.filter((n) => n.selected);
    if (selectedNodes.length > 0) {
      const selectedIds = new Set(selectedNodes.map((n) => n.id));
      setNodes((nds) => nds.filter((n) => !selectedIds.has(n.id)));
      setEdges((eds) =>
        eds.filter((e) => !selectedIds.has(e.source) && !selectedIds.has(e.target))
      );
    }
  }, [nodes, setNodes, setEdges]);

  // Delete a specific node by ID
  const deleteNode = useCallback((nodeId: string) => {
    setNodes((nds) => nds.filter((n) => n.id !== nodeId));
    setEdges((eds) =>
      eds.filter((e) => e.source !== nodeId && e.target !== nodeId)
    );
  }, [setNodes, setEdges]);

  // Edit a specific node by ID
  const editNode = useCallback((nodeId: string) => {
    setEditingNodeId(nodeId);
    setConfigDialogOpen(true);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      // Delete or Backspace - delete selected nodes
      if (e.key === 'Delete' || e.key === 'Backspace') {
        e.preventDefault();
        deleteSelectedNodes();
      }

      // Ctrl/Cmd + S - save workflow
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        saveWorkflow();
      }

      // Escape - deselect all
      if (e.key === 'Escape') {
        setNodes((nds) => nds.map((n) => ({ ...n, selected: false })));
        setConfigDialogOpen(false);
        setEditingNodeId(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [deleteSelectedNodes, setNodes]);

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
        const workflow = data.workflow;

        console.log('[WorkflowBuilder] Loaded workflow:', workflow);

        // Convert agents to nodes
        const loadedNodes: Node[] = workflow.agents?.map((agent: {
          id: string;
          name: string;
          role: string;
          model: string;
          system_instructions: string;
          tools: string[];
        }, index: number) => ({
          id: agent.id,
          type: 'agent',
          position: { x: 100 + (index % 3) * 300, y: 100 + Math.floor(index / 3) * 200 },
          data: {
            label: agent.name,
            role: agent.role,
            model: agent.model,
            systemInstructions: agent.system_instructions,
            tools: agent.tools || [],
            onDelete: deleteNode,
            onEdit: editNode,
          },
        })) || [];

        // Convert connections to edges
        const loadedEdges: Edge[] = workflow.workflow_connections?.map((conn: {
          id: string;
          from_agent_id: string;
          to_agent_id: string;
        }) => ({
          id: conn.id,
          source: conn.from_agent_id,
          target: conn.to_agent_id,
          type: 'default' as const,
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
  }, [workflowId, session?.access_token, apiUrl, setNodes, setEdges, deleteNode, editNode]);

  const addNewAgent = useCallback(() => {
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
        onDelete: deleteNode,
        onEdit: editNode,
      },
    };
    setNodes((nds) => [...nds, newNode]);
    // Immediately open config dialog for new agent
    setEditingNodeId(newNode.id);
    setConfigDialogOpen(true);
  }, [nodes.length, setNodes, deleteNode, editNode]);

  const handleSaveAgentConfig = useCallback((config: {
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
          ? { ...node, data: { ...config, onDelete: deleteNode, onEdit: editNode } }
          : node
      )
    );
    setEditingNodeId(null);
  }, [editingNodeId, setNodes, deleteNode, editNode]);

  const handleDeleteAgent = useCallback(() => {
    if (editingNodeId) {
      deleteNode(editingNodeId);
      setConfigDialogOpen(false);
      setEditingNodeId(null);
    }
  }, [editingNodeId, deleteNode]);

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
      if (existingAgents?.workflow?.agents) {
        await Promise.all(
          existingAgents.workflow.agents.map((agent: { id: string }) =>
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

  // Check if we're editing an existing node (not creating new)
  const isEditingExisting = editingNodeId ? nodes.some(n => n.id === editingNodeId && !n.id.startsWith('agent-')) : false;

  return (
    <div className="h-full w-full flex flex-col" ref={containerRef}>
      {/* Header */}
      <div className="border-b bg-background p-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-4 flex-1 min-w-0">
          {isEditingName ? (
            <Input
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              onBlur={() => setIsEditingName(false)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') setIsEditingName(false);
                if (e.key === 'Escape') {
                  setWorkflowName(workflowData?.name || '');
                  setIsEditingName(false);
                }
              }}
              className="text-lg font-semibold h-8 max-w-[300px]"
              autoFocus
            />
          ) : (
            <h2
              className="text-lg font-semibold truncate cursor-pointer hover:text-primary transition-colors"
              onClick={() => setIsEditingName(true)}
              title="Click to edit name"
            >
              {workflowName || 'Untitled Workflow'}
            </h2>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button onClick={addNewAgent} size="sm" variant="outline" disabled={saving}>
            <Plus className="h-4 w-4 mr-1" /> Add Agent
          </Button>
          <Button onClick={saveWorkflow} size="sm" disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 mr-1 animate-spin" /> Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-1" /> Save
              </>
            )}
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setSettingsOpen(true)}>
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeDoubleClick={onNodeDoubleClick}
          nodeTypes={nodeTypes}
          fitView
          deleteKeyCode={null} // We handle delete ourselves
        >
          <Controls />
          <MiniMap />
          <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        </ReactFlow>
      </div>

      <AgentConfigDialog
        open={configDialogOpen}
        onClose={() => {
          setConfigDialogOpen(false);
          setEditingNodeId(null);
        }}
        onSave={handleSaveAgentConfig}
        onDelete={handleDeleteAgent}
        initialConfig={getCurrentAgentConfig()}
        isEditing={!!editingNodeId}
      />

      <WorkflowSettingsSidebar
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        workflowId={workflowId}
        initialData={workflowData ? {
          name: workflowData.name,
          description: workflowData.description,
          active: workflowData.active,
        } : undefined}
        onSave={() => refetchWorkflow()}
      />
    </div>
  );
}

// Export wrapped component with ReactFlowProvider
export function WorkflowBuilder(props: WorkflowBuilderProps) {
  return (
    <ReactFlowProvider>
      <WorkflowBuilderInner {...props} />
    </ReactFlowProvider>
  );
}
