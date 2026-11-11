// Sao chep TINH (khong doi gia tri) tu src/features/aadapt_mapping.py::AADAPT_TECHNIQUES
// - chi dung de hien thi ten/mo ta ky thuat AADAPT, nguon du lieu that
// (feature -> AADAPT ID) van den tu backend (data/dashboard/incidents.json).
export const AADAPT_TECHNIQUES: Record<string, { name: string; observable: string }> = {
  ADT3005: { name: "Cross-Chain Swaps (Hopping)", observable: "bridge→swap, nested bridge hops, chain change" },
  ADT3028: { name: "Siphon Funds", observable: "split, fan-out, many counterparties" },
  "ADT3028.001": { name: "Anonymous Wallets", observable: "chains of fresh intermediary addresses" },
  "ADT3028.003": { name: "Layering", observable: "swap→split, rapid token pivot, repeated transfer/swap" },
  "ADT3028.005": { name: "Peel Chains", observable: "peel-like chain, repeated split" },
  ADT3030: { name: "Use Anonymizing Services", observable: "mixer-or-exit interaction, abrupt flow end" },
  "ADT3030.003": { name: "Tumblers", observable: "mixer deposit, merge/split around mixer" },
};
