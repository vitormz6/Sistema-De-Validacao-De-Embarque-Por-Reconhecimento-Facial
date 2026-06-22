import "@testing-library/jest-dom/vitest";

// jsdom doesn't implement matchMedia — same polyfill as admin-web's setup.ts.
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

// jsdom doesn't implement getUserMedia — CameraCapture calls it on mount.
if (!window.navigator.mediaDevices) {
  Object.defineProperty(window.navigator, "mediaDevices", {
    value: {
      getUserMedia: () =>
        Promise.resolve({
          getTracks: () => [],
        } as unknown as MediaStream),
    },
    configurable: true,
  });
}
