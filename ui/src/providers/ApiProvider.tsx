import {createContext,useContext,type ReactNode} from "react";
const Api=createContext({apiKey:""});export function ApiProvider({children}:{children:ReactNode}){return <Api.Provider value={{apiKey:""}}>{children}</Api.Provider>}export const useApi=()=>useContext(Api);
