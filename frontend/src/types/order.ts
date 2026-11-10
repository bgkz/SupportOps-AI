import { z } from "zod";

export const orderSchema = z.object({
  id: z.uuid(),
  order_number: z.string().max(10),
  created_at: z.iso.datetime({ offset: true, local: true }),
  status: z.enum(["shipped", "processing", "delivered", "cancelled"]),
  user_id: z.uuid(),
});

export type Order = z.infer<typeof orderSchema>;
