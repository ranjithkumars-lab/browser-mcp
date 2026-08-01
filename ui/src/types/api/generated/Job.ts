export interface Job { job_id:string; type:string; state:string; progress:number; result?:unknown; error?:string|null; }
