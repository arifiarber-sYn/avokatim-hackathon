export interface Contact {
  id: string;
  kind: string;
  display_name: string;
  national_id: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  notes: string | null;
  portal_enabled: boolean;
}

export interface Matter {
  id: string;
  reference: string;
  title: string;
  description: string | null;
  practice_area: string;
  status: string;
  client: Contact | null;
  responsible_user_id: string | null;
  court_name: string | null;
  court_case_number: string | null;
  opened_on: string | null;
  closed_on: string | null;
  restricted: boolean;
}

export interface Deadline {
  id: string;
  matter_id: string;
  kind: string;
  title: string;
  due_at: string;
  legal_basis: string | null;
  status: string;
  trigger_date: string | null;
  notes: string | null;
}

export interface DeadlineRule {
  id: string;
  code: string;
  name: Record<string, string>;
  legal_basis: string | null;
  practice_area: string | null;
  trigger_event: string;
  days: number;
  day_type: string;
}

export interface Doc {
  id: string;
  family_id: string;
  version: number;
  filename: string;
  mime_type: string;
  size_bytes: number;
  category: string | null;
  ocr_status: string;
  has_text: boolean;
  visible_to_client: boolean;
  approval_status: string;
  reviewer_id: string | null;
  approval_note: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface Intake {
  id: string;
  client_name: string;
  client_email: string | null;
  client_phone: string | null;
  opposing_names: string[];
  summary: string;
  status: string;
  conflict_result: {
    has_conflicts: boolean;
    hits: {
      contact_name: string;
      appears_in: { role: string; matter: string; title: string }[];
    }[];
  } | null;
  ai_classification: {
    practice_area?: string;
    suggested_title?: string;
    urgency?: string;
    key_issues?: string[];
    summary?: string;
  } | null;
  matter_id: string | null;
  created_at: string;
}

export interface Template {
  id: string;
  code: string;
  locale: string;
  name: Record<string, string>;
  practice_area: string | null;
  variables: { name: string; label: Record<string, string> }[];
}

export interface TimeEntry {
  id: string;
  matter_id: string;
  started_at: string;
  minutes: number;
  description: string;
  billable: boolean;
  hourly_rate: string | null;
  invoice_id: string | null;
}

export interface Task {
  id: string;
  matter_id: string | null;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  due_date: string | null;
  assignee_id: string | null;
  created_at: string;
}

export interface Expense {
  id: string;
  matter_id: string;
  incurred_on: string;
  description: string;
  category: string;
  amount: string;
  billable: boolean;
  invoice_id: string | null;
}

export interface Invoice {
  id: string;
  number: string;
  matter_id: string | null;
  contact_id?: string | null;
  status: string;
  currency: string;
  issued_on: string | null;
  due_on: string | null;
  paid_on: string | null;
  payment_reference: string | null;
  vat_rate: number;
  vat_amount: string;
  total_with_vat: string;
  items: { id: string; description: string; quantity: string; unit_price: string; amount: string }[];
  total: string;
}

export interface Message {
  id: string;
  role: string;
  content: string;
  citations: { type: string; title: string; section?: string; reference?: string }[];
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string | null;
  matter_id: string | null;
  provider: string;
  created_at: string;
}

export const PRACTICE_AREAS = [
  "civil",
  "criminal",
  "family",
  "commercial",
  "labor",
  "administrative",
  "other",
] as const;
