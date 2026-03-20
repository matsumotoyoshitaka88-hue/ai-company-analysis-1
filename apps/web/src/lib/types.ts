export interface DiagnosisReport {
  company: {
    code: string;
    name: string;
    industry: string;
  };
  overall_score: {
    score: number;
    traffic_light: string;
    summary_text: string;
  };
  sections: {
    executive_summary: {
      content: string;
    };
    financial_diagnosis: {
      profitability: ScoredSection;
      safety: ScoredSection;
      efficiency: ScoredSection;
      narrative: string;
      industry_comparison: {
        industry: string;
        benchmark: Record<string, number>;
      };
    };
    competitive_position: {
      peers: Array<{ name: string; ratios: Record<string, number | null> }>;
      ranking: Array<{ metric: string; rank: number; total: number }>;
      score: number;
      traffic_light: string;
      narrative: string;
    };
    dx_maturity: {
      score: number;
      traffic_light: string;
      indicators: Array<{ name: string; value: string; status: string }>;
      narrative: string;
    };
    risk_opportunity: {
      narrative: string;
    };
  };
  data_sources: string[];
  errors: string[];
}

export interface ScoredSection {
  score: number;
  traffic_light: string;
  metrics: Array<{
    name: string;
    value: string;
    benchmark: string;
    score: number;
  }>;
}

export interface DiagnosisStatus {
  job_id: string;
  status: string;
  progress?: {
    current_step: string;
    percent: number;
    message?: string;
  };
  report?: DiagnosisReport;
  generated_at?: string;
}
