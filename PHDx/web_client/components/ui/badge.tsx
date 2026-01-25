"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "success" | "warning" | "error" | "info" | "neutral";
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = "neutral", ...props }, ref) => {
    const variants = {
      success: "badge-success",
      warning: "badge-warning",
      error: "badge-error",
      info: "badge-info",
      neutral: "badge-neutral",
    };

    return (
      <span
        ref={ref}
        className={cn("badge", variants[variant], className)}
        {...props}
      />
    );
  }
);

Badge.displayName = "Badge";

export { Badge };
