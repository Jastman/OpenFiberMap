import { useState, useCallback } from "react";
import type { FilterState, Region, FiberStatus, CapacityClass } from "@/types";

export const DEFAULT_FILTERS: FilterState = {
  region: "all",
  operator: "all",
  status: "all",
  capacityClass: "all",
  searchQuery: "",
};

export function useFilters() {
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);

  const setRegion = useCallback((region: Region | "all") => {
    setFilters((f) => ({ ...f, region }));
  }, []);

  const setOperator = useCallback((operator: string) => {
    setFilters((f) => ({ ...f, operator }));
  }, []);

  const setStatus = useCallback((status: FiberStatus | "all") => {
    setFilters((f) => ({ ...f, status }));
  }, []);

  const setCapacityClass = useCallback((capacityClass: CapacityClass | "all") => {
    setFilters((f) => ({ ...f, capacityClass }));
  }, []);

  const setSearchQuery = useCallback((searchQuery: string) => {
    setFilters((f) => ({ ...f, searchQuery }));
  }, []);

  const reset = useCallback(() => setFilters(DEFAULT_FILTERS), []);

  return {
    filters,
    setRegion,
    setOperator,
    setStatus,
    setCapacityClass,
    setSearchQuery,
    reset,
  };
}
