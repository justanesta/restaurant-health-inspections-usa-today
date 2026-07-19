```yaml
# data_mapping_schema.yaml
fields:
  - target_name: restaurant_name
    target_type: string
    description: "Cannonical name of the restaurant"
    sources:
      - source_author: new_york_state
        source_field: facility
        source_type: string
      - source_author: los_angeles_county
        source_field: "FACILITY NAME"
        source_type: string
      - source_author: albuquerque_city
        source_field: 
        source_type: string

  - target_name: restaurant_address
    target_type: string
    description: "Street address of the restaurant"
    sources:
      - source_author: new_york_state
        source_field:
            - address
            - city
            - zip_code 
        source_type: string
      - source_author: los_angeles_county
        source_field: 
            - "FACILITY ADDRESS"
            - "FACILITY CITY"
            - "FACILITY STATE"
            - "FACILITY ZIP"
        source_type: string
      - source_author: albuquerque_city
        source_field: 
        source_type: string

  - target_name: inspection_date
    target_type: string
    description: "Datetime of restaurant inspection"
    sources:
      - source_author: new_york_state
        source_field: date
        source_type: timestamp
      - source_author: los_angeles_county
        source_field: "Activity Date"
        source_type: date
      - source_author: albuquerque_city
        source_field: "Inspection Date"
        source_type: string

  - target_name: inspection_result
    target_type: enum
    target_values:
        - pass
        - fail
    description: "Result of restaurant inspection. Either explicit or inferred from the data."
    sources:
      - source_author: new_york_state
        source_field: total_critical_violations
        source_type: numeric
        notes: "We will assume any critical violations resulted in a failure"
      - source_author: los_angeles_county
        source_field: SCORE
        source_type: numeric
        notes: "We will assume any score below 70 is a failure"
      - source_author: albuquerque_city
        source_field: "Inspection Status"
        source_type: string
        notes: "We will designate any non-CLOSED score as a 'pass' and only CLOSED scores as a 'fail'."

  - target_name: inspection_id
    target_type: string
    description: "Unique identifier of restaurant inspection in source data"
    sources:
      - source_author: new_york_state
        source_field: nys_health_operation_id
        source_type: string
      - source_author: los_angeles_county
        source_field: "SERIAL NUMBER"
        source_type: string
      - source_author: albuquerque_city
        source_field: "Inspection ID Number"
        source_type: string

  - target_name: inspection_violations
    target_type: string
    description: "Description of restaurant inspection violations"
    sources:
      - source_author: new_york_state
        source_field: violations
        source_type: string
      - source_author: los_angeles_county
        source_field: "VIOLATION DESCRIPTION"
        source_type: string
      - source_author: albuquerque_city
        source_field: "Violation: "
        source_type: string
```