import { z } from 'zod';
import { publicProcedure, router } from '../trpc';
import { workflowRouter } from './workflow';

export const appRouter = router({
  hello: publicProcedure
    .input(z.object({ text: z.string().nullish() }).nullish())
    .query(({ input }) => {
      return {
        greeting: `Hello ${input?.text ?? 'world'}`,
      };
    }),
  workflow: workflowRouter,
});

export type AppRouter = typeof appRouter;
