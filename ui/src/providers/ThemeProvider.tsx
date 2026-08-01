import {createContext,useContext,useState,type ReactNode} from "react";
const Theme=createContext({dark:false,toggle:()=>{}});
export function ThemeProvider({children}:{children:ReactNode}){const[dark,setDark]=useState(false);return <Theme.Provider value={{dark,toggle:()=>{setDark(v=>!v);document.documentElement.classList.toggle("dark")}}}>{children}</Theme.Provider>}
export const useTheme=()=>useContext(Theme);
