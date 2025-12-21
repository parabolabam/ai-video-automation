'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { X } from 'lucide-react';

interface AgentConfig {
  label: string;
  role: string;
  model: string;
  systemInstructions: string;
  tools: string[];
}

interface AgentConfigDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (config: AgentConfig) => void;
  initialConfig?: AgentConfig;
}

const AVAILABLE_MODELS = [
  'gpt-4o',
  'gpt-4o-mini',
  'gpt-4-turbo',
  'claude-3-5-sonnet-20241022',
  'claude-3-5-haiku-20241022',
];

const AVAILABLE_TOOLS = [
  'web_search',
  'image_generation',
  'code_interpreter',
  'file_reader',
];

export function AgentConfigDialog({ open, onClose, onSave, initialConfig }: AgentConfigDialogProps) {
  const [config, setConfig] = useState<AgentConfig>(
    initialConfig || {
      label: '',
      role: 'Researcher',
      model: 'gpt-4o',
      systemInstructions: 'You are a helpful AI assistant.',
      tools: [],
    }
  );

  const [newTool, setNewTool] = useState('');

  useEffect(() => {
    if (initialConfig) {
      setConfig(initialConfig);
    }
  }, [initialConfig]);

  const handleSave = () => {
    if (!config.label.trim()) {
      alert('Agent name is required');
      return;
    }
    onSave(config);
    onClose();
  };

  const addTool = (tool: string) => {
    if (tool && !config.tools.includes(tool)) {
      setConfig({ ...config, tools: [...config.tools, tool] });
    }
  };

  const removeTool = (tool: string) => {
    setConfig({ ...config, tools: config.tools.filter((t) => t !== tool) });
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Configure Agent</DialogTitle>
          <DialogDescription>
            Set up the agent's name, role, model, and capabilities.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="name">Agent Name</Label>
            <Input
              id="name"
              value={config.label}
              onChange={(e) => setConfig({ ...config, label: e.target.value })}
              placeholder="e.g., Content Researcher"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="role">Role</Label>
            <Input
              id="role"
              value={config.role}
              onChange={(e) => setConfig({ ...config, role: e.target.value })}
              placeholder="e.g., Researcher, Writer, Analyzer"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="model">AI Model</Label>
            <Select value={config.model} onValueChange={(value) => setConfig({ ...config, model: value })}>
              <SelectTrigger>
                <SelectValue placeholder="Select a model" />
              </SelectTrigger>
              <SelectContent>
                {AVAILABLE_MODELS.map((model) => (
                  <SelectItem key={model} value={model}>
                    {model}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="instructions">System Instructions</Label>
            <Textarea
              id="instructions"
              value={config.systemInstructions}
              onChange={(e) => setConfig({ ...config, systemInstructions: e.target.value })}
              placeholder="Describe the agent's personality and guidelines..."
              rows={6}
            />
          </div>

          <div className="grid gap-2">
            <Label>Tools</Label>
            <Select value={newTool} onValueChange={(value) => { addTool(value); setNewTool(''); }}>
              <SelectTrigger>
                <SelectValue placeholder="Add a tool..." />
              </SelectTrigger>
              <SelectContent>
                {AVAILABLE_TOOLS.map((tool) => (
                  <SelectItem key={tool} value={tool} disabled={config.tools.includes(tool)}>
                    {tool}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="flex flex-wrap gap-2 mt-2">
              {config.tools.map((tool) => (
                <Badge key={tool} variant="secondary" className="flex items-center gap-1">
                  {tool}
                  <button
                    onClick={() => removeTool(tool)}
                    className="ml-1 hover:text-destructive"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave}>Save Agent</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
