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
import { Plus, Save, Loader2, Settings } from 'lucide-react';
import { AgentNode, type ExecutionState } from '@/components/agent-node';
import { AgentConfigDialog } from '@/components/agent-config-dialog';
import { WorkflowSettingsSidebar } from '@/components/workflow-builder/workflow-settings-sidebar';
import { RunControls } from '@/components/workflow-editor/run-controls';
import { ExecutionPanel, type LogEntry } from '@/components/workflow-editor/execution-panel';
import { useAuth } from '@/lib/auth-context';
import { useWorkflow } from '@/hooks/use-workflows';
import { runWorkflowStream, type StreamEvent } from '@/lib/api-stream';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

const nodeTypes = {
  agent: AgentNode,
};

interface UnifiedWorkflowEditorProps {
  workflowId: string;
  userId: string;
}

function UnifiedWorkflowEditorInner({ workflowId, userId }: UnifiedWorkflowEditorProps) {
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
  const containerRef = useRef<HTMLDivElement>(null);
  const nameInitializedRef = useRef(false);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Execution state
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [nodeExecutionStates, setNodeExecutionStates] = useState<Map<string, ExecutionState>>(new Map());

  // Update workflow name only on initial load
  useEffect(() => {
    if (workflowData?.name && !nameInitializedRef.current) {
      setWorkflowName(workflowData.name);
      nameInitializedRef.current = true;
    }
  }, [workflowData?.name]);

  const onConnect = useCallback(
    (params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeDoubleClick = useCallback((_event: React.MouseEvent, node: Node) => {
    if (!isRunning) {
      setEditingNodeId(node.id);
      setConfigDialogOpen(true);
    }
  }, [isRunning]);

  // Delete selected nodes
  const deleteSelectedNodes = useCallback(() => {
    if (isRunning) return;
    const selectedNodes = nodes.filter((n) => n.selected);
    if (selectedNodes.length > 0) {
      const selectedIds = new Set(selectedNodes.map((n) => n.id));
      setNodes((nds) => nds.filter((n) => !selectedIds.has(n.id)));
      setEdges((eds) =>
        eds.filter((e) => !selectedIds.has(e.source) && !selectedIds.has(e.target))
      );
    }
  }, [nodes, setNodes, setEdges, isRunning]);

  // Delete a specific node by ID
  const deleteNode = useCallback((nodeId: string) => {
    if (isRunning) return;
    setNodes((nds) => nds.filter((n) => n.id !== nodeId));
    setEdges((eds) =>
      eds.filter((e) => e.source !== nodeId && e.target !== nodeId)
    );
  }, [setNodes, setEdges, isRunning]);

  // Edit a specific node by ID
  const editNode = useCallback((nodeId: string) => {
    if (isRunning) return;
    setEditingNodeId(nodeId);
    setConfigDialogOpen(true);
  }, [isRunning]);

  // Update node data with execution state
  const updateNodesWithExecutionState = useCallback(() => {
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: {
          ...node.data,
          executionState: nodeExecutionStates.get(node.id) || 'idle',
          isEditable: !isRunning,
          onDelete: deleteNode,
          onEdit: editNode,
        },
      }))
    );
  }, [nodeExecutionStates, isRunning, setNodes, deleteNode, editNode]);

  useEffect(() => {
    updateNodesWithExecutionState();
  }, [nodeExecutionStates, isRunning]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      if ((e.key === 'Delete' || e.key === 'Backspace') && !isRunning) {
        e.preventDefault();
        deleteSelectedNodes();
      }

      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (!isRunning) saveWorkflow();
      }

      if (e.key === 'Escape') {
        setNodes((nds) => nds.map((n) => ({ ...n, selected: false })));
        setConfigDialogOpen(false);
        setEditingNodeId(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [deleteSelectedNodes, setNodes, isRunning]);

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
            executionState: 'idle' as ExecutionState,
            isEditable: true,
            onDelete: deleteNode,
            onEdit: editNode,
          },
        })) || [];

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
      } finally {
        setLoading(false);
      }
    };

    loadWorkflow();
  }, [workflowId, session?.access_token, apiUrl, setNodes, setEdges, deleteNode, editNode]);

  const addNewAgent = useCallback(() => {
    if (isRunning) return;
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
        executionState: 'idle' as ExecutionState,
        isEditable: true,
        onDelete: deleteNode,
        onEdit: editNode,
      },
    };
    setNodes((nds) => [...nds, newNode]);
    setEditingNodeId(newNode.id);
    setConfigDialogOpen(true);
  }, [nodes.length, setNodes, deleteNode, editNode, isRunning]);

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
          ? {
              ...node,
              data: {
                ...config,
                executionState: 'idle' as ExecutionState,
                isEditable: !isRunning,
                onDelete: deleteNode,
                onEdit: editNode,
              },
            }
          : node
      )
    );
    setEditingNodeId(null);
  }, [editingNodeId, setNodes, deleteNode, editNode, isRunning]);

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
    if (!session?.access_token || isRunning) return;

    setSaving(true);

    try {
      const existingAgents = await fetch(
        `${apiUrl}/api/workflows/${workflowId}`,
        {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
          },
        }
      ).then(res => res.json());

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

      const agentIdMap = new Map<string, string>();

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

      for (const edge of edges) {
        const fromAgentId = agentIdMap.get(edge.source);
        const toAgentId = agentIdMap.get(edge.target);

        if (!fromAgentId || !toAgentId) continue;

        await fetch(`${apiUrl}/api/connections`, {
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
      }

      addLog('Workflow saved successfully', 'success');
    } catch (error) {
      console.error('Save workflow error:', error);
      addLog(`Error saving workflow: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    } finally {
      setSaving(false);
    }
  };

  // Execution logic
  const addLog = (message: string, type: LogEntry['type'] = 'info', agentName?: string) => {
    setLogs((prev) => [...prev, { timestamp: new Date(), message, type, agentName }]);
  };

  const handleRun = async (input: string, dryRun: boolean) => {
    if (!session?.access_token) {
      addLog('Not authenticated. Please sign in.', 'error');
      return;
    }

    setIsRunning(true);
    setLogs([]);
    setNodeExecutionStates(new Map());

    addLog(`Starting ${dryRun ? 'dry run' : 'workflow'} for topic: "${input}"...`, dryRun ? 'dry-run' : 'info');

    try {
      const streamUrl = `${apiUrl}/api/run/stream`;

      await runWorkflowStream({
        workflow_id: workflowId,
        user_id: userId,
        input,
        streamUrl,
        accessToken: session.access_token,
        dry_run: dryRun,
        onEvent: (event: StreamEvent) => {
          if (event.type === 'node_active') {
            setNodeExecutionStates((prev) => {
              const next = new Map(prev);
              next.set(event.node_id, 'active');
              return next;
            });
            addLog('Started processing...', event.dry_run ? 'dry-run' : 'info', event.agent_name);
          } else if (event.type === 'node_complete') {
            setNodeExecutionStates((prev) => {
              const next = new Map(prev);
              next.set(event.node_id, 'completed');
              return next;
            });
            const outputPreview = event.output.length > 150 ? event.output.substring(0, 150) + '...' : event.output;
            addLog(`Output: ${outputPreview}`, event.dry_run ? 'dry-run' : 'success');
          } else if (event.type === 'workflow_complete') {
            addLog(`Workflow completed!`, event.dry_run ? 'dry-run' : 'success');
            addLog(event.final_output, event.dry_run ? 'dry-run' : 'info');
          } else if (event.type === 'error') {
            addLog(event.content, 'error');
          }
        },
      });
    } catch (e) {
      addLog(`Connection error: ${e instanceof Error ? e.message : 'Unknown error'}`, 'error');
    } finally {
      setIsRunning(false);
    }
  };

  const clearLogs = () => {
    setLogs([]);
    setNodeExecutionStates(new Map());
  };

  if (loading) {
    return (
      <div className="h-full w-full flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <p className="ml-2 text-muted-foreground font-mono">Loading workflow...</p>
      </div>
    );
  }

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
              className="text-lg font-semibold h-8 max-w-[300px] font-mono"
              autoFocus
            />
          ) : (
            <h2
              className={cn(
                'text-lg font-semibold truncate font-mono',
                !isRunning && 'cursor-pointer hover:text-primary transition-colors'
              )}
              onClick={() => !isRunning && setIsEditingName(true)}
              title={!isRunning ? 'Click to edit name' : undefined}
            >
              {workflowName || 'Untitled Workflow'}
            </h2>
          )}
          {isRunning && (
            <span className="text-xs font-mono text-yellow-500 flex items-center gap-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              RUNNING
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button onClick={addNewAgent} size="sm" variant="outline" disabled={saving || isRunning}>
            <Plus className="h-4 w-4 mr-1" /> Add Agent
          </Button>
          <Button onClick={saveWorkflow} size="sm" disabled={saving || isRunning}>
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
          <Button variant="ghost" size="icon" onClick={() => setSettingsOpen(true)} disabled={isRunning}>
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
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
            nodesDraggable={!isRunning}
            nodesConnectable={!isRunning}
            elementsSelectable={!isRunning}
            fitView
            deleteKeyCode={null}
          >
            <Controls />
            <MiniMap />
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
          </ReactFlow>
        </div>

        {/* Right Panel */}
        <div className="w-80 border-l flex flex-col bg-background">
          <Card className="m-3 p-4">
            <RunControls onRun={handleRun} isRunning={isRunning} disabled={nodes.length === 0} />
          </Card>

          <Card className="mx-3 mb-3 flex-1 flex flex-col overflow-hidden bg-black border-neutral-800">
            <ExecutionPanel logs={logs} onClear={clearLogs} />
          </Card>
        </div>
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

export function UnifiedWorkflowEditor(props: UnifiedWorkflowEditorProps) {
  return (
    <ReactFlowProvider>
      <UnifiedWorkflowEditorInner {...props} />
    </ReactFlowProvider>
  );
}
