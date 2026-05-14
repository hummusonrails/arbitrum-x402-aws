export interface NetworkConfig {
  chainId: number;
  caip2: string;
  usdc: string;
  arbiscanTxBase: string;
  cdpFacilitatorUrl: string;
}

// Arbitrum One Mainnet Native USDC
export const NETWORK: NetworkConfig = {
  chainId: 42161,
  caip2: "eip155:42161",
  usdc: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
  arbiscanTxBase: "https://arbiscan.io/tx/",
  cdpFacilitatorUrl: "https://api.cdp.coinbase.com/platform/v2/x402",
};
