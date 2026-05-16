interface RouteResultSkeletonProps {
  baseFontSize: number;
}

export default function RouteResultSkeleton({ baseFontSize }: RouteResultSkeletonProps) {
  const tabHeight = Math.round(48 * baseFontSize);
  const cardPadding = Math.round(24 * baseFontSize);
  const barHeight = Math.round(20 * baseFontSize);
  const barHeightLg = Math.round(28 * baseFontSize);

  return (
    <div className="animate-pulse" aria-hidden="true">
      <div className="flex gap-3 mb-6">
        <div
          className="flex-1 rounded-full bg-eldergo-border/80"
          style={{ height: tabHeight }}
        />
        <div
          className="flex-1 rounded-full bg-eldergo-border/60"
          style={{ height: tabHeight }}
        />
      </div>

      <div
        className="bg-white/90 rounded-2xl shadow-md mb-6 space-y-4"
        style={{ padding: cardPadding }}
      >
        <div
          className="rounded-lg bg-eldergo-border/80 w-3/4"
          style={{ height: barHeightLg }}
        />
        <div
          className="rounded-lg bg-eldergo-border/60 w-full"
          style={{ height: barHeight }}
        />
        <div
          className="rounded-lg bg-eldergo-border/60 w-5/6"
          style={{ height: barHeight }}
        />
        <div
          className="rounded-lg bg-eldergo-border/50 w-2/3"
          style={{ height: barHeight }}
        />
      </div>
    </div>
  );
}
