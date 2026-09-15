# Phase 1 Product Scope

## 1. Goal

Ship a **responsive web application** for Mumbai that validates whether people will repeatedly use a gamified civic platform without requiring a native app download.

The website should work especially well on mobile browsers and can later be made installable as a **Progressive Web App (PWA)**.

## 2. Primary Phase 1 user journeys

### Journey A — Explore
1. Open CivicQuest in a browser.
2. Allow location or manually choose an area.
3. See nearby Places issues, Civic Catches, Civic Actions, and hotspots.
4. Inspect a report or hotspot.

### Journey B — Report a Place issue
1. Tap Capture / Report.
2. Take or upload a photo.
3. Attach current location.
4. App suggests a category.
5. User reviews the category.
6. User sees likely ward / responsible body.
7. Submit.
8. Receive Civic XP.
9. Report appears in the Places feed after required checks.

### Journey C — Report a Civic Catch
1. Capture/upload evidence.
2. Choose / confirm civic-behavior category.
3. Submit for review.
4. Public visibility follows CivicQuest moderation policy.
5. Reporter receives XP only when the report meets validity rules.

### Journey D — Upvote / boost attention
1. Browse Places or Civic Catches.
2. Upvote an issue that deserves attention.
3. Trending / hotspot score increases.
4. Upvotes do not provide meaningful XP.

### Journey E — Civic Action
1. Discover an NGO/community cleanup.
2. Join.
3. Check in at the location.
4. Upload before / after proof.
5. Verification completes.
6. Earn higher Civic XP.

### Journey F — Identity and sharing
1. User starts as a guest.
2. After earning value, CivicQuest asks the user to save progress.
3. User links an account.
4. Profile stores XP, level, CivicDex, actions, and rank.
5. User generates a shareable impact card.

## 3. Phase 1 must-have capabilities

### Website
- Responsive design
- Mobile-browser optimized camera/upload
- PWA-ready manifest/service worker
- SEO pages for public hotspots and public reports where policy allows
- Accessible keyboard/touch interactions

### Identity
- Anonymous guest session
- Optional account conversion
- Google login first; additional providers later
- Signed, secure session cookie
- Server-side identity and rate-limit state

### Explore
- Mumbai map
- Current location
- Manual place search
- Places / Civic Catches / Civic Actions filters
- Nearby reports
- Hotspot pins

### Reporting
- Image upload / camera capture
- EXIF stripping on public derivatives
- GPS/location selection
- Category suggestion
- Duplicate check
- Ward / authority lookup
- Submit
- Report status

### Community
- Separate Places and Civic Catches feeds
- Upvotes only
- Trending score
- Public report detail
- Basic report history/timeline

### Accountability
- Administrative-area lookup
- BMC / ward mapping
- Responsible-department mapping for supported categories
- Representative metadata when available
- Hotspot summary

### Gamification
- Civic XP
- XP events ledger
- Levels
- CivicDex
- Basic quests
- Mumbai/local leaderboard

### Civic Actions
- Event listing
- Event join
- Check-in
- Before/after upload
- Verification
- XP award

### Moderation
- Content state machine
- Report abuse
- Moderator queue
- Original/private media
- Public derivative media
- Appeals placeholder

## 4. Phase 1 non-goals

Do not block launch on:

- Native iOS/Android apps
- Full AR camera experience
- Pan-India launch
- Cash rewards or brand coupons
- Direct government system integration
- Automatic fines
- Automated identification of a person
- Public face recognition
- Full social graph / followers
- DMs
- Complex comment threads
- Every Mumbai civic category
- City-wide legal enforcement workflows
- Real-time live video
- Full enterprise analytics portal

## 5. Pilot recommendation

Start with a controlled Mumbai area and a small category set.

### Places
- Garbage / illegal dumping
- Overflowing bins
- Potholes
- Water leakage
- Open drains

### Civic Catches
- Littering
- Spitting
- Public urination
- Prohibited smoking

### Civic Actions
- Cleanup drives
- Beach cleanups
- Neighborhood cleanup events

## 6. Success gates before Phase 2

Move to a broader rollout only if:

- First-report completion is strong.
- D7 retention shows repeat use.
- Duplicate/fake report rates are manageable.
- Hotspot clustering produces useful results.
- Accountability mapping is accurate enough to be trusted.
- NGO action participation is measurable.
- Moderation workload is operationally sustainable.
