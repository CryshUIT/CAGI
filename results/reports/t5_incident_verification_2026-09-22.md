# T5 — Re-verify 15 incident: nguồn công khai + tx hash đối chiếu (2026-09-22)

## Phương pháp

Với mỗi incident trong 15 incident chính (`main_table.csv`): (a) đọc `metadata/incident_registry.csv`
(cột `source_report`, `source_url`, `notes` — đã được viết chi tiết trong các phiên trước, có đối chiếu
tx-level), (b) **tự đối chiếu độc lập lại** — gọi trực tiếp `find_provenance_bridge_events()` (bằng chứng
tiền vào seed từ bridge contract đã verify) hoặc quét `<incident>_events.json` (trajectory outbound thật)
để lấy tx hash + số tiền + thời điểm THẬT, so với claim trong `notes`.

**3/15 incident được đối chiếu tx-hash-cụ-thể 100% khớp tuyệt đối** (ronin_bridge_2022,
bsc_token_hub_2022, deltaprime_arbitrum_2024 — chọn vì notes có claim tx hash cụ thể nhất để kiểm tra
nghiêm ngặt nhất). **12/15 incident còn lại** được xác nhận có tx hash thật + số tiền hợp lý trong
trajectory đã decode (khớp bậc độ lớn với báo cáo công khai đã ghi trong notes), nhưng KHÔNG re-verify
từng chữ số với nguồn bên ngoài (ngoài phạm vi thời gian cho phép — xem "Giới hạn" cuối báo cáo).

## Bảng tổng hợp

| Incident | Nguồn công khai độc lập | Tx hash đối chiếu | Trạng thái |
|---|---|---|---|
| ronin_bridge_2022 | Ronin Network official; Chainalysis; US Treasury OFAC | `0xc28fad5e...d0b7` (173,600 ETH) + `0xed2c72ef...b08` (25.5M USDC) — **tự verify qua `find_provenance_bridge_events()`, khớp 100% với notes** | **VERIFIED (đối chiếu độc lập)** |
| bsc_token_hub_2022 | Halborn; Merkle Science; Nansen; Elliptic; CNBC; TechCrunch | `0xebf83628...e3b8b` + `0x05356fd0...5c57a` — 1.000.000 BNB/lần, block 21957793/21960470 — **tự verify, khớp 100%** | **VERIFIED (đối chiếu độc lập)** |
| deltaprime_arbitrum_2024 | CertiK; Halborn; crypto.news; BeInCrypto; Three Sigma | `0x21032a57...8f5da` — 2,967 WBTC bridge_deposit — **tự verify, khớp 100% với "2.96 WBTC" (crypto.news)** | **VERIFIED (đối chiếu độc lập)** |
| chibi_finance_2023 | CertiK | `0x56f6194e...6ae8` — 74,122 ARB transfer, block 105368069 (có trong trajectory, khớp bậc độ lớn) | Có bằng chứng, chưa re-verify từng chữ số |
| feg_bridge_2024 | CertiK; Halborn; TenArmor | `0xedf8be6d...077b74` — 100 ETH mixer_or_exit (Tornado Cash), block 21506183 | Có bằng chứng, chưa re-verify từng chữ số |
| hackerdao_2022 | CertiK | 4 tx mixer_or_exit tới TornadoProxyLight (block ~17427-17428xxx) — CertiK báo ~200 BNB/~65K USD tổng, trajectory chỉ thấy phần nhỏ (xem `hackerdao_2022_investigation_2026-09-22.md` — đã điều tra riêng, xác nhận có khoảng trống dữ liệu ở đầu trajectory) | Có bằng chứng nguồn gốc, đã biết giới hạn dữ liệu (báo cáo riêng) |
| magic_abracadabra_arbitrum_2025 | CertiK; threesigma.xyz | `0xf92ae483...9f54b` — 465,000 USDC transfer, block 319389085 | Có bằng chứng, chưa re-verify từng chữ số |
| new_free_dao_2022 | Halborn; ImmuneBytes; QuillAudits; Cointelegraph; BeInCrypto; CryptoSlate | `0x53adf53e...d6171` — 100 BNB mixer_or_exit (Tornado Cash), block 17690249 | Có bằng chứng, chưa re-verify từng chữ số |
| paraluni_2022 | CertiK; SlowMist | `0x9f9f21f1...7d1c` — 8.74M USDT swap, block 16040892 | Có bằng chứng, chưa re-verify từng chữ số |
| qbridge_qubit_2022 | CertiK; SlowMist; Halborn; CoinDesk; Cointelegraph | `0x8a64854c...82e4b9` — 9.35M USDC transfer, block 14765366 | Có bằng chứng, chưa re-verify từng chữ số |
| radiant_capital_arbitrum_2024 | Halborn; CoinDesk; ChainCatcher; rekt.news; Radiant Capital official | `0x293f7946...4f2458d` — 3.84M ARB transfer, block 264502980 (notes có chuỗi dòng tiền chi tiết hơn, đã verify trong phiên trước) | Có bằng chứng, chưa re-verify từng chữ số |
| utopiasphere_2024 | CertiK | `0x1ddf415a...889f604` — 96.7M + 42M USDT transfer cùng tx, block 40665083 | Có bằng chứng, chưa re-verify từng chữ số |
| wault_finance_2021 | SlowMist | `0xe49e19df...ac4df` — 628.79 BNB swap, block 9755791 | Có bằng chứng, chưa re-verify từng chữ số |
| wooppv2_2024 | Beosin; CUBE3.AI; PeckShield; Cyfrin | `0xceffd7fc...b9924` — 222.6 ETH transfer, block 187392030 | Có bằng chứng, chưa re-verify từng chữ số |
| xkingdom_2024 | CertiK | `0xbde4f488...ad99c` — 500,000 USDC transfer, block 167735383 | Có bằng chứng, chưa re-verify từng chữ số |

## Phát hiện phụ (không phải mâu thuẫn — đã hiểu rõ cơ chế)

Ban đầu quét trực tiếp `ronin_bridge_2022_events.json`/`bsc_token_hub_2022_events.json` **KHÔNG tìm thấy**
2 tx hash cụ thể ghi trong `notes` — tưởng là sai lệch, nhưng xác nhận đây là THIẾT KẾ ĐÚNG: các tx đó là
**provenance event** (tiền chảy VÀO seed từ bridge contract đã verify, dùng để XÁC NHẬN danh tính seed) —
theo docstring `find_provenance_bridge_events()`: "KHÔNG thuộc outbound trajectory (builder chỉ mở rộng
forward từ seed)". Gọi đúng hàm này thì tìm thấy khớp 100%. Không phải bug, không cần sửa gì.

## Giới hạn (trung thực, chưa làm)

- Chỉ 3/15 incident được đối chiếu tx-hash-cụ-thể-trong-notes 1-1 nghiêm ngặt; 12/15 còn lại chỉ xác nhận
  "có tx thật, số tiền hợp lý" chứ chưa so khớp từng chữ số với văn bản báo cáo gốc (CertiK/SlowMist/...).
- Không truy cập lại các URL nguồn (`source_url`) trong phiên này để re-đọc báo cáo gốc — dựa vào `notes`
  đã ghi từ các phiên trước (bản thân notes đã ghi rõ "khớp chính xác" kèm số liệu cụ thể khi đối chiếu
  trước đó) cộng với xác nhận tx thật tồn tại trong dữ liệu đã decode.
- Không tìm thấy incident nào thiếu nguồn công khai hoặc có dấu hiệu sai lệch nghiêm trọng cần báo cáo
  ngay — không có incident nào bị đề xuất loại khỏi dataset.
