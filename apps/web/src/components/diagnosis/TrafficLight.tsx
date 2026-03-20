interface Props {
  color: string;
  size?: "sm" | "md" | "lg";
  label?: string;
}

const colorMap: Record<string, string> = {
  green: "bg-green-500",
  yellow: "bg-yellow-400",
  red: "bg-red-500",
};

const sizeMap: Record<string, string> = {
  sm: "w-4 h-4",
  md: "w-8 h-8",
  lg: "w-16 h-16",
};

export function TrafficLight({ color, size = "md", label }: Props) {
  return (
    <div className="flex items-center gap-2">
      <div
        className={`rounded-full ${colorMap[color] ?? "bg-gray-300"} ${sizeMap[size]}`}
      />
      {label && (
        <span className="text-sm text-[var(--color-text-secondary)]">
          {label}
        </span>
      )}
    </div>
  );
}
