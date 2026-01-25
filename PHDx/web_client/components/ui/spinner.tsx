"use client";

import { cn } from "@/lib/utils";

interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: "sm" | "md" | "lg";
}

function Spinner({ className, size = "md", ...props }: SpinnerProps) {
  const sizes = {
    sm: "w-4 h-4 border",
    md: "w-5 h-5 border-2",
    lg: "w-8 h-8 border-2",
  };

  return (
    <div
      className={cn(
        "rounded-full border-border border-t-accent-primary animate-spin",
        sizes[size],
        className
      )}
      {...props}
    />
  );
}

export { Spinner };
