# Test fixtures

Real FOGIS responses from one referee's match history, anonymized: every person, team, club, competition and
venue name is replaced, all ids are remapped (cross-references and event-id order preserved), free text is
blanked and dates are shifted by a few weeks. Scores, minutes and shirt numbers are unchanged.

Each folder is one scenario from docs/FOGIS_API.md and uses the layout
`matches/<year>.json`, `events/<matchid>.json`, `lineups/<matchid>_<matchlagid>.json`,
`officials/<matchid>_<matchlagid>.json` — each file is the `d` payload of the corresponding API method.

| Folder | Shows |
|---|---|
| 01_modern_linked_subs | substitutions linked 16 → 17 (2024+) |
| 02_unlinked_subs_pre2024 | unlinked "on" events that must be paired by team + minute |
| 03_auto_second_caution | server-created #2 after a second caution (id + 1, same time, not linked) |
| 04_orphan_second_caution | #2 left behind with only one caution |
| 05_penalty_pair | automatic #3 linked to 14 and to 26 |
| 06a_penalty_shootout_football | shoot-out in period 3, time "0" |
| 06b_penalty_shootout_futsal | futsal shoot-out in period 5, mm:ss times |
| 07_added_time | "90+6" stored as minute 90 + text |
| 08a_period0_old | old match with every event in period 0 |
| 08b_period0_empty_minute | event saved with an empty minute (0 / period 0) |
| 08c_period0_overflow_minute | minutes typed as 91+ landing in period 0 |
| 09a_typed_score_mismatch | typed score on a goal differs from the running score |
| 09b_futsal_save_order_score | first-saved goal typed 1-1: right in match order, wrong in save order |
| 10_official_discipline | team-official caution and sending-offs |
| 11_protected_person | crew member with protected identity |
| 12_match_list | five-match list (incl. futsal and extra time) |
