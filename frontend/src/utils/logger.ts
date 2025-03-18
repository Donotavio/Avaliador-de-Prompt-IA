type LogLevel = 'info' | 'warn' | 'error';

class Logger {
  private static instance: Logger;
  private logFile: string = 'frontend.log';
  
  private constructor() {
    // Singleton
  }

  public static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  private formatMessage(level: LogLevel, message: string): string {
    const timestamp = new Date().toISOString();
    return `${timestamp} - ${level.toUpperCase()} - ${message}`;
  }

  private log(level: LogLevel, message: string, error?: Error): void {
    const formattedMessage = this.formatMessage(level, message);
    
    // Log no console
    switch (level) {
      case 'info':
        console.log(formattedMessage);
        break;
      case 'warn':
        console.warn(formattedMessage);
        break;
      case 'error':
        console.error(formattedMessage, error);
        break;
    }
    
    // Em produção, você pode enviar logs para um serviço de logging
    if (process.env.NODE_ENV === 'production') {
      // Implementar envio para serviço de logging
    }
  }

  public info(message: string): void {
    this.log('info', message);
  }

  public warn(message: string): void {
    this.log('warn', message);
  }

  public error(message: string, error?: Error): void {
    this.log('error', message, error);
  }
}

export const logger = Logger.getInstance(); 