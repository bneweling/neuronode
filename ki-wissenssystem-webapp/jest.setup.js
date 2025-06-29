require('@testing-library/jest-dom');

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/',
      pathname: '/',
      query: {},
      asPath: '/',
      push: jest.fn(),
      pop: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      prefetch: jest.fn().mockResolvedValue(undefined),
      beforePopState: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn(),
      },
    };
  },
}));

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
      prefetch: jest.fn(),
    };
  },
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}));

// Mock WebSocket für Real-time Tests
global.WebSocket = class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) this.onopen();
    }, 100);
  }
  
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  
  send = jest.fn();
  close = jest.fn();
  addEventListener = jest.fn();
  removeEventListener = jest.fn();
};

// Mock IntersectionObserver für Performance Tests
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock ResizeObserver für Component Tests
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock für Cytoscape (Graph Component)
jest.mock('cytoscape', () => {
  return jest.fn(() => ({
    mount: jest.fn(),
    unmount: jest.fn(),
    destroy: jest.fn(),
    nodes: jest.fn(() => ({
      length: 10,
      forEach: jest.fn(),
    })),
    edges: jest.fn(() => ({
      length: 15,
      forEach: jest.fn(),
    })),
    layout: jest.fn(() => ({
      run: jest.fn(),
      stop: jest.fn(),
    })),
    zoom: jest.fn(),
    pan: jest.fn(),
    center: jest.fn(),
    on: jest.fn(),
    off: jest.fn(),
    style: jest.fn(),
    add: jest.fn(),
    remove: jest.fn(),
  }));
});

// Environment Variables für Tests
process.env.NODE_ENV = 'test';
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
process.env.NEXT_PUBLIC_WS_URL = 'ws://localhost:8000';

// Console Error/Warning Filter für cleaner Test Output
const originalError = console.error;
const originalWarn = console.warn;

console.error = (...args) => {
  if (
    typeof args[0] === 'string' &&
    args[0].includes('Warning: ReactDOM.render is deprecated')
  ) {
    return;
  }
  originalError.call(console, ...args);
};

console.warn = (...args) => {
  if (
    typeof args[0] === 'string' &&
    (args[0].includes('componentWillReceiveProps') ||
     args[0].includes('componentWillMount'))
  ) {
    return;
  }
  originalWarn.call(console, ...args);
};

// Performance Timing Mock für Performance Tests
Object.defineProperty(window, 'performance', {
  value: {
    now: jest.fn(() => Date.now()),
    mark: jest.fn(),
    measure: jest.fn(),
    getEntriesByType: jest.fn(() => []),
    getEntriesByName: jest.fn(() => []),
  },
  writable: true,
});

// Mock für File API (Document Upload Tests)
Object.defineProperty(window, 'File', {
  value: class File {
    constructor(chunks, filename, options = {}) {
      this.chunks = chunks;
      this.name = filename;
      this.size = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
      this.type = options.type || '';
      this.lastModified = Date.now();
    }
  },
});

Object.defineProperty(window, 'FileList', {
  value: class FileList {
    constructor(files = []) {
      this.length = files.length;
      files.forEach((file, index) => {
        this[index] = file;
      });
    }
  },
});

// Setup für Accessibility Tests
require('axe-core'); 