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
import { Plus, Save } from 'lucide-react';
import { AgentNode } from '@/components/agent-node';
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
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [saving, setSaving] = useState(false);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const onConnect = useCallback(
    (params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

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
  };

  const saveWorkflow = async () => {
    if (!session?.access_token) {
      alert('Not authenticated');
      return;
    }

    setSaving(true);
    alert('Workflow builder is under construction. Backend API endpoints for agents and connections will be added next.');
    setSaving(false);
  };

  return (
    <div className="h-full w-full relative">
      <div className="absolute top-4 left-4 z-10 flex gap-2">
        <Button onClick={addNewAgent} size="sm">
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
        nodeTypes={nodeTypes}
        fitView
      >
        <Controls />
        <MiniMap />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
      </ReactFlow>
    </div>
  );
}
