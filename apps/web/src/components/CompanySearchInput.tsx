"use client";

import { useState, useEffect, useRef } from "react";

interface Company {
  code: string;
  name: string;
  industry: string | null;
  exchange: string | null;
}

interface Props {
  onSubmit: (companyCode: string) => void;
  disabled?: boolean;
}

export function CompanySearchInput({ onSubmit, disabled }: Props) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<Company[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    if (query.length < 1) {
      setSuggestions([]);
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await fetch(
          `/api/v1/companies/search?q=${encodeURIComponent(query)}&limit=8`
        );
        if (res.ok) {
          const data = await res.json();
          setSuggestions(data);
          setShowSuggestions(true);
        }
      } catch {
        // Silently fail on autocomplete errors
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  const handleSelect = (company: Company) => {
    setQuery(company.name);
    setSelectedCode(company.code);
    setShowSuggestions(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedCode) {
      onSubmit(selectedCode);
    } else if (query.trim()) {
      onSubmit(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative w-full">
      <div className="flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setSelectedCode(null);
          }}
          placeholder="企業名または証券コードを入力..."
          className="flex-1 px-6 py-4 text-lg border-2 border-gray-200 rounded-xl
                     focus:border-[var(--color-primary-light)] focus:outline-none
                     bg-white shadow-sm"
          disabled={disabled}
        />
        <button
          type="submit"
          disabled={disabled || !query.trim()}
          className="px-8 py-4 text-lg font-bold text-white bg-[var(--color-primary)]
                     rounded-xl hover:bg-[var(--color-primary-light)]
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors shadow-sm min-w-[120px]"
        >
          {disabled ? "診断中..." : "診断開始"}
        </button>
      </div>

      {showSuggestions && suggestions.length > 0 && (
        <ul className="absolute z-10 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg max-h-80 overflow-y-auto">
          {suggestions.map((company) => (
            <li
              key={company.code}
              onClick={() => handleSelect(company)}
              className="px-6 py-3 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0"
            >
              <span className="font-medium">{company.name}</span>
              <span className="ml-3 text-sm text-[var(--color-text-secondary)]">
                {company.code}
                {company.industry && ` / ${company.industry}`}
              </span>
            </li>
          ))}
        </ul>
      )}
    </form>
  );
}
