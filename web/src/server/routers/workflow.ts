import { z } from 'zod';
import { publicProcedure, router } from '../trpc';
import { supabase } from '@/lib/supabase';

export const workflowRouter = router({
  list: publicProcedure
    .input(z.object({ userId: z.string().uuid() }).optional())
    .query(async ({ input }) => {
      // In a real app, get userId from session. For now, use the seed user or input.
      const targetUser = input?.userId || 'cb176b48-0995-41e2-8dda-2b80b29cb94d'; 
      
      const { data, error } = await supabase
        .from('workflows')
        .select('*')
        .eq('user_id', targetUser)
        .order('created_at', { ascending: false });

      if (error) throw new Error(error.message);
      return data;
    }),

  get: publicProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input }) => {
      const { data, error } = await supabase
        .from('workflows')
        .select('*, agents(*), workflow_connections(*)')
        .eq('id', input.id)
        .single();
        
      if (error) throw new Error(error.message);
      return data;
    }),
});
