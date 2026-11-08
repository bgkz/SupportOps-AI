import { z } from "zod";

export const userSchema = z.object({
  id: z.uuid(),
  user_role: z.string(),
  email: z.email(),
  created_at: z.iso.datetime({ offset: true, local: true }),
  updated_at: z.iso.datetime({ offset: true, local: true }),
  email_verified_at: z.iso.datetime({ offset: true, local: true }).nullable(),
});

export type User = z.infer<typeof userSchema>;
