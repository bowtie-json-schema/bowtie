/** The one hover tooltip the real-world benchmark charts share (see ChartTip.svelte). */
export interface TipContent {
  title: string;
  subtitle?: string;
  rows: [label: string, value: string][];
}

class ChartTipState {
  content = $state<TipContent | null>(null);
  x = $state(0);
  y = $state(0);

  show(event: PointerEvent, content: TipContent) {
    this.content = content;
    this.x = event.clientX;
    this.y = event.clientY;
  }

  hide() {
    this.content = null;
  }
}

export const chartTip = new ChartTipState();
