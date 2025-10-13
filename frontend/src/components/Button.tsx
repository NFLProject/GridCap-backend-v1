"use client";

import clsx from "clsx";
import React from "react";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary";
};

export default function Button({ variant = "primary", className, ...props }: ButtonProps) {
  const base = "inline-flex items-center justify-center rounded-md px-4 py-2 font-medium";
  const variants = {
    primary: "bg-brand-accent text-white hover:bg-sky-500",
    secondary: "bg-white text-brand border border-brand hover:bg-slate-100",
  } as const;

  return <button className={clsx(base, variants[variant], className)} {...props} />;
}
