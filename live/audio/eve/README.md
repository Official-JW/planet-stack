# Eve voice clips (dev build)

Clips are `<id>_<n>.mp3` (n = line index from 0). Only clips listed in `manifest.json` are fetched; anything unlisted stays silent.
Source: `AUDIO/eve_clips/` (voice A). All 9 approved and md5-checked 10/31/2026 (EM 07:58).

- cargo_delivered_0, away_summary_0: number-free voice lines; the on-screen text keeps the real amounts.
- name_greeting_0: fixed "Welcome aboard, Commander"; the typed name shows only in Eve's banner and call text.
- first_deposit_0: never plays in this build (CFG.econ.deposits = false, so first_deposit never rings).
- mine_first_view_1 is the deposits-OFF line. mine_first_view_dep_1 and _parked/ are left out on purpose.
