import { createBrowserRouter } from 'react-router-dom';

export const router = createBrowserRouter([
  {
    path: '/',
    lazy: async () => {
      const page = await import('../pages/UploadPage.tsx');
      return { Component: page.UploadPage };
    },
  },
  {
    path: '/videos/:videoId',
    lazy: async () => {
      const page = await import('../pages/VideoOverviewPage.tsx');
      return { Component: page.VideoOverviewPage };
    },
  },
  {
    path: '/annotate/:videoId',
    lazy: async () => {
      const page = await import('../pages/AnnotatePage.tsx');
      return { Component: page.AnnotatePage };
    },
  },
  {
    path: '/analyze/:videoId',
    lazy: async () => {
      const page = await import('../pages/AnalyzePage.tsx');
      return { Component: page.AnalyzePage };
    },
  },
  {
    path: '/result/:videoId',
    lazy: async () => {
      const page = await import('../pages/ResultPage.tsx');
      return { Component: page.ResultPage };
    },
  },
]);
