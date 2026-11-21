import { z } from "zod";

export const ticketSchema = z.object({
  id: z.uuid(),
  user_id: z.uuid(),
  order_number: z.string().nullable(),
  text: z.string(),
  category: z
    .enum([
      "damaged_goods",
      "return_refund",
      "shipping_status",
      "invoice_payment",
      "technical_faq",
      "out_of_scope",
    ])
    .nullable(),
  status: z.enum([
    "pending",
    "processing",
    "waiting_for_approval",
    "resolved",
    "escalated",
  ]),
  reply_draft: z.record(z.string(), z.unknown()).nullable(),
  knowledge_sources: z.array(z.record(z.string(), z.unknown())).nullable(),
  review_reason: z.string().nullable(),
  approved: z.boolean().nullable(),
  created_at: z.iso.datetime({ offset: true, local: true }),
  updated_at: z.iso.datetime({ offset: true, local: true }),
});

export type Ticket = z.infer<typeof ticketSchema>;
