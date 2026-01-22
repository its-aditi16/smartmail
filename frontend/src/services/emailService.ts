import axios from 'axios';
import { EmailResponse, EmailListResponse, EmailItem, VoiceCommandRequest, VoiceCommandResponse } from '../types/email';

const API_BASE_URL = 'http://localhost:5000';

class EmailService {
  async startEmailAssistant(): Promise<EmailResponse> {
    try {
      const response = await axios.get<EmailResponse>(`${API_BASE_URL}/api/start`);
      return response.data;
    } catch (error) {
      console.error('Error starting email assistant:', error);
      throw this.handleError(error);
    }
  }

  async getEmails(): Promise<EmailListResponse> {
    try {
      const response = await axios.get<EmailListResponse>(`${API_BASE_URL}/api/emails`);
      // Transform the response to match EmailItem interface
      const emails = response.data.emails.map(email => ({
        id: email.id,
        subject: email.subject,
        sender: email.sender,
        date: email.date,
        isUnread: email.labels?.includes('UNREAD') || false,
        body: email.body,
        labels: email.labels
      }));
      return {
        emails,
        speech_response: response.data.speech_response,
        total_count: response.data.total_count,
        unread_count: response.data.unread_count
      };
    } catch (error) {
      console.error('Error fetching emails:', error);
      throw this.handleError(error);
    }
  }

  async processVoiceCommand(command: string): Promise<VoiceCommandResponse> {
    try {
      const request: VoiceCommandRequest = { command };
      const response = await axios.post<VoiceCommandResponse>(`${API_BASE_URL}/api/voice/process`, request);
      return response.data;
    } catch (error) {
      console.error('Error processing voice command:', error);
      throw this.handleError(error);
    }
  }

  private handleError(error: any): Error {
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.message || error.message;
      return new Error(`API Error: ${message}`);
    }
    return error instanceof Error ? error : new Error('An unknown error occurred');
  }
}

export default new EmailService(); 