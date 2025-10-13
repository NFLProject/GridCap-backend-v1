import React from "react";

type CardProps = {
  title?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
};

export default function Card({ title, children, actions }: CardProps) {
  return (
    <section className="bg-white shadow-sm rounded-lg p-6 border border-slate-200">
      {title && <h3 className="text-xl mb-4 text-brand">{title}</h3>}
      <div className="space-y-4">{children}</div>
      {actions && <div className="mt-6 flex gap-3">{actions}</div>}
    </section>
  );
}
