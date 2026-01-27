"use client";

import { useDataStore } from "@/stores/data-store";
import { Card, Badge, Progress, EmptyState, Skeleton } from "@/components/ui";
import { cn } from "@/lib/utils";
import { MessageSquare, ThumbsUp, ThumbsDown, Minus } from "lucide-react";

export function SentimentResults() {
  const { sentimentResult, isAnalyzingSentiment } = useDataStore();

  if (isAnalyzingSentiment) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (!sentimentResult) {
    return (
      <EmptyState
        title="No sentiment analysis"
        description="Run sentiment analysis on a text column to see results"
        icon={<MessageSquare className="w-8 h-8" />}
      />
    );
  }

  const { overall, by_row } = sentimentResult;
  const total = overall.positive + overall.negative + overall.neutral;

  return (
    <div className="space-y-6">
      {/* Overall Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-success-soft flex items-center justify-center">
              <ThumbsUp className="w-5 h-5 text-success" />
            </div>
            <div>
              <p className="text-xs text-text-secondary">Positive</p>
              <p className="text-2xl font-semibold text-success">{overall.positive}</p>
            </div>
          </div>
          <Progress
            value={(overall.positive / total) * 100}
            className="mt-3 h-1.5"
          />
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-bg-tertiary flex items-center justify-center">
              <Minus className="w-5 h-5 text-text-secondary" />
            </div>
            <div>
              <p className="text-xs text-text-secondary">Neutral</p>
              <p className="text-2xl font-semibold text-text-primary">{overall.neutral}</p>
            </div>
          </div>
          <Progress
            value={(overall.neutral / total) * 100}
            className="mt-3 h-1.5"
          />
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-error-soft flex items-center justify-center">
              <ThumbsDown className="w-5 h-5 text-error" />
            </div>
            <div>
              <p className="text-xs text-text-secondary">Negative</p>
              <p className="text-2xl font-semibold text-error">{overall.negative}</p>
            </div>
          </div>
          <Progress
            value={(overall.negative / total) * 100}
            className="mt-3 h-1.5"
          />
        </Card>
      </div>

      {/* Distribution Chart */}
      <Card className="p-4">
        <h4 className="font-semibold text-text-primary mb-4">Sentiment Distribution</h4>
        <div className="h-8 flex rounded-lg overflow-hidden">
          <div
            className="bg-success transition-all"
            style={{ width: `${(overall.positive / total) * 100}%` }}
          />
          <div
            className="bg-bg-tertiary transition-all"
            style={{ width: `${(overall.neutral / total) * 100}%` }}
          />
          <div
            className="bg-error transition-all"
            style={{ width: `${(overall.negative / total) * 100}%` }}
          />
        </div>
        <div className="flex justify-between mt-2 text-xs text-text-secondary">
          <span>{((overall.positive / total) * 100).toFixed(1)}% Positive</span>
          <span>{((overall.neutral / total) * 100).toFixed(1)}% Neutral</span>
          <span>{((overall.negative / total) * 100).toFixed(1)}% Negative</span>
        </div>
      </Card>

      {/* Individual Results */}
      <Card className="p-4">
        <h4 className="font-semibold text-text-primary mb-4">Sample Results</h4>
        <div className="space-y-3 max-h-[400px] overflow-y-auto">
          {by_row.slice(0, 50).map((item, i) => (
            <div
              key={i}
              className={cn(
                "p-3 rounded-lg border",
                item.sentiment === "positive" && "bg-success-soft border-success/20",
                item.sentiment === "neutral" && "bg-bg-tertiary border-border",
                item.sentiment === "negative" && "bg-error-soft border-error/20"
              )}
            >
              <div className="flex items-start justify-between gap-4">
                <p className="text-sm text-text-primary flex-1 line-clamp-2">
                  {item.text}
                </p>
                <Badge
                  variant={
                    item.sentiment === "positive"
                      ? "success"
                      : item.sentiment === "negative"
                      ? "error"
                      : "neutral"
                  }
                  className="flex-shrink-0"
                >
                  {item.sentiment}
                </Badge>
              </div>
              <p className="text-xs text-text-tertiary mt-2">
                Confidence: {(item.confidence * 100).toFixed(1)}%
              </p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
