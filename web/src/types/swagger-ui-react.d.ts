declare module 'swagger-ui-react' {
  import { Component } from 'react';

  interface SwaggerUIProps {
    spec?: unknown;
    url?: string;
    onComplete?: (system: unknown) => void;
    requestInterceptor?: (req: unknown) => unknown;
    responseInterceptor?: (res: unknown) => unknown;
    docExpansion?: 'list' | 'full' | 'none';
    defaultModelsExpandDepth?: number;
    [key: string]: unknown;
  }

  export default class SwaggerUI extends Component<SwaggerUIProps> {}
}
