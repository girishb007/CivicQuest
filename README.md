# CivicQuest

> Level up your city.

CivicQuest is an open-source, mobile-first civic participation platform for Mumbai, India. It turns civic discovery, reporting, verification, and community action into a measurable experience with Civic XP, profiles, quests, and impact sharing.

The project is currently in the product vision and design-validation stage. This repository is the public home for the product direction, design references, decisions, and future implementation work.

## Product vision

CivicQuest is inspired by location-based exploration games, but its goal is real-world civic improvement:

```text
Discover -> Report or act -> Build attention -> Identify responsibility -> Verify change -> Earn Civic XP
```

The concept has three participation areas:

- **Places**: infrastructure and public-space issues such as garbage, potholes, water leaks, and broken streetlights.
- **Civic Catches**: reports about civic-behavior violations, handled with verification, moderation, privacy, and due-process safeguards.
- **Civic Actions**: positive offline activities such as cleanups, restoration drives, and NGO-led community work.

The guiding principle is: **reporting matters, fixing matters more**.

## Current status

This is a design-first product repository. There is no production application or local development stack yet.

- Product vision: [CivicQuest Project Vision](CivicQuest_Project_Vision.md)
- Product vision hub: [CivicQuest Product Vision Hub](https://girishbisane8668.atlassian.net/wiki/spaces/~635304b6fc0cc7a600add921/pages/393217/CivicQuest+Product+Vision+Hub)
- Product vision slides: [CivicQuest Product Vision PDF](CivicQuest_Product_Vision.pdf)
- Figma concept: [CivicQuest - Mumbai Product Vision](https://www.figma.com/design/43BWAaDcCrxYLYROLAdOvM/CivicQuest-%E2%80%94-Mumbai-Product-Vision?node-id=1-2&p=f&t=WLBnPNu84pLUJdcw-0)
- Target pilot geography: Mumbai, India
- Intended platform: mobile-first
- Planned reward model: Civic XP, not cash or coupons in the initial concept

## Repository map

| Path | Purpose |
| --- | --- |
| `CivicQuest_Project_Vision.md` | Product brief, user journeys, feature ideas, data model, and open decisions |
| `CONTRIBUTING.md` | How to propose changes and contribute |
| `SECURITY.md` | How to report security, privacy, or abuse concerns |
| `.github/` | Issue forms and pull request guidance |

As the project evolves, implementation documentation can be added under `docs/` and code under an agreed application structure.

## Contributing

Contributions are welcome, including product critique, UX research, civic taxonomy, safety review, documentation, design, engineering, and local-government context.

Before proposing implementation work, please read the vision and review the open product and safety decisions in it. Start with [CONTRIBUTING.md](CONTRIBUTING.md), and use an issue to discuss substantial changes before opening a pull request.

## Safety and responsible design

CivicQuest must never turn an unverified allegation into public punishment. Identity exposure, face visibility, evidence retention, moderation, appeals, reporting, and authority escalation require explicit product, legal, and safety decisions before launch.

The project should prioritize reporting civic issues and positive civic action, protect bystanders and vulnerable people, minimize personal data, and provide fair review for disputed reports. See [SECURITY.md](SECURITY.md) for the scope of security and privacy concerns.

## License

CivicQuest is released under the [MIT License](LICENSE). Contributions are accepted under the same license.
