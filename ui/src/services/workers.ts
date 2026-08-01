import { request } from "./client";
import type { Worker } from "../types/api/generated/Worker";

export const getWorkers = () => request<Worker[]>("/api/v1/workers");
export const getWorker = (id: string) => request<Worker>(`/api/v1/workers/${id}`);