## 1. Implementation and verification

- [ ] 1.1 Implement sourced boundary import and ambiguous ownership; PostGIS edge tests pass
- [ ] 1.2 Implement map, viewport, search and list fallback; browser exploration tests pass

## 2. Nammakasa-inspired area journeys

- [x] 2.1 Add a public area projection with public-only statistics, provenance and separate constituency/representative context; PostGIS projection test passes
- [ ] 2.2 Add ward shading, numbered clusters, category/status filters, grouped list and ward detail routes; browser accessibility and count-consistency checks pass

## 3. Electoral geometry and reference UX

- [x] 3.1 Count public reports by actual area geometry; test crossing constituencies and shared boundaries on PostGIS
- [x] 3.2 Exclude inactive/expired/future boundaries from lookup, map, search and details; require reviewed/current representative terms
- [x] 3.3 Validate complete imports and immutable version provenance before inserting records
- [x] 3.4 Verify ward→constituency routes, truthful counts, map/filter restoration and area accessibility in desktop/mobile Chrome
- [ ] 3.5 Complete reference UX-01/02/07/08 from docs/REMAINING_WORK.md; retain approved data prerequisites
