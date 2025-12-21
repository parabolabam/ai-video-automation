'use client';

import { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  Connection,
  addEdge,
  MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';
import { v4 as uuidv4 } from 'uuid';

import { trpc } from '@/lib/trpc';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle
} from './ui/sheet';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Loader2, Save, Plus } from 'lucide-react';

interface WorkflowEditorProps {
  workflowId: string;
}

export function WorkflowEditor({ workflowId }: WorkflowEditorProps) {
  // Graph State
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  
  // Selection / Editing State
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isSheetOpen, setIsSheetOpen] = useState(false);
  
  // Temporary state for the node being edited
  const [editForm, setEditForm] = useState({
    name: '',
    role: '',
    model: 'gpt-4o',
    system_instructions: '',
    tools: [] as string[]
  });

  const utils = trpc.useUtils();
  const { data: initialData, isLoading } = trpc.workflow.get.useQuery({ id: workflowId }, {
    refetchOnWindowFocus: false
  });
  
  const saveMutation = trpc.workflow.saveGraph.useMutation({
    onSuccess: () => {
      alert("Workflow Saved!"); // Simple alert for MVP
      utils.workflow.get.invalidate({ id: workflowId });
    },
    onError: (err) => {
      alert(`Error saving: ${err.message}`);
    }
  });

  // Load Initial Data
  useEffect(() => {
    if (initialData) {
      const { agents, workflow_connections } = initialData;

      const loadedNodes: Node[] = agents.map((agent: { id: string; name: string; role: string; model: string; system_instructions: string; tools: string[] }, index: number) => ({
        id: agent.id,
        position: { x: 250, y: index * 150 + 50 },
        data: { 
          label: agent.name,
          role: agent.role,
          model: agent.model,
          system_instructions: agent.system_instructions,
          tools: agent.tools || []
        },
        type: 'default',
        style: { 
          border: '1px solid #777', 
          padding: '10px', 
          borderRadius: '5px',
          width: 180,
          textAlign: 'center',
          background: '#1a1a1a',
          color: '#fff'
        }
      }));

      const loadedEdges: Edge[] = workflow_connections.map((conn: { id: string; from_agent_id: string; to_agent_id: string }) => ({
        id: conn.id,
        source: conn.from_agent_id,
        target: conn.to_agent_id,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { stroke: '#888' }
      })).filter((e: Edge) => e.source && e.target);

      setNodes(loadedNodes);
      setEdges(loadedEdges);
    }
  }, [initialData, setNodes, setEdges]);

  // Handlers
  const onConnect = useCallback((params: Connection) => {
    setEdges((eds) => addEdge({ ...params, markerEnd: { type: MarkerType.ArrowClosed } }, eds));
  }, [setEdges]);

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNodeId(node.id);
    setEditForm({
      name: node.data.label,
      role: node.data.role || 'Agent',
      model: node.data.model || 'gpt-4o',
      system_instructions: node.data.system_instructions || '',
      tools: node.data.tools || []
    });
    setIsSheetOpen(true);
  }, []);

  const addNewNode = () => {
    const newNodeId = uuidv4();
    const newNode: Node = {
      id: newNodeId,
      position: { x: 250, y: nodes.length * 100 + 50 },
      data: { 
        label: 'New Agent', 
        role: 'Assistant', 
        model: 'gpt-4o', 
        system_instructions: 'You are a helpful assistant.',
        tools: []
      },
      style: { 
        border: '1px solid #777', 
        padding: '10px', 
        borderRadius: '5px',
        width: 180,
        textAlign: 'center',
        background: '#1a1a1a',
        color: '#fff'
      }
    };
    setNodes((nds) => [...nds, newNode]);
    
    // Auto open edit
    setSelectedNodeId(newNodeId);
    setEditForm({ ...newNode.data, name: newNode.data.label });
    setIsSheetOpen(true);
  };

  const handleSaveGraph = () => {
    const agents = nodes.map(node => ({
        id: node.id,
        name: node.data.label,
        role: node.data.role,
        model: node.data.model,
        system_instructions: node.data.system_instructions,
        tools: node.data.tools
    }));

    const connections: { from_agent_id: string | null, to_agent_id: string }[] = edges.map(edge => ({
        from_agent_id: edge.source,
        to_agent_id: edge.target
    }));
    
    // Find start node(s) - nodes with no incoming edges? 
    // In our schema, start node connection has from_agent_id = NULL.
    // For now, let's assume the first node created (or top-most) is start 
    // AND add a explicit start connection for it IF it has no incoming edges.
    // Actually, the simpler way for MVP:
    // Any node that is a target of an edge is "connected".
    // Any node that is NOT a target of any edge is a "root".
    // We should create a NULL->Root connection for the first root found.
    
    const targets = new Set(edges.map(e => e.target));
    const roots = nodes.filter(n => !targets.has(n.id));
    
    if (roots.length > 0) {
        // Use the first root as entry point
        connections.push({
            from_agent_id: null,
            to_agent_id: roots[0].id
        });
    }

    saveMutation.mutate({
        workflowId,
        agents,
        connections
    });
  };

  const updateSelectedNode = () => {
    setNodes((nds) => nds.map(node => {
        if (node.id === selectedNodeId) {
            return {
                ...node,
                data: {
                    ...node.data,
                    label: editForm.name,
                    role: editForm.role,
                    model: editForm.model,
                    system_instructions: editForm.system_instructions,
                    tools: editForm.tools
                }
            };
        }
        return node;
    }));
    setIsSheetOpen(false);
  };

  const deleteSelectedNode = () => {
    if (!selectedNodeId) return;
    setNodes((nds) => nds.filter(n => n.id !== selectedNodeId));
    setEdges((eds) => eds.filter(e => e.source !== selectedNodeId && e.target !== selectedNodeId));
    setIsSheetOpen(false);
  };

  if (isLoading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>;

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col">
       {/* Toolbar */}
       <div className="h-12 border-b border-neutral-800 flex items-center justify-between px-4 bg-neutral-900/50">
          <div className="flex items-center gap-2">
             <Button variant="outline" size="sm" onClick={addNewNode}>
                <Plus className="w-4 h-4 mr-2" /> Add Agent
             </Button>
          </div>
          <div>
             <Button size="sm" onClick={handleSaveGraph} disabled={saveMutation.isLoading}>
                {saveMutation.isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                Save Changes
             </Button>
          </div>
       </div>

       {/* Editor */}
       <div className="flex-1 relative bg-neutral-950">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            fitView
          >
            <Background color="#333" gap={16} />
            <Controls />
          </ReactFlow>
       </div>

       {/* Edit Panel */}
       <Sheet open={isSheetOpen} onOpenChange={setIsSheetOpen}>
          <SheetContent className="overflow-y-auto">
             <SheetHeader>
               <SheetTitle>Edit Agent</SheetTitle>
               <SheetDescription>Configure the agent&apos;s behavior and tools.</SheetDescription>
             </SheetHeader>
             
             <div className="grid gap-4 py-4">
                <div className="space-y-2">
                   <Label>Name</Label>
                   <Input 
                     value={editForm.name} 
                     onChange={e => setEditForm(prev => ({ ...prev, name: e.target.value }))}
                   />
                </div>
                
                <div className="space-y-2">
                   <Label>Role</Label>
                   <Input 
                     value={editForm.role}
                     onChange={e => setEditForm(prev => ({ ...prev, role: e.target.value }))}
                   />
                </div>

                <div className="space-y-2">
                   <Label>Model</Label>
                   <Select 
                     value={editForm.model} 
                     onValueChange={val => setEditForm(prev => ({ ...prev, model: val }))}
                   >
                     <SelectTrigger><SelectValue /></SelectTrigger>
                     <SelectContent>
                       <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                       <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                       <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                     </SelectContent>
                   </Select>
                </div>

                <div className="space-y-2">
                   <Label>System Instructions</Label>
                   <Textarea 
                     className="min-h-[200px] font-mono text-sm"
                     value={editForm.system_instructions}
                     onChange={e => setEditForm(prev => ({ ...prev, system_instructions: e.target.value }))}
                   />
                </div>
                
                <div className="pt-4 flex justify-between">
                   <Button variant="destructive" size="sm" onClick={deleteSelectedNode}>Delete</Button>
                   <Button onClick={updateSelectedNode}>Apply</Button>
                </div>
             </div>
          </SheetContent>
       </Sheet>
    </div>
  );
}
