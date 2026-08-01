import { request } from "./client"; import type { Job } from "../types/api/generated/Job";
export const getJob=(id:string)=>request<Job>("/api/v1/jobs/"+id);
export const cancelJob=(id:string)=>request<Job>("/api/v1/jobs/"+id,{method:"DELETE"});
