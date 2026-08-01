export interface BrowserEvent { header:{event_id:string;timestamp:string;priority:number}; event_type:string; category:string; meta:Record<string,unknown>; payload:Record<string,unknown>; }
