"use client";

import React from "react";

interface FormProps extends React.FormHTMLAttributes<HTMLFormElement> {
  title: string;
  description?: string;
  error?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
}

export default function Form({ title, description, error, children, actions, ...rest }: FormProps) {
  return (
    <form className="bg-white shadow-sm rounded-lg p-6 border border-slate-200 space-y-4" {...rest}>
      <div>
        <h2 className="text-2xl text-brand mb-1">{title}</h2>
        {description && <p className="text-sm text-slate-600">{description}</p>}
        {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
      </div>
      <div className="space-y-4">{children}</div>
      {actions && <div className="flex gap-3 justify-end">{actions}</div>}
    </form>
  );
}
