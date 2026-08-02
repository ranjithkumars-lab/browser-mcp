import type { JSX } from "react";

function base(props: JSX.IntrinsicElements["svg"]) {
  return {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": true,
    ...props,
  } as const;
}

export const Icons = {
  dashboard: (p: JSX.IntrinsicElements["svg"]) => (
    <svg {...base(p)}><rect x="3" y="3" width="7" height="9" rx="1" /><rect x="14" y="3" width="7" height="5" rx="1" /><rect x="14" y="12" width="7" height="9" rx="1" /><rect x="3" y="16" width="7" height="5" rx="1" /></svg>
  ),
  chat: (p: JSX.IntrinsicElements["svg"]) => (
    <svg {...base(p)}><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
  ),
  jobs: (p: JSX.IntrinsicElements["svg"]) => (
    <svg {...base(p)}><path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" /></svg>
  ),
  workers: (p: JSX.IntrinsicElements["svg"]) => (
    <svg {...base(p)}><rect x="2" y="7" width="20" height="14" rx="2" /><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" /></svg>
  ),
  logs: (p: JSX.IntrinsicElements["svg"]) => (
    <svg {...base(p)}><path d="M4 4h16v16H4z" /><path d="M8 9h8M8 13h5M8 17h8" /></svg>
  ),
  plugins: (p: JSX.IntrinsicElements["svg"]) => (
    <svg {...base(p)}><path d="M12 2l2.4 4.8L20 8l-4 3.6 1 6.4-5-2.8-5 2.8 1-6.4L4 8l5.6-1.2z" /></svg>
  ),
  artifacts: (p: JSX.IntrinsicElements["svg"]) => (
    <svg {...base(p)}><path d="M21 8v13H3V8" /><path d="M1 3h22v5H1z" /><path d="M10 12h4" /></svg>
  ),
  sessions: (p: JSX.IntrinsicElements["svg"]) => (
    <svg {...base(p)}><rect x="2" y="4" width="20" height="16" rx="2" /><path d="M8 4v16" /></svg>
  ),
  downloads: (p: JSX.IntrinsicElements["svg"]) => (
    <svg {...base(p)}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="M7 10l5 5 5-5" /><path d="M12 15V3" /></svg>
  ),
  access: (p: JSX.IntrinsicElements["svg"]) => (
    <svg {...base(p)}><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
  ),
  settings: (p: JSX.IntrinsicElements["svg"]) => (
    <svg {...base(p)}><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg>
  ),
  menu: (p: JSX.IntrinsicElements["svg"]) => (
    <svg {...base(p)}><path d="M4 6h16M4 12h16M4 18h16" /></svg>
  ),
  sun: (p: JSX.IntrinsicElements["svg"]) => (
    <svg {...base(p)}><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" /></svg>
  ),
  moon: (p: JSX.IntrinsicElements["svg"]) => (
    <svg {...base(p)}><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg>
  ),
} as const;

export type IconName = keyof typeof Icons;

export function Icon({ name, ...props }: { name: IconName } & JSX.IntrinsicElements["svg"]) {
  const Cmp = Icons[name];
  return <Cmp {...props} />;
}
