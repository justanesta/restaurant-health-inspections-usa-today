This project is a proof-of-concept, not a full system build. I just need to flesh out enough at a simple level of tooling to show how the product works as currently constructed and how it _would_ work with more fleshed out infrastructure and tooling. The schema decision-making, trade-offs, and future project questions will be the most illuminating part of this rather than the code or even data.

# My Initial Thoughts

## Data Pipeline Flow and Formats
Let's have this be as simple of a skeleton as possible. Python extractors for data from the three sources. A folder for the raw extracted source data, a folder for the transformed & normalized staging data, then a folder with the combined final "production" data. GitHub actions that are both scheduled but can also be triggered by workflow dispatch run the initial extractors. Later pipeline steps are only triggered by successful previous ones. Data validation both at raw extract to ensure no upstream changes as well as at pre-final integration to ensure no downstream pollution. It's very important that data schema/integrity errors are handled, loud and easily findable in the repo. Can be a plain-text file in a different folder for a proof-of-concept. Final schema should be YAML derived. Let's have everything after intial landing data flow to JSON and conform to JSON schema.  

## Metadata
Each source should inject its own US Census FIPS/GEOID code as well as basic demographic statistics like population that can be obtained from the census. Each inspection and establishment (establishments can be inspected more than once and change names) should have its own UUID we define. There should also be a plain-text state file that tracks pipeline state for each source.

## Future Improvements and Questions to Ask
- This would work so much better with a database that is downstream from the raw object storage layer and is medallionized with data integrity enforced with dbt. What are the infrastructure options available at USA TODAY to support such a product?
- Would a product like this be backwards-looking to try and capture inspection edits
- For this product, observability seems like a major concern. In an ideal world data integrity would be observed with something like Monte Carlo/Soda core and errors would be observed with something like Sentry. Does the USA TODAY have support/experience with platforms like that currently?
- As something like this scales, orchestration through tools such as Apache Airflow and Prefect could be come desireable or necessary. Does USA TODAY have support/experience with platforms like that currently? 
- In terms of presentation, the raw GitHub content URL of the finalized JSON in this repo could be plugged into a slack hook, email blast, etc. Or even be revamped into an RSS feed. A more fleshed out front-end could have a full API, or even a website that reporters could use to query and search the data as desired. Does the USA TODAY have the appetite/demand and tooling, infrastructure, or personel to develop and deliver such a product?

# Initial Delivery
- Appropriately named folders for each data stage
- Finalized and employable data schema
- The lightest possible weight python package for extracting, transforming, and loading from the three sources
- Sensible collection of unit, integration, and e2e testing suite.
- Project documentation model crafted on a pared down version of [this project](https://raw.githubusercontent.com/justanesta/consumer-product-recalls/refs/heads/main/documentation/documentation_model.md)
- Skeleton of an answer sheet addressing the "What to Deliver" section in the [assignment instructions](assignment_instructions.md)




