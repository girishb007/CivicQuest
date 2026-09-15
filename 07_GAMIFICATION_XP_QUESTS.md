# CivicQuest Gamification, XP, CivicDex & Quests

## 1. Purpose

Gamification exists to make civic contribution repeatable.

It must not incentivize spam, humiliation, dangerous confrontation, staged problems, or compulsive reporting.

## 2. XP ledger

All XP is awarded through immutable `xp_events`.

Required fields:
- event type,
- source object,
- points,
- idempotency key,
- anti-abuse metadata.

## 3. Initial XP proposal

| Activity | XP |
|---|---:|
| Valid Civic Catch | 5–10 |
| Valid Place report | 5–15 |
| Verify existing report | 2 |
| Report passes verification | +5 |
| Major attention threshold | +5 |
| Issue resolved | +15 |
| Verify resolution | +10 |
| Civic Action check-in | +20 |
| Civic Action completed | +50 |
| Verified before/after impact | +50 bonus |

## 4. Upvotes

Upvotes primarily affect:
- attention,
- trending,
- hotspot score.

Do not make them a meaningful XP source.

## 5. Levels

```text
1   Observer
5   Civic Scout
10  Street Guardian
20  City Champion
30  Civic Hero
50  Mumbai Legend
```

Use a progressive XP curve.

## 6. CivicDex

Users collect **issue categories**, not people.

### Common
- Littering
- Spitting
- Improper waste disposal
- Illegal parking

### Uncommon
- Public urination
- Reserved-seat misuse
- Prohibited smoking

### Rare
- Hazardous dumping
- Public-property damage

Rarity is presentation only; severe incidents must never be made desirable to hunt.

## 7. Quests

### Daily
- verify 3 nearby reports,
- inspect hotspot updates.

### Nearby
- discover a new category,
- verify a resolved issue.

### Community
- join a cleanup,
- submit before/after proof.

## 8. Data-driven quest definition

```json
{
  "code": "daily_verify_3",
  "type": "daily",
  "target_event": "report.verification",
  "target_value": 3,
  "reward_xp": 15,
  "rules": {"max_per_day": 1}
}
```

## 9. Leaderboards

Phase 1:
- local,
- Mumbai,
- India placeholder if data supports it.

Rank by verified XP, not raw upload count.

## 10. Anti-gaming

- daily XP caps,
- duplicate-report reduction,
- same-location spam suppression,
- self-upvote prevention,
- collusion detection,
- action check-in geofence,
- proof verification,
- idempotency keys.

## 11. XP reversal

Use compensating ledger events.

```text
+10 report_valid
-10 report_invalidated
```
