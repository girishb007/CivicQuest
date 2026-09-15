# CivicQuest Decisions & Open Questions

## 1. Decisions already made

### Product
- Brand: CivicQuest.
- Phase 1: responsive website, not native mobile.
- Mumbai is the first concept geography.
- Guest-first onboarding.
- Explore is the default entry experience.
- Places and Civic Catches are separate.
- Civic Actions are a third positive layer.
- No downvotes in Phase 1.
- Civic XP is the initial reward currency.
- NGO cleanup participation earns more XP.
- Before/after proof is a major feature.
- Infrastructure reports should show responsibility when data supports it.
- Civic Profile, CivicDex, leaderboard, quests, and share cards are core.
- No follower-count focus in V1.

### UX
- Do not show AI/model confidence percentages.
- Reporting should be short and visual.
- Visual direction is light, airy, and game-like.

### Engineering
- Web/PWA first.
- PostgreSQL/PostGIS.
- Private originals + public derivatives.
- Async heavy processing.
- Modular monolith before microservices.
- XP is ledger-based.
- Upvotes affect attention, not XP farming.

## 2. Must decide before public Civic Catches

- Are faces visible publicly?
- Which categories are allowed?
- What is sufficient evidence?
- Which reports require human review?
- How does an affected person appeal?
- What is the removal SLA?
- How long is original evidence retained?
- How are minors handled?
- How are sensitive locations handled?
- What wording avoids implying guilt before verification?

## 3. Mumbai data questions

- Which pilot wards?
- Official ward boundary source?
- Category-to-department ownership source?
- Representative data source?
- Refresh frequency?
- Ambiguous ownership rules?
- Which railway/public-transport workflows are in scope?

## 4. Product questions

- Comments in Phase 1?
- Can guests upvote?
- Can guest reports become public before account linking?
- Does reporter credibility change review speed?
- Minimum hotspot threshold?
- Duplicate radius/time window?
- Is XP awarded on submission or after verification?
- Which profile stats are public by default?

## 5. Gamification questions

- XP curve?
- Daily caps?
- CivicDex rarity rules?
- Leaderboard reset period?
- Local leaderboard geography?
- Streak mechanics?

## 6. NGO questions

- Who can create events?
- How is an NGO verified?
- GPS check-in radius?
- How is before/after proof verified?
- Can organizers directly award XP? Recommended: no; server rules award XP.

## 7. Open-source/business questions

- Public-good project, startup, or hybrid?
- License?
- Municipality SaaS later?
- Sponsored civic missions?
- Which datasets remain open?

## 8. Launch readiness checklist

Do not launch publicly until:
- policy docs exist,
- moderation is staffed,
- accountability data is tested,
- security review is complete,
- backup/restore is tested,
- report-abuse works,
- analytics is privacy-reviewed,
- terms/privacy notice exist,
- incident-response owners are named.
