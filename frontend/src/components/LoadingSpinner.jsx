import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ message = "Analyzing documents with AI..." }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-4 border-indigo-100 border-t-indigo-600 animate-spin"></div>
        <div className="absolute inset-0 flex items-center justify-center text-indigo-600">
          <Loader2 className="w-6 h-6 animate-pulse" />
        </div>
      </div>
      <p className="mt-4 text-base font-semibold text-slate-800">{message}</p>
      <p className="text-xs text-slate-400 mt-1">Running semantic NLP matching & computing company weight matrices...</p>
    </div>
  );
}
