export interface Worker {
  worker_id: string;
  status: "idle" | "busy" | "draining" | "offline";
  concurrency: number;
  active_jobs: number;
  queues: string[];
  started_at: string;
  last_heartbeat: string;
}