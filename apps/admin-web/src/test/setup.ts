import "@testing-library/jest-dom/vitest";

// jsdom doesn't implement matchMedia — AntD's grid/breakpoint hooks
// (Row/Col, useBreakpoint) call it as soon as they mount, so without
// this polyfill every test that renders so much as a <Form> blows up
// with "window.matchMedia is not a function".
window.matchMedia =
  window.matchMedia ||
  function matchMediaPolyfill(query: string): MediaQueryList {
    return {
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    } as MediaQueryList;
  };
