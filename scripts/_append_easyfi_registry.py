"""Them easyfi_2021 vao metadata/incident_registry_N30.csv. Chi chay 1 lan."""
import pandas as pd

r = pd.read_csv("metadata/incident_registry_N30.csv")

new_row = {
 "incident_id": "easyfi_2021",
 "name": "EasyFi exploit (19/04/2021, compromised admin/mnemonic keys)",
 "label": 1, "chain_primary": "eth", "chains_involved": "eth",
 "seed_address": "0x83a2eb63b6cc296529468afa85dbde4a469d8b37",
 "start_block": 12269350, "is_cross_chain": False,
 "bridge_families": "",
 "dex_families": "Uniswap V2 (269 swap action truc tiep toi Router, da allowlist)",
 "mixer_families": "Khong xac dinh (bao cao neu 'dark pool' qua WBTC/renBTC, khong co ten/dia chi cu the, KHONG verify duoc)",
 "source_report": "Medium (EasyFi official); AMBCrypto; Yahoo Finance/BeInCrypto; gbaglobal.org; AVOID.NET",
 "source_url": "https://medium.com/easify-network/easyfi-security-incident-66c02a277a91",
 "confidence": "high", "endpoint_type": "verified_dex_swap_no_mixer_label", "endpoint_confirmed": False,
 "annotator_1": "AI-assisted (Claude Code) pipeline, dataset expansion N30 lo 2, 2026-10-15",
 "annotator_2": "",
 "notes": ("Seed xac nhan doc lap boi nhieu nguon (dia chi nhan 2.98 trieu EASY token danh cap). "
           "Bao cao goc noi 'hacker dung WBTC/renBTC qua dark pool, remained untraced' - KHONG co ten/"
           "dia chi bridge/DEX/mixer cu the de verify truc tiep tu bao cao. Kiem tra on-chain THAT lai "
           "phat hien seed GOI TRUC TIEP Uniswap V2 Router (0x7a250d563..., da allowlist) nhieu lan "
           "trong cung ngay hack (2021-04-19) - dat cong (3) qua DEX THAT (khong phai tu bao cao, tu "
           "on-chain). Build thuc te BUNG NO cuc lon: n_actions=17166, n_processed=2369 (LON HON Inverse "
           "Finance 11592) - 269/2166 swap action cham truc tiep Uniswap V2 Router, KHONG co mixer_or_exit "
           "nao. endpoint_confirmed=False (chi co swap, khong co mixer/exit-service xac nhan theo dinh "
           "nghia literal). Xem known_builder_limitations.md ve muc bung no nghiem trong hon Inverse - "
           "de xuat them sensitivity 'N tru EasyFi' tuong tu da lam cho Inverse."),
 "eval_tier": "primary",
}

for col in r.columns:
    if col not in new_row:
        new_row[col] = ""
new_df = pd.DataFrame([new_row])[r.columns.tolist()]
out = pd.concat([r, new_df], ignore_index=True)
out.to_csv("metadata/incident_registry_N30.csv", index=False)
print("Da them easyfi_2021. Tong hien tai:", len(out))
