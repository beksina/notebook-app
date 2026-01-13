export type HighlightColor = "yellow" | "green" | "blue" | "pink";

export interface HighlightPosition {
  start_offset?: number;
  end_offset?: number;
  page?: number; // PDF only
}

export interface Highlight {
  id: string;
  source_material_id: string;
  position: HighlightPosition;
  selected_text: string;
  color: HighlightColor;
  note: string | null;
  created_at: string;
  updated_at: string;
}

export interface HighlightCreate {
  position: HighlightPosition;
  selected_text: string;
  color?: HighlightColor;
  note?: string;
}

export interface HighlightUpdate {
  color?: HighlightColor;
  note?: string;
}

export interface TextSelection {
  text: string;
  startOffset: number;
  endOffset: number;
  page?: number; // PDF only
}
