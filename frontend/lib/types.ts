export interface Token {
  address: string;
  symbol: string;
  name: string;
  decimals: number;

  pair_address: string | null;
  factory: string | null;
  dex: string | null;

  creation_block: number | null;
  creation_timestamp: string;

  bonding_platform: string | null;
  bonding_progress: number;
  is_bonding: boolean;
  migrated_at: string | null;
  // $0/month path only (scan_runner.py) — used to prune bonding tokens
  // with no forward progress in DEAD_BONDING_HOURS; not written by the
  // legacy always-on path, so treat as optional.
  progress_high_water_mark?: number;
  progress_stale_since?: string | null;

  liquidity_usd: number;
  liquidity_locked: boolean;
  market_cap_usd: number;
  price_usd: number;
  volume_24h_usd: number;
  holder_count: number;
  top10_holder_pct: number;

  owner_renounced: boolean;
  mint_disabled: boolean;
  contract_verified: boolean;

  honeypot_risk: boolean | null;
  buy_tax_pct: number;
  sell_tax_pct: number;

  ave_security_score: number | null;
  security_score: number;
  runner_score: number;
  is_runner: boolean;

  last_checked_at: string;
  created_at: string;
}

export interface TokenListResponse {
  items: Token[];
  total: number;
  limit: number;
  offset: number;
}

export interface Bookmark {
  id: string;
  user_id: string;
  token_address: string;
  note: string | null;
  created_at: string;
  token: Token | null;
}

export interface Stats {
  total_tokens: number;
  bonding_tokens: number;
  migrated_tokens: number;
  runners_24h: number;
  avg_security_score: number;
  last_token_at: string | null;
}

export interface WsEvent {
  type: "new_token" | "token_updated" | "runner_flagged" | "bonding_complete";
  data: Token;
}

export interface TokenFilters {
  bonding?: boolean;
  platform?: string;
  min_security_score?: number;
  min_holder_count?: number;
  runners_only?: boolean;
  search?: string;
  sort_by?: string;
  order?: "asc" | "desc";
  limit?: number;
  offset?: number;
}
