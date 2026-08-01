import { request } from "./client";
export interface Dashboard {jobs:{total:number;running:number;failed:number};workers:Record<string,unknown>;plugins:unknown}
export const getDashboard=()=>request<Dashboard>("/api/v1/dashboard");
