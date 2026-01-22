export interface EmailItem {
  id: string;
  subject: string;
  sender: string;
  date: string;
  isUnread: boolean;
  body?: string;
  labels?: string[];
}

export interface EmailResponse {
  message: string;
  action?: 'next' | 'previous' | 'switch_tab' | 'search' | 'read' | 'mark_unread' | 'delete' | 'archive' | 'star';
  success: boolean;
  speech_response?: string;
  email?: EmailItem;
}

export interface EmailListResponse {
  emails: EmailItem[];
  speech_response: string;
  total_count?: number;
  unread_count?: number;
}

export interface VoiceCommandRequest {
  command: string;
}

export interface VoiceCommandResponse extends EmailResponse {
  recognized_command?: string;
  error_details?: string;
} 