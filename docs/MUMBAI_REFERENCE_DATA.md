# Mumbai geography and accountability data

Run the packaged, network-free reference import after migrations and the normal seed:

```bash
civicquest install-mumbai-reference
```

Download the current Department of Posts resource and import its Mumbai points:

```bash
curl -L https://www.data.gov.in/sites/default/files/datafile/pincode.csv -o /tmp/pincode.csv
civicquest import-postal --file /tmp/pincode.csv --metadata data/reference/india-post-pincodes.metadata.json
```

Import the current BMC ward-office board lines and control rooms from layer 23 of the same official map:

```bash
curl -G 'https://services8.arcgis.com/r6MmJtuWAzMawmJ8/arcgis/rest/services/BMConMaps_Nov26gdb/FeatureServer/23/query' \
  --data-urlencode 'where=1=1' --data-urlencode 'outFields=*' --data-urlencode 'outSR=4326' \
  --data-urlencode 'f=geojson' -o /tmp/bmc-offices.geojson
civicquest import-bmc-offices --file /tmp/bmc-offices.geojson --metadata data/reference/bmc-offices.metadata.json
```

After the first reviewed installation, refresh the online sources transactionally:

```bash
civicquest refresh-reference
```

The command requires all expected source coverage before commit: at least 200 Mumbai City/Suburban postal rows, at least 150 usable in-boundary postal points, exactly 24 BMC ward polygons, at least 40 valid BMC office contacts and exactly six sitting Mumbai MPs. Any failed request, mismatch or incomplete snapshot rolls back the entire refresh. Replaced BMC contacts and Digital Sansad MP records receive end dates rather than being deleted.

This activates:

- 24 BMC administrative ward polygons and a Greater Mumbai coverage polygon derived from BMC's public **BMC Wards** ArcGIS layer;
- 36 Mumbai Assembly constituency polygons (AC 152–187) from the DataMeet CC BY 4.0 boundary layer;
- six Mumbai Parliamentary constituency polygons (PC 26–31) from the DataMeet CC BY 4.0 layer;
- 36 MLAs from the Maharashtra CEO/ECI elected-candidates Gazette dated 24 November 2024;
- six sitting MPs snapshotted from Digital Sansad on 13 September 2026.
- 230 in-coverage post-office points representing 89 Mumbai City/Suburban pincodes from the Department of Posts catalog snapshot.
- 24 BMC ward-office board lines and 23 valid control-room lines from the official BMC office layer. These are general contacts; category-specific operational ownership is still resolved separately.

The BMC service item publishes no license text. Its local snapshot is marked as an official reviewed source, while redistribution approval remains a launch prerequisite. Constituency polygons are contextual community geometry; representative names and terms use the dated government sources.

Pincodes are search aliases, not ownership or constituency keys. Postal delivery areas can cross ward and electoral boundaries. Resolve a searched pincode to a point, run `ST_Covers` against every active layer, and surface shared-boundary ambiguity.

Without a MapTiler key, the local interactive basemap uses the standard OpenStreetMap raster endpoint with visible attribution and requests only the current viewport. It is an online development fallback with no SLA; the service worker does not prefetch or cache map tiles for offline use. Production should use the configured MapTiler adapter or an approved hosted/self-hosted alternative.

Refresh people as dated snapshots; never overwrite history without `effective_to`. Verify deaths, resignations, by-elections and party changes against Maharashtra CEO/ECI and Digital Sansad before setting `reviewed: true`.

## Operational responsibility rules

Operational owners are separate from MLA and MP context. BMC's official material confirms ward-level functions including [Solid Waste Management](https://portal.mcgm.gov.in/irj/portal/anonymous/qlceswm?guest_user=english), [Hydraulic Engineer water service](https://www.mcgm.gov.in/irj/portal/anonymous/qlhydrlc?guest_user=english), and [Assistant Engineer (Maintenance & Repair)](https://portal.mcgm.gov.in/irj/go/km/docs/documents/Model%20RTI%20Manual/Model%20RTI%2017%20Mannual%20AE%20MAINT%20for%20ward.pdf). The official complaint process also states that routing depends on complaint type and can involve ward departments, central agencies or other agencies.

Do not turn those broad functions into blanket asset ownership. Major roads, drains, streetlights and water assets can have different responsible units. An admin must record a reviewed ward/category rule with an official source and effective dates. Overlapping reviewed periods for the same ward and category family are rejected. Until a specific rule exists, public responses say **Owner not confirmed** while still showing the general sourced ward office and control-room contacts.
