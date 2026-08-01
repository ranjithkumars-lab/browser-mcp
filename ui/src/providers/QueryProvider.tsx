import {createContext,useContext,useState,type ReactNode} from "react";
const Query=createContext({revision:0,invalidate:()=>{}});export function QueryProvider({children}:{children:ReactNode}){const[revision,setRevision]=useState(0);return <Query.Provider value={{revision,invalidate:()=>setRevision(v=>v+1)}}>{children}</Query.Provider>}export const useQueryRevision=()=>useContext(Query);
