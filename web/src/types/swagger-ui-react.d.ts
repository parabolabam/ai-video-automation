declare module 'swagger-ui-react' {
  import { Component } from 'react';

  interface SwaggerUIProps {
    spec?: any;
    url?: string;
    onComplete?: (system: any) => void;
    requestInterceptor?: (req: any) => any;
    responseInterceptor?: (res: any) => any;
    docExpansion?: 'list' | 'full' | 'none';
    defaultModelsExpandDepth?: number;
    [key: string]: any;
  }

  export default class SwaggerUI extends Component<SwaggerUIProps> {}
}
