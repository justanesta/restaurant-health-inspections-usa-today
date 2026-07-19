# New York State
[Food Service Establishment: Last Inspection](https://health.data.ny.gov/Health/Food-Service-Establishment-Last-Inspection/cnih-y5dw/about_data)

## Data Notes
This data includes the name and location of food service establishments and the violations that were found at the time of their last inspection. Although violation details are collected on inspection reports (i.e., the actual food item, quantity and temperature of food found out of temperature control) as well as corrective actions for critical violations, this data set is limited to the violation number and the corresponding general violation description. This dataset is for reporting purposes only. Any concerns about individual establishments should be referred to the corresponding Local Health Department.

This dataset is refreshed on a monthly basis. Some counties provide this information on their own websites and information found there may be more frequently updated. More detailed information can be obtained directly from each local health department through the Freedom of Information Law (FOIL) process. Requests for more detailed information or actual copies of inspection reports should be directed to the local health department or State District Office which conducted the inspections in question. Researchers agree to: Use the data for statistical reporting and analysis only. The author will include a disclaimer that states any analyses, interpretations or conclusions were reached by the author and not the NYSDOH. Last inspection data is the most recently submitted and available data. Historical inspection data through 2005 is also available. Active establishments can be found at: https://health.data.ny.gov/Health/Food-Service-Establishment-Inspections-Beginning-2/2hcc-shji. Inactive (closed) establishments can be found at: https://health.data.ny.gov/Health/Food-Service-Establishment-Inspections-Beginning-2/aaxz-j6pj.

## Limitations
This dataset excludes inspections conducted in New York City (https://nycopendata.socrata.com/), Suffolk County (https://eco.suffolkcountyny.gov/#/pa1/search) and Erie County (http://www.healthspace.com/erieny). Inspections are a “snapshot” in time and are not always reflective of the day-to-day operations and overall condition of an establishment. Occasionally, remediation may not appear until the following month due to the timing of the updates. The inspection data contained in this dataset was not collected in a manner intended for use as a restaurant grading system, and should not be construed or interpreted as such. Any use of this data to develop a restaurant grading system is not supported or endorsed by the New York State Department of Health.

## Additional Documentation
- https://health.data.ny.gov/api/views/cnih-y5dw/files/sqDp_3qndswu_m-1Rv-oOuoZheuYa-VsLib3LykR_mc?download=true&filename=NYSDOH_FSEInspection_Overview.pdf
- https://health.data.ny.gov/api/views/cnih-y5dw/files/C7ywYFjUuzbISPHLCOdkdJ_pEMmxlO4rBMmM2XoOiN0?download=true&filename=NYSDOH_FSEInspection_DataDictionary.pdf
- https://health.data.ny.gov/api/views/cnih-y5dw/files/CiE3kRhZhZMYsPcp-2BG-mV1Ob2ureoxAYUVFZe75Xw?download=true&filename=NYSDOH_FSEInspection_DataCollectionTool.pdf
- https://health.data.ny.gov/api/views/cnih-y5dw/files/F-Z-dYyaQzo8hT7xQEiStcrFFm3Dw50VvhhR26VGV7s?download=true&filename=NYSDOH_FSEInspection_MunicipalityCodes.pdf
- https://health.data.ny.gov/api/views/cnih-y5dw/files/c518a40d-7cda-4b94-acc8-785b05d9effb?download=true&filename=NYSDOH_FSEInspection_Benefits.pdf

## Extraction Method
Socrata SODA API. Here are the [docs](https://dev.socrata.com/docs/endpoints) as well as a specific tutorial on how to [query more than 1000 results](https://support.socrata.com/hc/en-us/articles/202949268-How-to-query-more-than-1000-rows-of-a-dataset)

# Los Angeles County
[Environmental Health Restaurant and Market Inspections 07/01/2023 to 06/30/2026](https://data.lacounty.gov/datasets/19b6607ac82c4512b10811870975dbdc/about)
[Environmental Health Restaurant and Market Violations 07/01/2023 to 06/30/2026](https://data.lacounty.gov/datasets/5eaea9f89b7549ee841da7617d3a9cba/about)

## Data Notes
### Inspections
This dataset lists restaurant and market inspections conducted by the Los Angeles County Department of Public Health, Environmental Health Division. It includes results from both routine and complaint-based inspections of food-related businesses and facilities.

This dataset contains information on inspections conducted by the Los Angeles County Department of Public Health, Environmental Health Division, for restaurants, markets, and other food facilities. These inspections are performed to ensure compliance with state and local public health regulations that protect consumers from foodborne illness and other health hazards.

The Environmental Health Division enforces public health laws throughout Los Angeles County’s unincorporated areas and 85 of its 88 incorporated cities. Data for Pasadena, Long Beach, and Vernon are not included, as each city operates its own local health department.

Each record represents a single inspection result. The Serial Number field serves as a unique identifier (primary key) that links each inspection to its corresponding violations in the Environmental Health Restaurant and Market Violations dataset.

The dataset is updated quarterly and includes data from the previous three years.

### Violations
This dataset lists health code violations observed during inspections of restaurants and markets regulated by the Los Angeles County Department of Public Health, Environmental Health Division. It includes information about each violation and can be linked to related inspection records for additional context..

This dataset contains information on health code violations identified during routine and follow-up inspections of restaurants, markets, and other retail food facilities conducted by the Los Angeles County Department of Public Health, Environmental Health Division. The division enforces public health laws throughout the County’s unincorporated areas and 85 of its 88 incorporated cities. Data for Pasadena, Long Beach, and Vernon are not included, as each city operates its own local health department.

Each record represents a single violation observed during an inspection. The Serial Number field serves as a unique identifier (primary key) that links each violation to its corresponding inspection in the Environmental Health Restaurant and Market Inspections dataset.

The dataset is updated quarterly and includes data from the previous three years. Each row represents one health code violation. All rows with the same Serial Number belong to the same inspection.

## Metadata
### Inspections
arcgis link can be found [here](https://www.arcgis.com/sharing/rest/content/items/19b6607ac82c4512b10811870975dbdc/info/metadata/metadata.xml?format=default&output=html).

## Data Dictionary
### Inspections
Field Name                               Description

ACTIVITY DATE:                       Date the inspection was conducted

OWNER ID:                              Unique identifier for the business or property owner

OWNER NAME:                        Name of the business or property owner

FACILITY ID:                             Unique identifier for the facility

FACILITY NAME:                      Name of the facility

RECORD ID:                             Unique identifier for the specific health program within the facility

PROGRAM NAME:                   Name of the health program

PROGRAM STATUS:                Current status of the program

PROGRAM ELEMENT:              Code identifying the program type

PE DESCRIPTION:                    Description of the program element

FACILITY ADDRESS:                Street address of the facility

FACILITY CITY:                         City where the facility is located

FACILITY STATE:                      State where the facility is located

FACILITY ZIP:                           ZIP code of the facility

SERVICE CODE:                      Code identifying the type of inspection performed

SERVICE DESCRIPTION:         Description of the inspection type

SCORE:                                    Total inspection score (out of 100 possible points)

GRADE :                                   Letter grade corresponding to the inspection score
### Violations
Field Name                               Description

SERIAL NUMBER*:                   Unique identifier for each inspection

VIOLATION STATUS:                Identifies the status of the violation

VIOLATION CODE:                   The code of the violation

VIOLATION DESCRIPTION:      A description of the violation code
## Extraction Method
### Inspections
cURL or other related python specific web fetching tool to ping [this url](https://www.arcgis.com/sharing/rest/content/items/19b6607ac82c4512b10811870975dbdc/data)

### Violations
cURL or other related python specific web fetching tool to ping [this url](https://www.arcgis.com/sharing/rest/content/items/5eaea9f89b7549ee841da7617d3a9cba/data)

# City of Albuquerque
[Restaurant Inspection Results](https://www.cabq.gov/environmentalhealth/food-safety/restaurant-inspection-results)

# Data Notes

Restaurant Inspection Results
Information about restaurant inspections and inspection results.

Albuquerque Restaurants & Food Inspections
View the Most Recent Inspection Report
View recent Albuquerque food inspection results
For current or historical records, please submit a public information request through the Office of the City Clerk’s by visiting ABQ Records NextRequest.
If you have questions about your business’ current or historical records, please contact the Environmental Health Department at 505-768-2716.

What is a Restaurant Inspection?
Routine inspections at food establishments are a "snapshot" of food safety operations on the particular day they are done. Critical and non-critical violations are recorded on an inspection form. Critical violations are factors that have been identified as items that could potentially cause a food borne illness. Most critical violations are typically corrected on the spot. However, some critical violations require additional time for compliance.

Are Only Restaurants Inspected?
All food service establishments receive routine inspections to ensure they are safe and sanitary.  The frequency of inspections may be increased based on past performance of the food service establishment and other laws; service of high-risk foods such as oysters, shellfish, or sushi; or service practices such a buffet or serving a high-risk population (elderly, infants).

What is the Difference Between a Green, Yellow, Red or Orange Sticker?
On the left is the green "approve" food safety inspection sticker, and the right is the red "unsatisfactory" food safety inspection sticker.

On the left is the orange "closed" sticker", and on right is the "conditional" sticker.

![Sticker image URL](https://www.cabq.gov/environmentalhealth/images/redandgreenfoodsafetystic.png/@@images/image-1200-1a1990ba65c5f10782a59a51b918fddd.png)

What Food Code does the City of Albuquerque follow?
The City of Albuquerque follows the 2022 Food and Drug Administration’s (FDA) Food Code and the Albuquerque Food Service and Retail Ordinance.

City of Albuquerque Food Report Form - English

To obtain assistance, please call 505-768-2716

## Extraction Method
cURL or other related python specific web fetching tool to ping [this url](https://www.cabq.gov/environmentalhealth/documents/chpd_main_inspection_report.pdf) and download the latest week's report PDF to be scraped.

# Issues and notes to incorporate in the deliverable
Because this was a proof-of-concept, I flattened some data edges and discordance between sources (i.e. any critical violations in New York state results signals a "failure") and kept the resulting set purposely very thin. In actual practice, what I would do is try and get the full universe of data sources _first_ (what are all of the newsrooms that might consume this data and what geographies/regulators administer them and would publish inspection data) and then try to design a data model around those. What that would probably end up resulting in is both a derived "pass/fail" field as well as some sort of index calculated from any of the scoring measures used by the various regulating agencies in an attempt to communicate relative risk.




