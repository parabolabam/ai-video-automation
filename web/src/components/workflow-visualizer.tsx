'use client';

import { useCallback, useEffect, useState, useRef } from 'react';
import ReactFlow, { 
  Node, 
  Edge, 
  Background, 
  Controls, 
  useNodesState, 
  useEdgesState,
  MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';

import { runWorkflowStream, StreamEvent } from '@/lib/api-stream'; // Helper we will create
import { trpc } from '@/lib/trpc';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Play, Loader2, Terminal, CheckCircle2, Circle } from 'lucide-react';

interface WorkflowVisualizerProps {
  workflowId: string;
  userId: string;
}

export function WorkflowVisualizer({ workflowId, userId }: WorkflowVisualizerProps) {
  // Graph State
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  
  // Execution State
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);
  const [completedNodes, setCompletedNodes] = useState<Set<string>>(new Set());
  const [inputTopic, setInputTopic] = useState("");

  // Data Fetching
  const q = trpc.workflow.get.useQuery({ id: workflowId }, {
    refetchOnWindowFocus: false
  });

  // Log auto-scroll
  const logEndRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Build Graph on Load
  useEffect(() => {
    if (q.data) {
      const { agents, workflow_connections } = q.data;
      
      // Simple layout: position them linearly for now (or basic grid)
      // A real app would use dagre for auto-layout.
      const newNodes: Node[] = agents.map((agent: any, index: number) => ({
        id: agent.id,
        position: { x: 250, y: index * 150 + 50 },
        data: { label: agent.name },
        type: 'default', // Using default for now
        style: { 
          border: '1px solid #777', 
          padding: '10px', 
          borderRadius: '5px',
          width: 150,
          textAlign: 'center',
          background: '#1a1a1a',
          color: '#fff'
        }
      }));

      const newEdges: Edge[] = workflow_connections.map((conn: any) => ({
        id: conn.id,
        source: conn.from_agent_id,
        target: conn.to_agent_id,
        markerEnd: { type: MarkerType.ArrowClosed },
        animated: false,
        style: { stroke: '#555' }
      })).filter((e: any) => e.source && e.target); // Filter start nodes

      setNodes(newNodes);
      setEdges(newEdges);
    }
  }, [q.data, setNodes, setEdges]);

  // Update Node Styles based on Active State
  useEffect(() => {
    setNodes((nds) => 
      nds.map((node) => {
        const isActive = node.id === activeNodeId;
        const isCompleted = completedNodes.has(node.id);
        
        let style = { ...node.style };
        if (isActive) {
          style.border = '2px solid #22c55e'; // Green
          style.boxShadow = '0 0 10px #22c55e';
        } else if (isCompleted) {
          style.border = '2px solid #3b82f6'; // Blue
          style.boxShadow = 'none';
        } else {
          style.border = '1px solid #777';
          style.boxShadow = 'none';
        }

        return {
          ...node,
          style
        };
      })
    );
    
    // Animate edges connected to active node?
    setEdges((eds) =>
      eds.map((edge) => ({
        ...edge,
        animated: edge.source === activeNodeId,
        style: { ...edge.style, stroke: edge.source === activeNodeId ? '#22c55e' : '#555' }
      }))
    );

  }, [activeNodeId, completedNodes, setNodes, setEdges]);


  const handleRun = async () => {
    if (!inputTopic) return;
    setIsRunning(true);
    setLogs([]);
    setCompletedNodes(new Set());
    setActiveNodeId(null);

    setLogs(prev => [...prev, `Starting workflow for topic: "${inputTopic}"...`]);

    try {
      await runWorkflowStream({
        workflow_id: workflowId,
        user_id: userId,
        input: inputTopic,
        onEvent: (event: StreamEvent) => {
          if (event.type === 'node_active') {
            setActiveNodeId(event.node_id);
            setLogs(prev => [...prev, `[${event.agent_name}] Started thinking...`]);
          } else if (event.type === 'node_complete') {
            setActiveNodeId(null);
            setCompletedNodes(prev => new Set(prev).add(event.node_id));
            setLogs(prev => [...prev, `[Agent] Output: ${event.output.substring(0, 100)}...`]);
          } else if (event.type === 'workflow_complete') {
            setLogs(prev => [...prev, `Workflow Completed. Final Output: \n${event.final_output}`]);
          } else if (event.type === 'error') {
            setLogs(prev => [...prev, `ERROR: ${event.content}`]);
          }
        }
      });
    } catch (e: any) {
      setLogs(prev => [...prev, `Stream connection error: ${e.message}`]);
    } finally {
      setIsRunning(false);
      setActiveNodeId(null);
    }
  };

  if (q.isLoading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-150px)]">
      {/* Left: Graph */}
      <Card className="lg:col-span-2 relative border-neutral-800 bg-neutral-950/50 overflow-hidden">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
          className="bg-neutral-950"
        >
          <Background color="#333" gap={16} />
          <Controls />
        </ReactFlow>
        <div className="absolute top-4 right-4 flex items-center gap-2 bg-black/50 p-2 rounded-lg border border-neutral-800">
           <div className="flex items-center gap-1 text-xs text-neutral-400">
              <div className="w-2 h-2 rounded-full bg-green-500" /> Active
           </div>
           <div className="flex items-center gap-1 text-xs text-neutral-400">
              <div className="w-2 h-2 rounded-full bg-blue-500" /> Completed
           </div>
        </div>
      </Card>

      {/* Right: Controls & Logs */}
      <div className="flex flex-col gap-4 h-full">
        <Card className="p-4 space-y-4">
           <h3 className="font-semibold flex items-center gap-2">
             <Play className="w-4 h-4" /> Controls
           </h3>
           <div className="flex gap-2">
             <Input 
               placeholder="Enter topic..." 
               value={inputTopic}
               onChange={e => setInputTopic(e.target.value)}
               disabled={isRunning}
             />
             <Button onClick={handleRun} disabled={isRunning || !inputTopic}>
               {isRunning ? <Loader2 className="animate-spin w-4 h-4" /> : "Run"}
             </Button>
           </div>
        </Card>

        <Card className="flex-1 flex flex-col p-0 overflow-hidden bg-black border-neutral-800 font-mono text-sm">
           <div className="p-3 border-b border-neutral-800 bg-neutral-900/50 flex items-center gap-2 text-neutral-400">
              <Terminal className="w-4 h-4" /> Live Logs
           </div>
           <ScrollArea className="flex-1 p-4">
              <div className="space-y-1">
                {logs.map((log, i) => (
                  <div key={i} className="break-words text-neutral-300 border-b border-neutral-900 pb-1 mb-1 last:border-0">
                    <span className="opacity-50 mr-2 text-xs">
                        {new Date().toLocaleTimeString()}
                    </span>
                    {log}
                  </div>
                ))}
                <div ref={logEndRef} />
              </div>
           </ScrollArea>
        </Card>
      </div>
    </div>
  );
}
