"use client";

import { useDataStore } from "@/stores/data-store";
import { Card, Badge, EmptyState, Skeleton } from "@/components/ui";
import { BarChart3, AlertTriangle, Hash, Type } from "lucide-react";

function StatCard({
  title,
  value,
  subtitle,
  icon,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
}) {
  return (
    <Card className="p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-text-secondary">{title}</p>
          <p className="text-2xl font-semibold text-text-primary mt-1">{value}</p>
          {subtitle && <p className="text-xs text-text-tertiary mt-1">{subtitle}</p>}
        </div>
        {icon && (
          <div className="w-10 h-10 rounded-lg bg-bg-tertiary flex items-center justify-center">
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
}

export function EDAResults() {
  const { edaResult, isRunningEda } = useDataStore();

  if (isRunningEda) {
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

  if (!edaResult) {
    return (
      <EmptyState
        title="No EDA results"
        description="Run exploratory data analysis to see insights about your dataset"
        icon={<BarChart3 className="w-8 h-8" />}
      />
    );
  }

  const { summary, column_types, missing_values, numeric_stats, categorical_stats } = edaResult;

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Total Rows"
          value={summary.total_rows.toLocaleString()}
          icon={<Hash className="w-5 h-5 text-text-secondary" />}
        />
        <StatCard
          title="Total Columns"
          value={summary.total_columns}
          icon={<Type className="w-5 h-5 text-text-secondary" />}
        />
        <StatCard
          title="Memory Usage"
          value={summary.memory_usage}
          icon={<BarChart3 className="w-5 h-5 text-text-secondary" />}
        />
      </div>

      {/* Column Types */}
      <Card className="p-4">
        <h4 className="font-semibold text-text-primary mb-4">Column Types</h4>
        <div className="flex flex-wrap gap-2">
          {Object.entries(column_types).map(([col, type]) => (
            <div
              key={col}
              className="px-3 py-1.5 bg-bg-tertiary rounded-lg text-sm flex items-center gap-2"
            >
              <span className="text-text-primary font-medium">{col}</span>
              <Badge variant={type.includes("int") || type.includes("float") ? "success" : "info"}>
                {type}
              </Badge>
            </div>
          ))}
        </div>
      </Card>

      {/* Missing Values */}
      {Object.values(missing_values).some((v) => v > 0) && (
        <Card className="p-4">
          <h4 className="font-semibold text-text-primary mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-warning" />
            Missing Values
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(missing_values)
              .filter(([, count]) => count > 0)
              .map(([col, count]) => (
                <div key={col} className="p-3 bg-warning-soft rounded-lg">
                  <p className="text-sm font-medium text-text-primary">{col}</p>
                  <p className="text-lg font-semibold text-warning">{count}</p>
                </div>
              ))}
          </div>
        </Card>
      )}

      {/* Numeric Statistics */}
      {Object.keys(numeric_stats).length > 0 && (
        <Card className="p-4 overflow-hidden">
          <h4 className="font-semibold text-text-primary mb-4">Numeric Statistics</h4>
          <div className="overflow-auto">
            <table className="w-full text-sm">
              <thead className="bg-bg-tertiary">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-text-secondary">
                    Column
                  </th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-text-secondary">
                    Mean
                  </th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-text-secondary">
                    Std
                  </th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-text-secondary">
                    Min
                  </th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-text-secondary">
                    Max
                  </th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(numeric_stats).map(([col, stats]) => (
                  <tr key={col} className="border-t border-border">
                    <td className="px-4 py-2 font-medium text-text-primary">{col}</td>
                    <td className="px-4 py-2 text-right text-text-secondary">
                      {stats.mean?.toFixed(2) ?? "-"}
                    </td>
                    <td className="px-4 py-2 text-right text-text-secondary">
                      {stats.std?.toFixed(2) ?? "-"}
                    </td>
                    <td className="px-4 py-2 text-right text-text-secondary">
                      {stats.min?.toFixed(2) ?? "-"}
                    </td>
                    <td className="px-4 py-2 text-right text-text-secondary">
                      {stats.max?.toFixed(2) ?? "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Categorical Statistics */}
      {Object.keys(categorical_stats).length > 0 && (
        <Card className="p-4">
          <h4 className="font-semibold text-text-primary mb-4">Categorical Columns</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(categorical_stats).map(([col, stats]) => (
              <div key={col} className="p-4 bg-bg-tertiary rounded-lg">
                <p className="font-medium text-text-primary mb-2">{col}</p>
                <div className="space-y-1 text-sm">
                  <p className="text-text-secondary">
                    Unique values: <span className="text-text-primary">{stats.unique}</span>
                  </p>
                  <p className="text-text-secondary">
                    Most common: <span className="text-text-primary">{stats.top}</span>
                    <span className="text-text-tertiary"> ({stats.frequency}x)</span>
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
