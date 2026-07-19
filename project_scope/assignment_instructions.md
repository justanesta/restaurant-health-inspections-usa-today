Design and demonstrate an approach to collect the same type of information from multiple sources that are each structured completely differently — and turn that into a single, repeatable scraping automation.

Use restaurant health inspections (or, alternatively, property transfers/deeds) as your subject. The core challenge is this: the same data lives across hundreds of city, county, and state sources, but no two are built alike. One might expose a clean REST API, another a searchable database, another a downloadable flat file, and many are outdated sites requiring multiple clicks, dropdowns, or PDF parsing.

We want to see how you actually work through that variety — how you'd pull one consistent set of fields out of sources that share nothing in common structurally, and unify them into one automation rather than a pile of one-off scripts.

You don't need to build the whole system. Choose at least three real data sources that are meaningfully different from each other, and walk us through your thinking and a working proof-of-concept.

What to Deliver
- A short walkthrough of the 3+ sources you chose and why they represent different structural challenges
- Your approach to normalizing those different structures into one consistent schema
- Your architecture for scaling this pattern across many more sources
- Your strategy for handling breakage when a source changes or goes down
- A short section on delivery: how you'd surface newsworthy signals to reporters (alerts, tip sheets, routing by beat/market)