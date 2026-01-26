import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/lib/auth-context';
import { workflowApi, cronApi, CreateWorkflowInput, SaveGraphInput, UpdateWorkflowInput } from '@/lib/api-client';

export function useWorkflows(userId?: string) {
  const { session } = useAuth();

  return useQuery({
    queryKey: ['workflows', userId],
    queryFn: () => workflowApi.list(session!.access_token, userId),
    enabled: !!session?.access_token,
  });
}

export function useWorkflow(id: string | undefined) {
  const { session } = useAuth();

  return useQuery({
    queryKey: ['workflow', id],
    queryFn: () => workflowApi.get(id!, session!.access_token),
    enabled: !!session?.access_token && !!id,
    refetchOnWindowFocus: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

export function useCreateWorkflow() {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateWorkflowInput) =>
      workflowApi.create(data, session!.access_token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });
}

export function useDeleteWorkflow() {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => workflowApi.delete(id, session!.access_token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });
}

export function useSaveWorkflowGraph(workflowId: string) {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Omit<SaveGraphInput, 'workflowId'>) =>
      workflowApi.saveGraph({ ...data, workflowId }, session!.access_token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflow', workflowId] });
    },
  });
}

export function useUpdateWorkflow(workflowId: string) {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateWorkflowInput) =>
      workflowApi.update(workflowId, data, session!.access_token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflow', workflowId] });
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });
}

export function useCronJobs() {
  const { session } = useAuth();

  return useQuery({
    queryKey: ['cron-jobs'],
    queryFn: () => cronApi.list(session!.access_token),
    enabled: !!session?.access_token,
  });
}

export function useCreateCronJob() {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ cronExpression, input }: { cronExpression: string; input: Record<string, unknown> }) =>
      cronApi.create(cronExpression, input, session!.access_token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cron-jobs'] });
    },
  });
}

export function useDeleteCronJob() {
  const { session } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: string) => cronApi.delete(jobId, session!.access_token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cron-jobs'] });
    },
  });
}
