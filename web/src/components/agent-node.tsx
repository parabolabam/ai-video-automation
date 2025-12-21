import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Bot } from 'lucide-react';

interface AgentNodeData {
  label: string;
  role: string;
  model: string;
  tools?: string[];
  systemInstructions?: string;
}

export const AgentNode = memo(({ data }: NodeProps) => {
  const nodeData = data as unknown as AgentNodeData;
  return (
    <Card className="min-w-[250px] shadow-lg">
      <Handle type="target" position={Position.Top} className="w-3 h-3" />

      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <Bot className="h-4 w-4" />
          {nodeData.label}
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
  );
});

AgentNode.displayName = 'AgentNode';
