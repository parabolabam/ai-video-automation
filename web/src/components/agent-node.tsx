import { memo, useState } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Bot, Pencil, X, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

export type ExecutionState = 'idle' | 'active' | 'completed' | 'error';

interface AgentNodeData {
  label: string;
  role: string;
  model: string;
  tools?: string[];
  systemInstructions?: string;
  onDelete?: (nodeId: string) => void;
  onEdit?: (nodeId: string) => void;
  executionState?: ExecutionState;
  isEditable?: boolean;
}

export const AgentNode = memo(({ data, id, selected }: NodeProps) => {
  const nodeData = data as unknown as AgentNodeData;
  const [isHovered, setIsHovered] = useState(false);
  const executionState = nodeData.executionState || 'idle';
  const isEditable = nodeData.isEditable !== false;

  const getExecutionStyles = () => {
    switch (executionState) {
      case 'active':
        return 'ring-2 ring-green-500 shadow-[0_0_15px_rgba(34,197,94,0.5)] animate-pulse';
      case 'completed':
        return 'ring-2 ring-blue-500';
      case 'error':
        return 'ring-2 ring-red-500';
      default:
        return '';
    }
  };

  const getExecutionIcon = () => {
    switch (executionState) {
      case 'active':
        return <Loader2 className="h-3 w-3 animate-spin text-green-500" />;
      case 'completed':
        return <CheckCircle2 className="h-3 w-3 text-blue-500" />;
      case 'error':
        return <AlertCircle className="h-3 w-3 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div
      className="relative"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Hover/Selection action buttons - only show when editable and not running */}
      {isEditable && (isHovered || selected) && executionState === 'idle' && (
        <div className="absolute -top-2 -right-2 z-10 flex gap-1">
          {nodeData.onEdit && (
            <Button
              size="icon"
              variant="secondary"
              className="h-6 w-6 rounded-full shadow-md"
              onClick={(e) => {
                e.stopPropagation();
                nodeData.onEdit?.(id);
              }}
            >
              <Pencil className="h-3 w-3" />
            </Button>
          )}
          {nodeData.onDelete && (
            <Button
              size="icon"
              variant="destructive"
              className="h-6 w-6 rounded-full shadow-md"
              onClick={(e) => {
                e.stopPropagation();
                nodeData.onDelete?.(id);
              }}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
      )}

      <Card className={cn(
        "min-w-[250px] shadow-lg transition-all duration-300",
        selected && executionState === 'idle' && "ring-2 ring-primary",
        isHovered && !selected && executionState === 'idle' && "ring-1 ring-primary/50",
        getExecutionStyles()
      )}>
        <Handle type="target" position={Position.Top} className="w-3 h-3" />

        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Bot className="h-4 w-4" />
            <span className="flex-1">{nodeData.label}</span>
            {getExecutionIcon()}
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Role:</span>
            <Badge variant="outline" className="text-xs">{nodeData.role}</Badge>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Model:</span>
            <span className="text-xs font-mono">{nodeData.model}</span>
          </div>

          {nodeData.tools && nodeData.tools.length > 0 && (
            <div>
              <span className="text-xs text-muted-foreground">Tools:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {nodeData.tools.map((tool: string, i: number) => (
                  <Badge key={i} variant="secondary" className="text-xs">
                    {tool}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {nodeData.systemInstructions && (
            <div className="text-xs text-muted-foreground mt-2 line-clamp-2">
              {nodeData.systemInstructions}
            </div>
          )}
        </CardContent>

        <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
      </Card>
    </div>
  );
});

AgentNode.displayName = 'AgentNode';
