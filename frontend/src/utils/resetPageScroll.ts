export function resetPageScroll(): void {
  if ('scrollRestoration' in history) {
    history.scrollRestoration = 'manual';
  }

  document.scrollingElement?.scrollTo?.(0, 0);
  window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  document.documentElement.scrollTop = 0;
  document.body.scrollTop = 0;

  const root = document.getElementById('root');
  if (root) {
    root.scrollTop = 0;
  }

  document.querySelectorAll<HTMLElement>('*').forEach((element) => {
    if (element.scrollTop > 0) {
      element.scrollTop = 0;
    }
  });
}
